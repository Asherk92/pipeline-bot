"""
Pipeline Bot - Natural language interface to your sales pipeline.
"""

import os
import json
from datetime import date
from dotenv import load_dotenv
from anthropic import Anthropic
from pipeline import get_all_deals, find_deal, update_deal, add_deal, list_deals, STAGES

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Initialize Claude
client = Anthropic()

SYSTEM_PROMPT = """You are a sales pipeline assistant. You help manage deals in a sales pipeline.

The pipeline has these stages (in order): Lead → Discovery → Build POC → Proposal → Negotiation → Won/Lost

Each deal has these fields:
- company_name, contact_name, contact_email, contact_phone
- project_description
- date_entered, stage, stage_date
- notes
- estimated_mrr (monthly recurring revenue)
- priority (High/Medium/Low)
- next_action_date, next_action
- lost_reason (only if Lost)

Based on the user's message, determine what action to take and respond with JSON:

For updating a deal:
{"action": "update", "company": "company name", "updates": {"field": "value", ...}}

For adding a new deal:
{"action": "add", "deal": {"company_name": "...", "stage": "Lead", ...}}

For listing deals:
{"action": "list", "filter_stage": null}  (or specify a stage)

For questions or unclear requests:
{"action": "clarify", "message": "your question"}

Always update stage_date to today when changing the stage.
Today's date is: """ + date.today().isoformat() + """

IMPORTANT: Respond ONLY with the JSON object, no other text."""


def process_command(user_message, current_deals):
    """Send a command to Claude and get structured response."""

    # Build context about current deals
    deals_context = "Current deals in pipeline:\n"
    if current_deals:
        for deal in current_deals:
            deals_context += f"- {deal.get('company_name', 'Unknown')}: {deal.get('stage', 'No stage')}\n"
    else:
        deals_context = "Pipeline is currently empty.\n"

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"{deals_context}\n\nUser request: {user_message}"}
        ]
    )

    # Parse the JSON response
    response_text = response.content[0].text.strip()

    # Handle potential markdown code blocks
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]

    return json.loads(response_text)


def execute_action(action_data):
    """Execute the action determined by Claude."""

    action = action_data.get("action")

    if action == "update":
        company = action_data.get("company")
        updates = action_data.get("updates", {})
        return update_deal(company, updates)

    elif action == "add":
        deal_data = action_data.get("deal", {})
        # Set defaults
        today = date.today().isoformat()
        deal_data.setdefault("date_entered", today)
        deal_data.setdefault("stage_date", today)
        deal_data.setdefault("stage", "Lead")
        return add_deal(deal_data)

    elif action == "list":
        filter_stage = action_data.get("filter_stage")
        deals = list_deals(filter_stage)
        if not deals:
            return "No deals found."

        result = f"Found {len(deals)} deal(s):\n"
        for deal in deals:
            result += f"  • {deal.get('company_name')}: {deal.get('stage')}"
            if deal.get('next_action'):
                result += f" (Next: {deal.get('next_action')})"
            result += "\n"
        return result

    elif action == "clarify":
        return f"Question: {action_data.get('message')}"

    else:
        return f"Unknown action: {action}"


def chat(user_message):
    """Process a natural language message and update the pipeline."""

    # Get current deals for context
    current_deals = get_all_deals()

    # Get action from Claude
    try:
        action_data = process_command(user_message, current_deals)
        result = execute_action(action_data)
        return result
    except json.JSONDecodeError as e:
        return f"Error parsing response: {e}"
    except Exception as e:
        return f"Error: {e}"


# Interactive mode
if __name__ == "__main__":
    print("Pipeline Bot ready! Type your commands (or 'quit' to exit)")
    print("Examples:")
    print("  - 'Add Acme Corp as a new lead'")
    print("  - 'Move Acme to Discovery'")
    print("  - 'Acme signed the contract'")
    print("  - 'Show all deals'")
    print()

    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            if not user_input:
                continue

            response = chat(user_input)
            print(f"Bot: {response}")
            print()
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
