import os
from dotenv import load_dotenv
from google import genai

# Load .env from current directory
load_dotenv('.env')

def test_api_key():
    api_key = os.getenv("GEMINI_API_KEY")
    
    print(f"Current working directory: {os.getcwd()}")
    print(f"Raw API key from env: '{api_key}'")
    print(f"API key length: {len(api_key) if api_key else 0}")
    
    # Also try reading the file directly
    try:
        with open('.env', 'r') as f:
            content = f.read()
            print(f".env file content: '{content}'")
    except Exception as e:
        print(f"Error reading .env file: {e}")
    
    if not api_key:
        print("❌ No API key found in .env file")
        return False
    
    # Clean the API key (remove quotes and whitespace)
    api_key = api_key.strip().strip('"').strip("'")
    print(f"Cleaned API key: '{api_key}'")
    print(f"Starts with AIza: {api_key.startswith('AIza')}")
    
    if not api_key.startswith("AIza"):
        print("❌ API key format looks incorrect (should start with 'AIza')")
        return False
    
    try:
        client = genai.Client(api_key=api_key)
        # Simple test request
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=["Say hello"]
        )
        print("✅ API key is working!")
        print(f"Response: {response.text}")
        return True
    except Exception as e:
        print(f"❌ API key test failed: {e}")
        return False

if __name__ == "__main__":
    test_api_key()