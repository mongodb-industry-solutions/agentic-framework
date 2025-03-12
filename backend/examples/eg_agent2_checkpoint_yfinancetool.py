from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_aws import ChatBedrock
from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool

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

class AgentState(TypedDict):
    # The list of messages exchanged between the agent and the user.
    messages: Annotated[list[AnyMessage], operator.add]

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
        self.graph = graph.compile(checkpointer=checkpointer)
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

    tool = YahooFinanceNewsTool()
    print(type(tool))
    print(tool.name)

    prompt = """You are a financial analyst tasked with analyzing the sentiment of news articles related to a specific stock ticker. Your objectives are: \
            1. **Sentiment Analysis:** Determine the overall sentiment (positive, negative, or neutral) of the latest news articles about the stock ticker provided. \
            2. **Summary:** Provide a brief summary of the key points from the news articles that influenced the sentiment. \
            3. **Recommendations:** Based on the sentiment analysis, suggest potential investment actions (e.g., buy, hold, sell). \

            **Instructions:** \
            - If the initial set of articles is insufficient, perform additional searches to gather more information. \
            - Ensure that your analysis is based solely on the retrieved news articles and does not include external data sources. \
            - Present your findings in a clear and concise manner, suitable for a financial report. \

            **Stock Ticker:** \
            **Industry Context:** \
            **Additional Information:**
            """

    model_id = "anthropic.claude-3-haiku-20240307-v1:0" # You can change this to any Claude Anthropic model.
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION")

    model = ChatBedrock(model=model_id,
                region=aws_region, 
                aws_access_key_id=aws_access_key, 
                aws_secret_access_key=aws_secret_key)
    
    with MongoDBSaver.from_conn_string(MONGODB_URI, DATABASE_NAME) as checkpointer:
        abot = Agent(model, [tool], system=prompt, checkpointer=checkpointer)
        # thread_id will be used to keep track of different threads inside the persistent checkpointer
        # this will allows us to have multiple conversations going on at the same time
        # this is really needed for production apps where you generally have multiple users 
        # this thread config is simply a dictionary with a configurable key. It could be equal to any string.
        config = {"configurable": {"thread_id": "1"}}

        messages = [HumanMessage(content="Which one you would suggest as best investment based on latest news and why?")]
        result = abot.graph.invoke({"messages": messages}, config)

    ascii_graph = abot.graph.get_graph().draw_ascii()
    print(ascii_graph)

    print(result['messages'])

if __name__ == '__main__':
    main()