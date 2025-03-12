from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_aws import ChatBedrock
from langchain_community.tools.tavily_search import TavilySearchResults

from langgraph.checkpoint.mongodb import MongoDBSaver

import logging

import os
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

"""
In previous examples we've annotated the `messages` state key
with the default `operator.add` or `+` reducer, which always
appends new messages to the end of the existing messages array.

Now, to support replacing existing messages, we annotate the
`messages` key with a customer reducer function, which replaces
messages with the same `id`, and appends them otherwise.
"""
from uuid import uuid4

def reduce_messages(left: list[AnyMessage], right: list[AnyMessage]) -> list[AnyMessage]:
    # assign ids to messages that don't have them
    for message in right:
        if not message.id:
            message.id = str(uuid4())
    # merge the new messages with the existing messages
    merged = left.copy()
    for message in right:
        for i, existing in enumerate(merged):
            # replace any existing messages with the same id
            if existing.id == message.id:
                merged[i] = message
                break
        else:
            # append any new messages to the end
            merged.append(message)
    return merged

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], reduce_messages]

class Agent:

    def __init__(self, model, tools, checkpointer, system=""):
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_bedrock)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges(
            "llm",
            self.exists_action,
            {True: "action", False: END}
        )
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
        # Human in the loop:
        # interrupt_before=["action"] will interrupt the graph before the action node
        # it's going to add an interrupt node before the action node
        # So the action node is where we call the tools.
        # the reason why we want to interrupt before the action node is because we want to give the user the opportunity to review the results before we take any action.
        self.graph = graph.compile(
            checkpointer=checkpointer,
            interrupt_before=["action"]
            )
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

    def exists_action(self, state: AgentState):
        result = state['messages'][-1]
        return len(result.tool_calls) > 0

    def call_bedrock(self, state: AgentState):
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        return {'messages': [message]}
    
    def take_action(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            print(f"Calling: {t}")
            if not t['name'] in self.tools:      # check for bad tool name from LLM
                print("\n ....bad tool name....")
                result = "bad tool name, retry"  # instruct LLM to retry if bad
            else:
                result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print("Back to the model!")
        return {'messages': results}
    

    
    
def main():

    if not os.environ.get("TAVILY_API_KEY"):
        os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

    tool = TavilySearchResults(max_results=4) # increased number of results
    print(type(tool))
    print(tool.name)

    prompt = """You are a smart research assistant. Use the search engine to look up information. \
    You are allowed to make multiple calls (either together or in sequence). \
    Only look up information when you are sure of what you want. \
    If you need to look up some information before asking a follow up question, you are allowed to do that!
    """

    model_id = "anthropic.claude-3-haiku-20240307-v1:0" # You can change this to any Claude Anthropic model.
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION")

    model = ChatBedrock(model=model_id,
                region=aws_region, 
                aws_access_key_id=aws_access_key, 
                aws_secret_access_key=aws_secret_key)
    
    thread = {"configurable": {"thread_id": "5"}}
    messages = [HumanMessage(content="How is current politics in Argentina?")]
    
    with MongoDBSaver.from_conn_string(MONGODB_URI, DATABASE_NAME) as checkpointer:
        abot = Agent(model, [tool], system=prompt, checkpointer=checkpointer)

        for event in abot.graph.stream({"messages": messages}, thread):
            for v in event.values():
                print(v)


if __name__ == '__main__':
    main()