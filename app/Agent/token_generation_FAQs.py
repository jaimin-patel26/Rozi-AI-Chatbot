import os
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

main_directory_path = os.getenv("MAIN_DIRECTORY_PATH")

file_name = main_directory_path+"/app/Public_Data_Files/FAQs(Sheet1).csv" 
df = pd.read_csv(file_name, encoding="utf-8")

docs = [
    Document(
        page_content=f"Q: {row['Queries']}\nA: {row['Bot Response 1']}",
        metadata={"data": "public", "source":str(file_name)}
    )
    for _, row in df.iterrows()
]
 
embedding = OpenAIEmbeddings(model = "text-embedding-3-large")
vectorstore = FAISS.from_documents(docs, embedding)
vectorstore.save_local(folder_path=r"Vector_Store\Public\FAQS")
