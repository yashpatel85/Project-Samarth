import os
import requests
import pandas as pd
from dotenv import load_dotenv
from io import StringIO
import json

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

DATA_GOV_API_KEY = os.getenv("DATA_GOV_API_KEY")
BASE_URL = "https://api.data.gov.in/resource/"

def fetch_data_from_resource(resource_id: str, limit: int = 1000) -> (pd.DataFrame, str):

    if not DATA_GOV_API_KEY:
        print("Error: DATA_GOV_API_KEY not found. Set it in the .env file.")
        return pd.DataFrame(), ""
    
    url = f"{BASE_URL}{resource_id}"
    params = {
        "api-key": DATA_GOV_API_KEY,
        "format": "json",
        "limit": str(limit)
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        if 'records' in data and data['records']:
            df = pd.DataFrame(data['records'])
            title = data.get('title', 'No Title Found')
            print(f"Successfully fetched {len(df)} records from '{title}'")
            return df, title
        
        else:
            print(f"Error: Resource '{resource_id}' returned no records or was empty.")
            print(f"Raw Response: {json.dumps(data, indent=2)}")
            return pd.DataFrame(), ""
        
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - {response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except requests.exceptions.JSONDecodeError:
        print(f"Error: Failed to decode JSON. Response was: {response.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return pd.DataFrame(), ""


# --- This part is for testing the function directly ---
if __name__ == "__main__":
    print("Testing data_fetch.py...")
    
    # Test 1: Crop Production (Known Good ID)
    CROP_ID = "35be999b-0208-4354-b557-f6ca9a5355de"
    print(f"\n--- Fetching Crop Production (ID: {CROP_ID}) ---")
    crop_df, crop_title = fetch_data_from_resource(CROP_ID, limit=5)
    if not crop_df.empty:
        print("Test 1 SUCCESS. DataFrame head:")
        print(crop_df.head())
        print(f"Source Title: {crop_title}")

    # Test 2: Commodity Prices (Known Good ID)
    PRICE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
    print(f"\n--- Fetching Commodity Prices (ID: {PRICE_ID}) ---")
    price_df, price_title = fetch_data_from_resource(PRICE_ID, limit=5)
    if not price_df.empty:
        print("Test 2 SUCCESS. DataFrame head:")
        print(price_df.head())
        print(f"Source Title: {price_title}")