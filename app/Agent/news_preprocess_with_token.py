import os
import pandas as pd
from bs4 import BeautifulSoup
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import  OpenAIEmbeddings
import shutil

from dotenv import load_dotenv

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

main_directory_path = os.getenv("MAIN_DIRECTORY_PATH")

df = pd.read_csv(main_directory_path+"/app/Public_Data_Files/Final_News_2.csv")

def clean_html(html):
    return BeautifulSoup(str(html), "html.parser").get_text(separator=" ")

df["clean_body"] = df["body"].apply(clean_html)
df["content"] = df["title"] + ". " + df["meta_description"] + " " + df["clean_body"]

docs = [
    Document(
        page_content=row["content"],
        metadata={
            "title": row["title"],
            "url": row["post_url"],
            "category": row["category"]
        }
    )
    for _, row in df.iterrows()
]

#embedding = OpenAIEmbeddings(model = "text-embedding-3-large")
#vectorstore = FAISS.from_documents(docs, embedding)
#vectorstore.save_local(folder_path=r"Vector_Store\Public\News")

vectorstore_path = os.path.join("Vector_Store", "Public", "News")


# If FAISS store already exists, delete it
if os.path.exists(vectorstore_path):
    print(f"Vector store already exists at '{vectorstore_path}'. Removing it...")
    shutil.rmtree(vectorstore_path)
else:
    print(f"No existing vector store found at '{vectorstore_path}'. Creating a new one...")

embedding = OpenAIEmbeddings(model="text-embedding-3-large")
vectorstore = FAISS.from_documents(docs, embedding)
vectorstore.save_local(folder_path=vectorstore_path)

print("Vector store created and saved successfully.")

