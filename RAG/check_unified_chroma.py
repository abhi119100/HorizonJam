#!/usr/bin/env python3
"""
Check contents of the unified ChromaDB store
"""

import chromadb
from chromadb.config import Settings
import os

# Initialize ChromaDB client
db_path = "unified_chroma_store"
client = chromadb.PersistentClient(path=db_path)

print(f"📊 Checking ChromaDB at: {os.path.abspath(db_path)}")

try:
    # Get the music_theory collection
    collection = client.get_collection(name="music_theory")
    
    # Get basic stats
    count = collection.count()
    print(f"✅ Total documents in music_theory collection: {count}")
    
    if count > 0:
        # Get a sample of documents to see what's stored
        results = collection.get(limit=5, include=["documents", "metadatas"])
        
        print("\n📋 Sample documents:")
        for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
            print(f"\n--- Document {i+1} ---")
            print(f"Type: {metadata.get('type', 'unknown')}")
            print(f"Topic: {metadata.get('topic', 'unknown')}")
            print(f"Source: {metadata.get('source', 'unknown')}")
            print(f"Content preview: {doc[:200]}...")
        
        # Search for soloing-related content
        print("\n🎸 Searching for soloing/improvisation content...")
        solo_results = collection.query(
            query_texts=["guitar solo techniques improvisation scales pentatonic lead guitar"],
            n_results=3,
            include=["documents", "metadatas"]
        )
        
        if solo_results['documents'][0]:  # Check if any results
            print("Found soloing-related content:")
            for i, (doc, metadata) in enumerate(zip(solo_results['documents'][0], solo_results['metadatas'][0])):
                print(f"\n--- Solo Result {i+1} ---")
                print(f"Type: {metadata.get('type', 'unknown')}")
                print(f"Topic: {metadata.get('topic', 'unknown')}")
                print(f"Content: {doc[:300]}...")
        else:
            print("❌ No soloing-related content found")
            
    else:
        print("❌ No documents found in the collection")
        
except Exception as e:
    print(f"❌ Error accessing collection: {e}")
    
    # List available collections
    try:
        collections = client.list_collections()
        print(f"\n📚 Available collections: {[c.name for c in collections]}")
    except Exception as e2:
        print(f"❌ Error listing collections: {e2}")