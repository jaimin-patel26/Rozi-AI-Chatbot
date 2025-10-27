from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()


os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

embedding_model=OpenAIEmbeddings(model="text-embedding-3-large")

def private_agent_question_answering(faiss_path, query):

    if not os.path.exists(faiss_path):
        #raise FileNotFoundError(f"FAISS index not found at path: {faiss_path}")
        return "Sorry I Dont Know Answer"
    else:
        try:
            vectorstore = FAISS.load_local(
                faiss_path,
                embeddings=embedding_model,
                allow_dangerous_deserialization=True
            )
        except Exception as e:
            raise RuntimeError(f"Error loading FAISS vectorstore: {e}")

        try:
            retriever = vectorstore.as_retriever(search_kwargs={"k": 8})
            retrieved_docs = retriever.invoke(query)

            context = "\n\n".join([doc.page_content for doc in retrieved_docs])
            main_context = f"""You are a helpful assistant.

                Answer the following query based only on the given context. Use the most relevant parts of the context.

                If the query cannot be answered using the context, reply with: "I don’t have the data related to this query."

                Query: {query}

                Context:
                {context}
                """

            # print(context)

            return main_context


        except Exception as e:
            raise RuntimeError(f"Error during context retrieval: {e}")
