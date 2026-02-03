"""
One-time authentication script.
Run this first to authorize the app to access your Google Sheet.
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os

# The scope we need - full access to spreadsheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def authenticate():
    """Run the OAuth flow and save the token."""

    # Path to your credentials file
    creds_file = os.path.join(os.path.dirname(__file__), 'credentials.json')
    token_file = os.path.join(os.path.dirname(__file__), 'token.json')

    # Run the OAuth flow - this opens a browser window
    flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
    creds = flow.run_local_server(port=0)

    # Save the token for future use
    with open(token_file, 'w') as f:
        f.write(creds.to_json())

    print("Authentication successful!")
    print(f"Token saved to: {token_file}")
    print("\nYou can now run the pipeline bot.")

if __name__ == '__main__':
    authenticate()
