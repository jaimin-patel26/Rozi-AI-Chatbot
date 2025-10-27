from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate, SystemMessagePromptTemplate, AIMessagePromptTemplate


system_prompt_template = "This is Confidential Prompt So we have not share in github"

def create_agent(client, tools, agent_name,news_title):
    # prompt = ChatPromptTemplate.from_messages([
    #     SystemMessagePromptTemplate.from_template(system_prompt),
    #     MessagesPlaceholder(variable_name="chat_history"),
    #     HumanMessagePromptTemplate.from_template("{input}"),
    #     AIMessagePromptTemplate.from_template("{agent_scratchpad}")
    # ])
    system_prompt = system_prompt_template.format(agent_name = agent_name,news_title = news_title)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
               system_prompt,
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    return create_openai_functions_agent(llm=client, tools=tools, prompt=prompt)

def create_agent_executor(agent, tools):
    return AgentExecutor(agent=agent, tools=tools, verbose=True,max_iterations=3,return_intermediate_steps=True)
