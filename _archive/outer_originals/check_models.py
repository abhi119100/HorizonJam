#!/usr/bin/env python3

import os
from pathlib import Path

def check_local_models():
    print("🔍 Checking for local sentence-transformers models...")
    
    # Check common cache locations
    cache_locations = [
        Path.home() / ".cache" / "huggingface" / "transformers",
        Path.home() / ".cache" / "torch" / "sentence_transformers",
        Path.home() / ".cache" / "sentence_transformers",
        Path("models"),  # Local models directory
        Path(".") / "sentence_transformers_cache"
    ]
    
    for cache_dir in cache_locations:
        print(f"\nChecking: {cache_dir}")
        if cache_dir.exists():
            print(f"  ✅ Exists")
            try:
                contents = list(cache_dir.iterdir())[:10]
                print(f"  Contents (first 10): {[c.name for c in contents]}")
            except Exception as e:
                print(f"  ❌ Error reading contents: {e}")
        else:
            print(f"  ❌ Does not exist")
    
    print("\n🔧 Trying alternative embedding approaches...")
    
    # Try to use a simpler embedding approach
    try:
        print("\n1. Testing basic sentence-transformers import...")
        from sentence_transformers import SentenceTransformer
        print("   ✅ sentence-transformers imported successfully")
        
        # Try to use a model that might be cached or available offline
        print("\n2. Testing model loading with offline mode...")
        import os
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        
        try:
            model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder='./models')
            print("   ✅ Model loaded successfully in offline mode")
            return True
        except Exception as e:
            print(f"   ❌ Offline model loading failed: {e}")
            
        # Try alternative models
        alternative_models = [
            'paraphrase-MiniLM-L6-v2',
            'all-mpnet-base-v2',
            'distilbert-base-nli-mean-tokens'
        ]
        
        print("\n3. Testing alternative models...")
        for model_name in alternative_models:
            try:
                print(f"   Trying {model_name}...")
                model = SentenceTransformer(model_name)
                print(f"   ✅ {model_name} loaded successfully")
                return True
            except Exception as e:
                print(f"   ❌ {model_name} failed: {e}")
                
    except Exception as e:
        print(f"❌ sentence-transformers import failed: {e}")
    
    return False

if __name__ == "__main__":
    success = check_local_models()
    if not success:
        print("\n💡 Suggestions:")
        print("1. Set up Hugging Face authentication: huggingface-cli login")
        print("2. Download models manually to a local directory")
        print("3. Use a different embedding approach (e.g., OpenAI embeddings)")
        print("4. Work offline with pre-downloaded models")