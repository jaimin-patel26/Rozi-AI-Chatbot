import os
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

from dotenv import load_dotenv

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

main_directory_path = os.getenv("MAIN_DIRECTORY_PATH")

embedding = OpenAIEmbeddings(model="text-embedding-3-large")

vectorstore = FAISS.load_local(
    main_directory_path+"/app/Agent/Vector_Store/Public/FAQS",
    embeddings=embedding,
    allow_dangerous_deserialization=True
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a strict assistant.\n"
     "You must answer the user's question using ONLY the provided context.\n"
     "If the answer is not found clearly in the context, reply exactly: 'Sorry, I don't know.'\n"
     "Do not use your own knowledge. Do not make assumptions.\n\n"
     "Context:\n{context}"),
    ("human", "{input}")
])
  
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

qa_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
 
chain = create_retrieval_chain(retriever, qa_chain)

def handle_faq_query(query):
    result = chain.invoke({"input": query})
    return result['answer']
 
 
 
 
