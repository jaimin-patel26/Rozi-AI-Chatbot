from langchain.agents import tool
from .agent_faqs import handle_faq_query
from .agent_real_estate import handle_real_estate_query
from .agent_news import handle_news_query
from .private_agent_question_answering import private_agent_question_answering

from app.schemas import PropertyInput

@tool
def real_estate_tool(location:PropertyInput, query: str):
    """
    Handles any query related to real estate—including informational, analytical, or statistical queries such as average, count, or sum.

    Required Fields (from PropertyInput):
    - Country (str): The country of interest (e.g., "USA", "India").
    - state (str): The state or region (e.g., "California", "Gujarat").
    - accommodation (optional): Number of persons to accommodate (e.g., "2").

    Special Handling:
    - If the user provides a long-form country name (e.g., "United Kingdom", "United States", "United Arab Emirates"), it will be normalized to short form ("UK", "USA", "UAE").
    - If the user provides only the City, the system will attempt to determine the corresponding country.
        - NOTE: If the state is "Victoria", the country will be strictly set to "USA".
    - For the following countries: **Vietnam**, **Thailand**, **Singapore**, **Hong Kong**, and **Indonesia** country and state are considered the same. So if any of these countries are identified, treat the `state` value as the country name itself.
    - Do NOT modify or rephrase the original query.
    - Do NOT ask the user for missing values beyond the above handling.
    - Use ONLY the information explicitly provided in the query and location input.

    This tool should be invoked immediately if the query involves real estate in any form.

    Example: "Provide the name of a building with an area greater than 10,000 sq ft."
    """
    return handle_real_estate_query(location, query)

@tool(return_direct=False)
def faq_tool(query: str) -> str:
    """
    This tool handles all user queries related to venue bookings, cancellations, payments, catering, booking modifications, venue availability, refunds, receipts, booking policies, venue features (e.g., sustainability, pet-friendliness), and contact support. It provides instant answers to common questions such as how to book, cancel, amend, or extend reservations; how refunds and payments work; available amenities; venue search by location; and accessing terms or invoices.
    """
    return handle_faq_query(query)

@tool(return_direct=False)
def news_insights_tool(query: str) -> str:
    """
    Use this for recent updates, current events, or news-related content. Also, apply this if the user asks questions about meeting room registration or the signup process.
    """
    return handle_news_query(query)

def other_query_tool_factory(faiss_path: str):
    @tool
    def other_query_tool(query: str) -> str:
        """Use this tool for handling other queries."""
        return private_agent_question_answering(faiss_path, query)
    return other_query_tool


def create_tools(agent_instance=None):
    """
    Returns a list of integrated tools that the agent can utilize
    for answering queries related to real estate, FAQs, and news and other query.
    """
    return [real_estate_tool, faq_tool, news_insights_tool,other_query_tool_factory(agent_instance.faiss_path)]
