"""
travel-agent-simple-web/app.py
=============================
Flask web interface for the flight booking agent.

USAGE:
    uv run python app.py
    Then open http://localhost:8000 in your browser.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, request

from agent import get_claude_response


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


#
# Create a Route/Endpoint for the home page
#
# GET: displays a plain HTML form
# POST: Sends the message to Claude, renders the response.
#
@app.route("/", methods=["GET", "POST"])
def home():

    #
    # GET - show intro text 
    # POST - show Claude's response.
    #
    content_html = ""
    if request.method == "POST":
        user_message = request.form.get("message", "").strip()
        if not user_message:
            return '<p>No message entered.</p><p><a href="/">Try again</a></p>'
        claude_response = get_claude_response(user_message)
        content_html = f'<pre style="white-space: pre-wrap;">{claude_response}</pre>'
    else:
        content_html = """
        <p>This demo uses query() — a single prompt, single response.</p>
        <p>Type your flight request below and click Send.</p>
        """

    return f"""
    <h2>Flight Booking Agent</h2>

    {content_html}

    <form method="POST">
        <input type="text" name="message"
               placeholder="e.g. I want to fly to Paris"
               size="60"
               autofocus>
        <button type="submit">Send</button>
    </form>
    """


#
# Run the Flask server
#
if __name__ == "__main__":
    app.run(port=HTTP_PORT)
