#!/usr/bin/env python3

from chordai_gpt_tutor import ChordAIRAGTutor

def check_rag_status():
    print("Checking RAG System Status...")
    print("=" * 40)
    
    try:
        tutor = ChordAIRAGTutor()
        
        print(f"RAG System Initialized: {tutor.rag_system is not None}")
        print(f"DB Path: {tutor.db_path}")
        print(f"Collection Name: {tutor.collection_name}")
        
        if tutor.rag_system is not None:
            print("\n✅ RAG system is ACTIVE")
            
            # Test RAG context retrieval
            test_chord_results = {
                'analysis_summary': {
                    'detected_key': 'C major',
                    'chord_progression': ['C', 'Am', 'F', 'G']
                }
            }
            test_context = tutor._retrieve_rag_context(test_chord_results, "chord progression theory")
            print(f"\nRAG Context Test:")
            print(f"- Context retrieved: {len(test_context.get('context_chunks', [])) > 0}")
            
            context_chunks = test_context.get('context_chunks', [])
            if context_chunks:
                first_chunk = context_chunks[0].get('text', '')
                print(f"- Context length: {len(first_chunk)} characters")
                if len(first_chunk) > 0:
                    print(f"- Sample context: {first_chunk[:200]}...")
                    print("\n🎯 RAG enhancement is WORKING")
                else:
                    print("\n⚠️  RAG system initialized but NO context retrieved")
                    print("   This means responses are still vanilla GPT-4o")
            else:
                print("\n⚠️  RAG system initialized but NO context chunks returned")
                print("   This means responses are still vanilla GPT-4o")
        else:
            print("\n❌ RAG system is NULL (fallback mode)")
            print("   Responses are vanilla GPT-4o with chord analysis only")
            
    except Exception as e:
        print(f"\n❌ Error initializing tutor: {e}")
        print("   RAG system is not working")

if __name__ == "__main__":
    check_rag_status()