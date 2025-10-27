from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate, SystemMessagePromptTemplate, AIMessagePromptTemplate


system_prompt_template = """This is Confidential Prompt So we have not shared"""

def create_agent(client, tools, agent_name):

    system_prompt = system_prompt_template.format(agent_name = agent_name)
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{input}"),
        AIMessagePromptTemplate.from_template("{agent_scratchpad}")
    ])
    return create_openai_functions_agent(llm=client, tools=tools, prompt=prompt)

def create_agent_executor(agent, tools):
    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=2)