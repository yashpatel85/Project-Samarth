import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY not found in .env")
    exit()

try:
    print("Configuring Google API...")
    genai.configure(api_key=GOOGLE_API_KEY)

    print("Checking available models...")
    # List models to ensure the API connection is working
    models_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    print(f"Available models: {models_list}")

    # Choose a modern model name directly supported by the library
    # Let's use the one LangChain was trying
    model_name = "models/gemini-1.5-pro-latest"
    if model_name not in models_list:
        # Fallback if the latest isn't listed (shouldn't happen with latest lib)
         model_name = "models/gemini-1.0-pro"
         if model_name not in models_list:
             print(f"Error: Neither gemini-1.5-pro-latest nor gemini-1.0-pro found!")
             exit()

    print(f"Attempting to use model: {model_name}")
    model = genai.GenerativeModel(model_name)

    print("Sending a simple prompt...")
    response = model.generate_content("Explain AI in one sentence.")

    print("\n--- SUCCESS ---")
    print(response.text)

except Exception as e:
    print("\n--- ERROR ---")
    print(f"An error occurred: {e}")
    # Print detailed traceback if it's a Google API error
    if hasattr(e, 'grpc_status_code'):
        import traceback
        traceback.print_exc()