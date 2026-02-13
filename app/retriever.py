import os
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import embeddings

VECTOR_PATH = "data/faiss_index"

_vectorstore = None


def build_vector_store():
    global _vectorstore

    if _vectorstore:
        return _vectorstore

    if os.path.exists(VECTOR_PATH):
        _vectorstore = FAISS.load_local(
            VECTOR_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        return _vectorstore

    with open("data/knowledge_base.txt", "r", encoding="utf-8") as f:
        text = f.read()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    docs = splitter.create_documents([text])

    _vectorstore = FAISS.from_documents(docs, embeddings)
    _vectorstore.save_local(VECTOR_PATH)

    return _vectorstore


def retrieve_solution(vectorstore, query: str):
    docs = vectorstore.similarity_search(query, k=2)
    return "\n\n".join(d.page_content for d in docs)
