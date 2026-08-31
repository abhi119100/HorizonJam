#!/usr/bin/env python3
"""Check contents of the enhanced ChromaDB store"""
import chromadb
import os
from chromadb.config import Settings

db_path = "enhanced_chroma_store"
print(f"📊 Checking ChromaDB at: {os.path.abspath(db_path)}")

client = chromadb.PersistentClient(path=db_path)
collections = client.list_collections()
print(f"Available collections: {[c.name for c in collections]}")

for col in collections:
    try:
        collection = client.get_collection(name=col.name)
        count = collection.count()
        print(f"Collection '{col.name}': {count} documents")
    except Exception as e:
        print(f"❌ Error reading collection {col.name}: {e}")