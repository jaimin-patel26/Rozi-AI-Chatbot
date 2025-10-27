
from langchain_community.document_loaders import CSVLoader, TextLoader, PyPDFLoader
import os


def load_document(file_path, file_ext):
    file_path = os.path.normpath(file_path)
    if file_ext == ".pdf":
        return PyPDFLoader(file_path).load()
    elif file_ext == ".csv":
        return CSVLoader(file_path, autodetect_encoding=True).load()
    elif file_ext == ".txt":
        return TextLoader(file_path).load()
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")