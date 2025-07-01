from airflow.providers.http.hooks.http import HttpHook
from unittest.mock import MagicMock
import requests
from math import ceil
import json
import time

class BreweryHook(HttpHook):

    def __init__(self, conn_id=None):
        """
        Set default per_page value and Airflow connection ID
        """
        self.per_page = 50
        self.conn_id = conn_id or "brewery_default"
        super().__init__(http_conn_id=self.conn_id)
        # Fallback URL in case Airflow connection is not configured
        if not self.base_url:
            self.log.warning(f"Conexão '{self.conn_id}' not found. Using fallback URL for local testing.")
            self.base_url = "https://api.openbrewerydb.org"

    def create_url(self, endpoint, params=None):
        """
        Builds the full URL including query parameters for the Open Brewery DB API.
        """
        url_raw = f"{self.base_url}{endpoint}"
        if params:
            query_string = "&".join([f"{key}={value}" for key, value in params.items()])
            url_raw = f"{url_raw}?{query_string}"
            
        return url_raw

    def connect_to_endpoint(self, url, session):
        """
        Sends a prepared GET request using the provided session.
        """
        request = requests.Request("GET", url)
        prep = session.prepare_request(request)
        self.log.info(f"URL: {url}")
        
        # O método `run_and_check` espera um objeto `PreparedRequest`
        # e não argumentos de URL, o que está correto aqui.
        return self.run_and_check(session, prep, {})

    def paginate(self, session):
        """
        Handles pagination logic to extract all brewery data from the API.
        """
        list_json_response = []
        
        # Step 1: Fetch metadata to determine total number of records
        meta_url = self.create_url("/v1/breweries/meta")
        response_meta = self.connect_to_endpoint(meta_url, session)
        meta_data = response_meta.json()
        
        total_breweries = meta_data.get('total', 0)
        if not total_breweries:
            self.log.warning("Could not retrieve total breweries. Returning empty list.")
            return list_json_response
        
        total_pages = ceil(total_breweries / self.per_page)
        self.log.info(f"Total records: {total_breweries}, extracting in {int(total_pages)} pages.")
        
        # Step 2: Iterate through pages and collect results
        for page_number in range(1, int(total_pages) + 1):
            params = {
                'page': page_number,
                'per_page': self.per_page
            }
            url_paginated = self.create_url("/v1/breweries", params=params)
            
            self.log.info(f"Extracting page {page_number}/{int(total_pages)}...")
            
            try:
                response = self.connect_to_endpoint(url_paginated, session)
                json_response = response.json()

                if json_response:
                    list_json_response.append(json_response)
                else:
                    self.log.info(f"Page {page_number} returned empty. Stopping pagination.")
                    break

                time.sleep(0.5) # Avoid API overload

            except Exception as e:
                self.log.error(f"Failed to extract page {page_number}: {e}")
                break 

        return list_json_response

    def run(self):
        """
        Main method that initiates the data extraction process.
        """
        session = self.get_conn() # Get HTTP session from Airflow connection
        self.log.info("Starting brewery paginated extraction...")
        return self.paginate(session)

# Testing Hook
if __name__ == "__main__":
    print("Starting local test for BreweryHook...") 
    
    try:
        hook = BreweryHook(conn_id="brewery_default")
        
        # Mock get_conn to simulate Airflow HTTP session
        from unittest.mock import MagicMock
        mock_session = requests.Session()
        hook.get_conn = MagicMock(return_value=mock_session)
        
        # Run extraction and show summary
        all_pages_data = hook.run()
        
        print("\n--- Extraction Completed ---")
        total_records = sum(len(page) for page in all_pages_data)
        print(f"Total records extracted: {total_records}")
        
        if all_pages_data and all_pages_data[0]:
            print("\nFirst 5 records of the first page:")
            print(json.dumps(all_pages_data[0][:5], indent=4))

    except Exception as e:
        print(f"An error occurred during test: {e}")