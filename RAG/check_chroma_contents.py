from langchain_community.vectorstores import Chroma

vectordb = Chroma(persist_directory="chroma_store")
print(f"✅ Total documents in ChromaDB: {vectordb._collection.count()}")
