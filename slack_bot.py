"""
Slack Bot - Natural language pipeline management from Slack.
"""

import os
import re
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from bot import chat

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Initialize Slack app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)


def clean_message(text):
    """Remove the bot mention from the message."""
    # Remove <@BOTID> mentions
    cleaned = re.sub(r'<@[A-Z0-9]+>', '', text).strip()
    return cleaned


@app.event("app_mention")
def handle_mention(event, say):
    """Handle when someone @mentions the bot."""
    user_message = clean_message(event.get("text", ""))

    if not user_message:
        say("How can I help with the pipeline? Try something like 'move Acme to Discovery'")
        return

    # Process through our pipeline bot
    response = chat(user_message)
    say(response)


@app.event("message")
def handle_dm(event, say):
    """Handle direct messages to the bot."""
    # Only respond to DMs (not channel messages without mention)
    if event.get("channel_type") != "im":
        return

    # Ignore bot's own messages
    if event.get("bot_id"):
        return

    user_message = event.get("text", "").strip()

    if not user_message:
        return

    # Process through our pipeline bot
    response = chat(user_message)
    say(response)


if __name__ == "__main__":
    print("Pipeline Bot is running!")
    print("You can @mention the bot in any channel or DM it directly.")
    print("Press Ctrl+C to stop.")
    print()

    # For local development, we need Socket Mode
    # First check if we have an app-level token
    app_token = os.environ.get("SLACK_APP_TOKEN")

    if app_token:
        handler = SocketModeHandler(app, app_token)
        handler.start()
    else:
        print("ERROR: SLACK_APP_TOKEN not found.")
        print()
        print("To run locally, you need Socket Mode enabled:")
        print("1. Go to api.slack.com/apps > Your App > Socket Mode")
        print("2. Enable Socket Mode")
        print("3. Generate an App-Level Token with 'connections:write' scope")
        print("4. Add SLACK_APP_TOKEN=xapp-... to your .env file")
