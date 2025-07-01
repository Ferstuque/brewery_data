import requests
import json
import os
from time import time


# API Endpoints
url_raw = "https://api.openbrewerydb.org/v1/breweries"
meta_url = "https://api.openbrewerydb.org/v1/breweries/meta"

# Function to send a GET request and return a JSON response
def request_api(url):
    try:
        response = requests.request("GET", url)
        response.raise_for_status() 
        json_response = response.json()
            
        return json_response
    
    except requests.exceptions.HTTPError as http_err:
        print(f"Error HTTP: {http_err}")
        return None
    except Exception as err:
        print(f"Other error: {err}")
        return None

# Request metadata to find out the total number of breweries
meta_data = request_api(meta_url)

if meta_data and 'total' in meta_data:
    total_breweries = meta_data['total']
    
    print(f"\nThe total is: {total_breweries}")
    
    # Calculate number of pages based on fixed items per page
    per_page = 50
    total_pages = (total_breweries + per_page - 1) // per_page 
    print(f"With {per_page} breweries, it would take {total_pages} pages to extract all the content.")
else:
    print("\nThe system was unable to retrieve the total. The 'total' key was missing from the request.")

# Loop through all pages and fetch the data
for page_number in range(1, total_pages + 1):
    url_paginated = f"https://api.openbrewerydb.org/v1/breweries?page={page_number}&per_page={per_page}"
    
    # Fetch data for the page
    data_page = request_api(url_paginated)
    print(json.dumps(data_page, indent=4))