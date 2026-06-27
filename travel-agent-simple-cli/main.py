"""
travel-agent-simple/main.py
==========================
A Simple CLI flight booking agent using the Claude Agent SDK's query() function.

USAGE:
    uv run python main.py
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

# ---------------------------------------------------------------------------
#
# We use two things from the Claude Agent SDK:
#   - query():             A function that sends a single prompt to Claude
#                          and streams back the response. This is the
#                          SIMPLEST way to interact with Claude through the
#                          SDK — and also the most limited.
#
#   - ClaudeAgentOptions:  Configuration object that lets us set the system
#                          prompt, control which tools Claude can use, and
#                          tune other behavior.
# ---------------------------------------------------------------------------

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
# Set the model
#
MODEL = "claude-haiku-4-5-20251001"

# 
# Provide the system prompt
# 
SYSTEM_PROMPT = """You are a friendly and professional flight booking assistant.

Your job is to collect all of the following information from the user before
searching for flights:

1. Passenger name: The full name of the person traveling.
2. Origin: The city or airport the user is departing from.
3. Destination: The city or airport the user wants to fly to.
4. Travel dates: The departure date (and return date if round-trip).
5. Seating preference: Window, aisle, or middle seat.

RULES:
- Be conversational and natural. Greet the user warmly.
- If the user provides some but not all of the required information, ask
  follow-up questions for the missing details. Do NOT guess or assume.
- Once you have ALL five pieces of information, confirm the details back
  to the user and let them know you will search for available flights.
- If the user is unclear or ambiguous, ask for clarification.
- Keep responses concise but friendly and don't use emojii
"""


def main():

    print("=" * 60)
    print("  FLIGHT BOOKING AGENT")
    print("=" * 60)
    print()
    print("""Please provide your:
1. Passenger name: The full name of the person traveling.
2. Origin: The city or airport the user is departing from.
3. Destination: The city or airport the user wants to fly to.
4. Travel dates: The departure date (and return date if round-trip).
5. Seating preference: Window, aisle, or middle seat.
          """)
    print()

    # -----------------------------------------------------------------------
    # Step 1: Collect the user's message.
    # -----------------------------------------------------------------------
    user_message = input("Type here: ").strip()

    if not user_message:
        print("No message entered. Exiting.")
        return

    print()
    print("Processing your request...")
    print()

    # -----------------------------------------------------------------------
    # Step 2: Send the message to Claude via query().
    #
    # query() is an async generator that yields response messages from Claude.
    # We configure it with:
    #   - prompt:  The user's single message.
    #   - options: Our system prompt and tool restrictions.
    # -----------------------------------------------------------------------
    async def run_query():
        options = ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT,
            model=MODEL,
            max_turns=3,
            disallowed_tools=["Read", "Write", "Edit", "Bash", "Glob",
                              "Grep"],
        )

        # -------------------------------------------------------------------
        # Stream and print Claude's response.
        #
        # NOTE: The query() function yields different message types. We look for
        # AssistantMessage objects and extract their TextBlock content.
        #
        # -------------------------------------------------------------------
        async for message in query(prompt=user_message, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Agent: {block.text}")

    # -----------------------------------------------------------------------
    # Step 3: Run the async query.
    # -----------------------------------------------------------------------
    asyncio.run(run_query())

    # -----------------------------------------------------------------------
    # Step 4: This is the end of the conversation.
    # -----------------------------------------------------------------------
    print()
    print("=" * 60)
    print("  Thanks for booking your flight with us!")
    print()



# ---------------------------------------------------------------------------
# Standard Python entry point.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
