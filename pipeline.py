"""
Pipeline Bot - Manage your sales pipeline with natural language.
"""

import os
import json
import base64
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Your spreadsheet ID (from the URL)
SPREADSHEET_ID = '1qBcLw3q1fDJPYOwcegoVAe3qq3N3YNBG4zfY8Pm_xGk'

# Column mapping (A=1, B=2, etc.)
COLUMNS = {
    'company_name': 'A',
    'contact_name': 'B',
    'contact_email': 'C',
    'contact_phone': 'D',
    'project_description': 'E',
    'date_entered': 'F',
    'stage': 'G',
    'stage_date': 'H',
    'notes': 'I',
    'estimated_mrr': 'J',
    'priority': 'K',
    'next_action_date': 'L',
    'next_action': 'M',
    'lost_reason': 'N'
}

# Valid stages
STAGES = ['Lead', 'Discovery', 'Build POC', 'Proposal', 'Negotiation', 'Won', 'Lost']


def get_sheets_service():
    """Connect to Google Sheets."""
    # Try environment variable first (for deployment), then file (for local)
    token_b64 = os.environ.get('GOOGLE_TOKEN_B64')

    if token_b64:
        token_json = base64.b64decode(token_b64).decode('utf-8')
        creds_data = json.loads(token_json)
    else:
        token_file = os.path.join(os.path.dirname(__file__), 'token.json')
        with open(token_file, 'r') as f:
            creds_data = json.load(f)

    creds = Credentials.from_authorized_user_info(creds_data)
    service = build('sheets', 'v4', credentials=creds)
    return service.spreadsheets()


def normalize_header(header):
    """Convert header to lowercase with underscores."""
    return header.lower().replace(' ', '_')


def get_all_deals():
    """Fetch all deals from the spreadsheet."""
    sheets = get_sheets_service()

    # Get all data from the sheet
    result = sheets.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='A:N'
    ).execute()

    values = result.get('values', [])

    if not values:
        return []

    # First row is headers, rest are deals - normalize header names
    headers = [normalize_header(h) for h in values[0]] if values else []
    deals = []

    for i, row in enumerate(values[1:], start=2):  # start=2 because row 1 is headers
        deal = {'row_number': i}
        for j, header in enumerate(headers):
            deal[header] = row[j] if j < len(row) else ''
        deals.append(deal)

    return deals


def find_deal(company_name):
    """Find a deal by company name (case-insensitive partial match)."""
    deals = get_all_deals()
    company_lower = company_name.lower()

    for deal in deals:
        if company_lower in deal.get('company_name', '').lower():
            return deal

    return None


def update_deal(company_name, updates):
    """
    Update a deal's fields.

    Args:
        company_name: The company to update
        updates: Dict of field names to new values
    """
    deal = find_deal(company_name)

    if not deal:
        return f"Could not find a deal for '{company_name}'"

    sheets = get_sheets_service()
    row = deal['row_number']

    for field, value in updates.items():
        if field not in COLUMNS:
            continue

        col = COLUMNS[field]
        cell = f'{col}{row}'

        sheets.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=cell,
            valueInputOption='USER_ENTERED',
            body={'values': [[value]]}
        ).execute()

    return f"Updated {company_name}: {updates}"


def add_deal(deal_data):
    """Add a new deal to the pipeline."""
    sheets = get_sheets_service()

    # Build the row in column order
    row = []
    for field in ['company_name', 'contact_name', 'contact_email', 'contact_phone',
                  'project_description', 'date_entered', 'stage', 'stage_date',
                  'notes', 'estimated_mrr', 'priority', 'next_action_date',
                  'next_action', 'lost_reason']:
        row.append(deal_data.get(field, ''))

    sheets.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='A:N',
        valueInputOption='USER_ENTERED',
        body={'values': [row]}
    ).execute()

    return f"Added new deal: {deal_data.get('company_name')}"


def list_deals(stage=None):
    """List all deals, optionally filtered by stage."""
    deals = get_all_deals()

    if stage:
        deals = [d for d in deals if d.get('stage', '').lower() == stage.lower()]

    return deals


# Quick test
if __name__ == '__main__':
    print("Testing connection to your pipeline sheet...")
    print()

    deals = get_all_deals()

    if not deals:
        print("No deals found yet. Your pipeline is empty.")
        print("\nLet's add a test deal...")

        from datetime import date
        today = date.today().isoformat()

        result = add_deal({
            'company_name': 'Test Company',
            'contact_name': 'John Doe',
            'contact_email': 'john@test.com',
            'stage': 'Lead',
            'date_entered': today,
            'stage_date': today,
            'priority': 'Medium'
        })
        print(result)
    else:
        print(f"Found {len(deals)} deal(s) in your pipeline:")
        for deal in deals:
            print(f"  - {deal.get('company_name', 'Unknown')}: {deal.get('stage', 'No stage')}")
