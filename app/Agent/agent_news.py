from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import os
from dotenv import load_dotenv

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

main_directory_path = os.getenv("MAIN_DIRECTORY_PATH")

embedding_model=OpenAIEmbeddings(model = "text-embedding-3-large")

vectorstore=FAISS.load_local(main_directory_path+"/app/Agent/Vector_Store/Public/News",embeddings=embedding_model,allow_dangerous_deserialization=True)
retriever=vectorstore.as_retriever(search_kwargs={"k": 3})

prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a helpful assistant.\n"
     "Use only the context to answer the user's question.\n"
     "If the answer is not in the context, reply: 'Sorry, I don't know.'\n"
     "Context:\n{context}"),
    ("human", "{input}")
])


llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

qa_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
chain_news = create_retrieval_chain(retriever, qa_chain)

def handle_news_query(query):
    result = chain_news.invoke({"input": query})
    return result['answer']


