"""
travel-agent-better/app.py
==========================
Flask web interface for the multi-turn flight booking agent.

    We use the SDK's built-in session persistence:
    - A shared InMemorySessionStore mirrors each turn's transcript in memory.
    - Each browser session maps to an SDK session_id (a UUID).
    - On subsequent requests, we pass `resume=session_id` to the SDK, which
      fast-loads the transcript from the store

USAGE:
    uv run python app.py
    Then open http://localhost:8000 in your browser.
"""

import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, request, session, redirect

# Import the agent function and the shared session store class.
# InMemorySessionStore is the SDK's built-in in-memory implementation
# of the SessionStore protocol — it stores transcript entries in a
# Python dict, perfect for demos.
from claude_agent_sdk import InMemorySessionStore
from agent import get_agent_response


#
# Load environment variables from .env file.
#
load_dotenv(Path(__file__).parent / ".env")

if not os.getenv("ANTHROPIC_API_KEY"):
    print("ERROR: ANTHROPIC_API_KEY not found.")
    print("Copy .env.example to .env and add your Anthropic API key.")
    print("Get a key at: https://console.anthropic.com/")
    raise SystemExit(1)

#
# Set the HTTP port
#
HTTP_PORT = 8000

#
# Create the Flask web application
#
app = Flask(__name__)
app.secret_key = os.urandom(24)

# ===========================================================================
# SESSION STORAGE 
# ===========================================================================
#
#   session_store: A shared InMemorySessionStore that the SDK mirrors
#     transcript entries to after each turn. On resume, the SDK reads
#     from this store to reconstruct the conversation
#
#   sdk_session_ids: Maps browser session ID → SDK session ID (UUID).
#     The browser session ID is a Flask cookie; the SDK session ID is what
#     the Claude CLI subprocess uses internally. We need this mapping so
#     we can tell the SDK which session to resume on the next request.
#
#   display_history: Maps browser session ID → list of (user, assistant)
#     text pairs for rendering in the HTML page. The SDK session store
#     holds the full transcript in an internal format — we keep a simple
#     parallel list of the display text so the HTML template can show
#     the latest exchange without parsing the SDK's internal format.
# ===========================================================================
session_store = InMemorySessionStore()
sdk_session_ids: dict[str, str] = {}
display_history: dict[str, list[dict]] = {}


def get_session_id() -> str:
    """
    Get or create a unique session ID for this browser session.

    Flask's session object is a signed cookie. We store a UUID in it
    so we can look up the SDK session ID and display history for this user.
    """
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]


#
# Create a Route/Endpoint for the home page
#
# GET: displays a plain HTML form
# POST: Sends the message to Claude, renders the response.
#
@app.route("/", methods=["GET"])
def home():
    """
    Display the conversation page.

    On first visit: shows a welcome message and the input form.
    On return visits: shows the latest exchange and the input form.
    """
    browser_session_id = get_session_id()
    history = display_history.get(browser_session_id, [])

    # Show only the latest user input and agent response
    conversation_html = ""
    if len(history) >= 2:
        user_entry = history[-2]
        agent_entry = history[-1]
        conversation_html = f"""
        <p><b>You:</b></p>
        <pre style="white-space: pre-wrap;">{user_entry['text']}</pre>
        <hr>
        <p><b>Agent:</b></p>
        <pre style="white-space: pre-wrap;">{agent_entry['text']}</pre>
        <hr>
        """

    return f"""
    <h2>Flight Booking Agent (ClaudeSDKClient + Custom Tools)</h2>
    <p>This agent uses ClaudeSDKClient for multi-turn conversations
       and a custom search_flights tool. Talk naturally — provide your
       flight details in any order, across as many messages as you like.</p>
    <hr>

    {conversation_html}

    <form method="POST" action="/booktravel">
        <input type="text" name="message"
               placeholder="e.g. I want to fly to Paris"
               size="60"
               autofocus>
        <button type="submit">Send</button>
    </form>

    <br>
    <a href="/reset">Start a new conversation</a>
    """


#
# Handle a new message from the user.
#
@app.route("/booktravel", methods=["POST"])
def booktravel():
    """
    Process a new user message and get Claude's response.

    This is where the session persistence magic happens:
    1. Look up the SDK session_id for this browser session (if any).
    2. Call get_agent_response() with the session_id and session_store.
    3. The agent either starts a new session or resumes the existing one.
    4. Save the returned session_id for next time.
    """
    browser_session_id = get_session_id()
    user_message = request.form.get("message", "").strip()

    if not user_message:
        return '<p>No message entered.</p><p><a href="/">Go back</a></p>'

    # ------------------------------------------------------------------
    # LOOK UP THE SDK SESSION ID
    #
    # On the first request for this browser session, there's no SDK
    # session_id yet — we pass None, and the SDK auto-generates one.
    # On subsequent requests, we pass the stored session_id so the SDK
    # can resume the conversation.
    # ------------------------------------------------------------------
    sdk_session_id = sdk_session_ids.get(browser_session_id)

    # ------------------------------------------------------------------
    # CALL THE AGENT
    #
    # get_agent_response() handles all the SDK logic:
    # - If sdk_session_id is None: starts a new conversation
    # - If sdk_session_id is set: passes `resume=sdk_session_id` so
    #   the CLI fast-loads the transcript from the session_store
    #
    # It returns both the response text and the session_id (which may
    # be newly generated on the first call).
    # ------------------------------------------------------------------
    claude_response, returned_session_id = get_agent_response(
        session_id=sdk_session_id,
        new_message=user_message,
        session_store=session_store,
    )

    # ------------------------------------------------------------------
    # SAVE STATE FOR NEXT REQUEST
    #
    # 1. Store the SDK session_id so we can resume next time.
    # 2. Append to display_history so the HTML page can show the exchange.
    #
    # Note: There is no need to store the full conversation history ourselves —
    # the InMemorySessionStore handles that internally. We only keep the
    # display text for rendering the HTML.
    # ------------------------------------------------------------------
    sdk_session_ids[browser_session_id] = returned_session_id

    if browser_session_id not in display_history:
        display_history[browser_session_id] = []
    display_history[browser_session_id].append({"role": "user", "text": user_message})
    display_history[browser_session_id].append({"role": "assistant", "text": claude_response})

    # Redirect to home page to show updated conversation
    # (POST-Redirect-GET pattern to prevent form resubmission)
    return redirect("/")


@app.route("/reset")
def reset():
    """
    Clear the conversation history and start fresh.

    This discards the current session's conversation data:
    - The SDK session_id mapping
    - The display history for the HTML page
    - The Flask session cookie (forces a new browser session)

    Note: The InMemorySessionStore still holds the old transcript data,
    but it becomes orphaned (no browser session points to it). In a
    production app you'd want to clean that up; for a demo it's fine.
    """
    browser_session_id = get_session_id()

    # Clean up our session mappings
    sdk_session_ids.pop(browser_session_id, None)
    display_history.pop(browser_session_id, None)

    # Clear the Flask session to get a fresh browser session_id
    session.clear()
    return redirect("/")


#
# Run the Flask server
#
if __name__ == "__main__":
    app.run(port=HTTP_PORT)

