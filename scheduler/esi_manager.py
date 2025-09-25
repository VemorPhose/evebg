import configparser
import webbrowser
import requests
import json
import os
import base64
import secrets # Import the secrets module for generating the state token
from urllib.parse import urlparse, parse_qs
from collections import defaultdict

class EsiManager:
    """Handles ESI authentication and data fetching."""
    
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        self.client_id = self.config['ESI']['client_id']
        self.client_secret = self.config['ESI']['client_secret']
        self.callback_url = self.config['ESI']['callback_url']
        self.structure_ids = [s.strip() for s in self.config['STRUCTURE']['structure_ids'].split(',')]
        self.character_name = self.config['CHARACTER']['character_name']

        self.tokens = {}
        self.state = None # Will be used to store the state token
        print(f"ESI Manager initialized for structures: {self.structure_ids}")

    def _get_auth_url(self):
        """Generates the full ESI authentication URL."""
        # Generate a secure, random state token for CSRF protection
        self.state = secrets.token_urlsafe(16)
        
        base_url = "https://login.eveonline.com/v2/oauth/authorize/?"
        params = {
            'response_type': 'code',
            'redirect_uri': self.callback_url,
            'client_id': self.client_id,
            'scope': 'esi-assets.read_assets.v1',
            'state': self.state  # Include the state token in the request
        }
        return base_url + requests.compat.urlencode(params)

    def _process_callback(self, callback_url):
        """
        Processes the callback URL from EVE SSO, verifies the state, 
        and exchanges the authorization code for tokens.
        """
        try:
            parsed_url = urlparse(callback_url)
            query_params = parse_qs(parsed_url.query)

            # --- Verify the state parameter ---
            received_state = query_params.get('state', [None])[0]
            if not received_state or received_state != self.state:
                print("\nERROR: State parameter mismatch. Authentication aborted for security reasons.")
                return False

            auth_code = query_params.get('code', [None])[0]
            if not auth_code:
                print("\nERROR: Authorization code not found in callback URL.")
                return False

            # Exchange code for tokens
            token_url = "https://login.eveonline.com/v2/oauth/token"
            auth_string = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            headers = {'Authorization': f'Basic {auth_string}', 'Content-Type': 'application/x-www-form-urlencoded'}
            data = {'grant_type': 'authorization_code', 'code': auth_code}
            
            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status() # Will raise an exception for HTTP errors
            
            self.tokens = response.json()
            with open('tokens.json', 'w') as f:
                json.dump(self.tokens, f)
            print("Tokens received and saved successfully.")
            return True

        except requests.exceptions.RequestException as e:
            print(f"\nAn HTTP error occurred: {e}")
            print(f"Response content: {e.response.text if e.response else 'N/A'}")
            return False
        except (KeyError, IndexError) as e:
            print(f"\nError parsing the callback URL. Make sure you copied the full URL. Error: {e}")
            return False

    def _refresh_tokens(self):
        """Refreshes the access token using the refresh token."""
        try:
            refresh_token = self.tokens.get('refresh_token')
            if not refresh_token:
                return False

            token_url = "https://login.eveonline.com/v2/oauth/token"
            auth_string = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            headers = {'Authorization': f'Basic {auth_string}', 'Content-Type': 'application/x-www-form-urlencoded'}
            data = {'grant_type': 'refresh_token', 'refresh_token': refresh_token}

            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            
            new_tokens = response.json()
            self.tokens['access_token'] = new_tokens['access_token']
            self.tokens['expires_in'] = new_tokens['expires_in']
            # EVE SSO might or might not return a new refresh token. If it does, update it.
            if 'refresh_token' in new_tokens:
                self.tokens['refresh_token'] = new_tokens['refresh_token']

            with open('tokens.json', 'w') as f:
                json.dump(self.tokens, f)
            print("Access token refreshed.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to refresh token: {e}")
            return False
    
    def authenticate(self):
        """Main authentication flow."""
        if os.path.exists('tokens.json'):
            with open('tokens.json', 'r') as f:
                self.tokens = json.load(f)
            if self._refresh_tokens():
                return True
        
        # If no tokens or refresh failed, start full auth flow
        print("\n--- EVE Online Authentication Required ---")
        auth_url = self._get_auth_url()
        print("Your browser will now open for EVE Online authentication.")
        webbrowser.open(auth_url)
        
        callback_url = input("Please log in, and then paste the full callback URL from your browser here:\n> ")
        return self._process_callback(callback_url)

    def get_inventory(self):
        """
        Fetches asset lists from all configured structures and aggregates them.
        Returns a dictionary of {type_id: total_quantity}.
        """
        access_token = self.tokens.get('access_token')
        if not access_token:
            print("Authentication required.")
            return {}

        # First, we need the character ID to make the authenticated call
        char_info_url = "https://esi.evetech.net/verify/"
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(char_info_url, headers=headers)
        if response.status_code != 200:
            print(f"Could not verify character info. Status: {response.status_code}")
            return {}
        character_id = response.json()['CharacterID']
        
        aggregated_inventory = defaultdict(int)

        for structure_id in self.structure_ids:
            print(f"Fetching assets from structure {structure_id}...")
            page = 1
            while True:
                assets_url = f"https://esi.evetech.net/v5/characters/{character_id}/assets/"
                params = {'page': page}
                response = requests.get(assets_url, headers=headers, params=params)

                if response.status_code == 403: # Token expired
                    if not self._refresh_tokens(): 
                        print("Authentication failed during asset fetch.")
                        return {}
                    headers['Authorization'] = f'Bearer {self.tokens.get("access_token")}'
                    continue # Retry the request

                if response.status_code != 200:
                    print(f"Error fetching assets from structure {structure_id}, page {page}. Status: {response.status_code}")
                    break
                
                assets_page = response.json()
                if not assets_page:
                    break # No more assets on subsequent pages

                for asset in assets_page:
                    # We are only interested in assets inside the specified structure
                    if str(asset.get('location_id')) == str(structure_id):
                        aggregated_inventory[asset['type_id']] += asset['quantity']
                
                # Check for more pages
                if 'x-pages' in response.headers and int(response.headers['x-pages']) > page:
                    page += 1
                else:
                    break
        
        print(f"Inventory fetch complete. Found {len(aggregated_inventory)} unique item types.")
        return dict(aggregated_inventory)

