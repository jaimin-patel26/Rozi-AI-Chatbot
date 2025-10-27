
from langchain_openai import  ChatOpenAI
from langchain_core.messages import HumanMessage 
from .agent_managers import create_agent, create_agent_executor
from .tools import create_tools
import os
from dotenv import load_dotenv
import tiktoken

load_dotenv()

class PropertyAgent:
    def __init__(self,messages, agent_name ,title_name ,faiss_path):
        self.API_KEY = os.getenv("OPENAI_API_KEY")
        self.Model = "gpt-4o-mini"
        self.client = ChatOpenAI(
            api_key=self.API_KEY,
            model=self.Model,
        )
        self.ENCODING = "cl100k_base"
        self.message = messages
        self.user_input = ""
        self.agent_name = agent_name
        self.news_title = title_name
        self.faiss_path = faiss_path
        self.encoding = tiktoken.encoding_for_model("gpt-4-0613")

    def num_tokens_from_string(self, string: str) -> int:
        """Returns the number of tokens in a text string."""
        return len(self.encoding.encode(string))
    
    def run_conversation(self, user_input):
        """Run the conversation with the agent."""
        self.user_input = user_input
        self.message.append(HumanMessage(content=user_input))
        tools = create_tools(self)
        agent = create_agent(self.client, tools=tools, agent_name=self.agent_name,news_title = self.news_title)
        agent_executor = create_agent_executor(agent, tools)
        
        max_response_tokens = 250
        token_limit = 50000

        def calculate_token_length(messages):
            num_tokens = 0
            for message in messages:
                num_tokens += 3
                num_tokens += len(self.encoding.encode(message.content))
            num_tokens += 3  
            return num_tokens

        def ensure_message_length_within_limit():
            conv_history_tokens = calculate_token_length(self.message)
            while conv_history_tokens + max_response_tokens >= token_limit:
                if len(self.message) > 1:
                    del self.message[1]
                    conv_history_tokens = calculate_token_length(self.message)
                else:
                    break
        
        ensure_message_length_within_limit()
        response = agent_executor.invoke({"input": user_input, "chat_history": self.message})

        return response
         
