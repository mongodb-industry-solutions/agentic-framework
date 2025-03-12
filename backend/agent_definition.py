from datetime import datetime

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent_llm import get_llm
from agent_tools import tools


llm = get_llm(model_id="anthropic.claude-3-haiku-20240307-v1:0")

def create_agent(llm, tools, system_message: str):
    """Create an agent

    Args:
        llm (ChatBedrock): The ChatBedrock instance to use.
        tools (List[Callable]): The list of tools to bind to the agent.
        system_message (str): The system message to display to the agent.

    Returns:
        ChatAgent: The created ChatAgent instance.
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful AI assistant, collaborating with other assistants."
                " Use the provided tools to progress towards answering the question."
                " If you are unable to fully answer, that's OK, another assistant with different tools "
                " will help where you left off. Execute what you can to make progress."
                " If you or any of the other assistants have the final answer or deliverable,"
                " prefix your response with FINAL ANSWER so the team knows to stop."
                " You have access to the following tools: {tool_names}.\n{system_message}"
                "\nCurrent time: {time}.",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(time=lambda: str(datetime.now()))
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))

    return prompt | llm.bind_tools(tools)


# Chatbot agent and node
chatbot_agent = create_agent(
    llm,
    tools,
    system_message="You are helpful HR Chabot Agent.",
)