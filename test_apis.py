#!/usr/bin/env python3
"""
Test script to find the correct working Sonnet model
Run this before running the main app to verify API setup
"""

import os
from dotenv import load_dotenv
from services.llm_providers import create_test_clients, SonnetClient

def test_sonnet_models():
    """Test all possible Sonnet model names to find the working one"""
    load_dotenv()
    
    sonnet_key = os.getenv("SONNET_API_KEY") 
    if not sonnet_key:
        print("❌ SONNET_API_KEY not found in .env file")
        return None
    
    print("🧪 Testing Sonnet model names...")
    
    # Test different model names based on the search results
    model_candidates = [
        "claude-3-5-sonnet-20241022",    # Latest Claude 3.5 Sonnet
        "claude-3-5-sonnet-20240620",    # Previous Claude 3.5 Sonnet
        "claude-sonnet-4-20250514",      # Claude 4 Sonnet (if available)
        "claude-3-7-sonnet-20250219",    # Claude 3.7 Sonnet
        "claude-3-sonnet-20240229",      # Old Claude 3 Sonnet (might still work)
    ]
    
    for model_name in model_candidates:
        print(f"  Testing: {model_name}...", end=" ")
        
        try:
            client = SonnetClient(sonnet_key, model=model_name, max_tokens=50)
            
            # Simple test request
            test_schema = {
                "test_field": "string",
                "test_number": "number"
            }
            
            result = client.generate_json("Generate a simple test JSON with test_field='hello' and test_number=123", test_schema)
            
            if not result.get("error"):
                print("✅ WORKS!")
                print(f"    Response: {result}")
                return model_name
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    print("\n❌ No working Sonnet model found!")
    return None

def test_deepseek_timeout():
    """Test DeepSeek with a timeout scenario"""
    load_dotenv()
    
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_key:
        print("❌ DEEPSEEK_API_KEY not found in .env file")
        return False
    
    print("🧪 Testing DeepSeek with timeout handling...")
    
    try:
        from services.llm_providers import DeepSeekClient
        
        client = DeepSeekClient(deepseek_key, max_tokens=100)  # Smaller token limit for faster response
        
        # Simple test
        result = client.generate("Write a brief test message.")
        
        if result.content.startswith("Error"):
            print(f"❌ DeepSeek Error: {result.content}")
            return False
        else:
            print("✅ DeepSeek works!")
            print(f"    Response preview: {result.content[:100]}...")
            return True
            
    except Exception as e:
        print(f"❌ DeepSeek Exception: {str(e)}")
        return False

def main():
    print("🚀 API Model Testing")
    print("=" * 50)
    
    # Test DeepSeek
    deepseek_works = test_deepseek_timeout()
    print()
    
    # Test Sonnet models
    working_sonnet_model = test_sonnet_models()
    print()
    
    # Summary
    print("=" * 50)
    print("📊 TEST RESULTS:")
    print(f"DeepSeek API: {'✅ Working' if deepseek_works else '❌ Not working'}")
    print(f"Sonnet API: {'✅ Working' if working_sonnet_model else '❌ Not working'}")
    
    if working_sonnet_model:
        print(f"\n🔧 RECOMMENDED SONNET MODEL: {working_sonnet_model}")
        print(f"Update your services/llm_providers.py SonnetClient __init__ to use:")
        print(f'model: str = "{working_sonnet_model}"')
    
    print("=" * 50)
    
    if deepseek_works and working_sonnet_model:
        print("🎉 Both APIs are working! You can now run: python app.py")
    else:
        print("⚠️  Fix the API issues above before running the main application")
    
    return working_sonnet_model

if __name__ == "__main__":
    working_model = main()