from langchain.agents import tool
from .private_agent_question_answering import private_agent_question_answering

def question_answering_tool_factory(faiss_path: str):
    @tool
    def question_answering_tool(query: str) -> str:
        """Use this tool for every FAQ query."""
        return private_agent_question_answering(faiss_path, query)
    return question_answering_tool


def create_tools(agent_instance=None):
    """
    Returns a list of integrated tools that the agent can utilize
    for answering queries.
    """
    return [question_answering_tool_factory(agent_instance.faiss_path)]
