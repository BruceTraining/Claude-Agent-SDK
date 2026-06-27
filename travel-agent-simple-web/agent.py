"""
travel-agent-simple-web/agent.py
================================
Flight booking agent logic using the Claude Agent SDK.
Separated from the Flask web layer so it can be used independently.
"""

import asyncio

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


#
# Send the message to Claude via query()
#
def get_claude_response(user_message: str) -> str:
    """
    Send a single message to Claude via query() and return the text response.

    Args:
        user_message: The user's flight request.

    Returns:
        Claude's text response as a string.
    """

    async def run_query():
        options = ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT,
            model=MODEL,
            max_turns=3,
            disallowed_tools=["Read", "Write", "Edit", "Bash", "Glob",
                              "Grep"],
        )

        # Collect all text blocks from Claude's response.
        response_parts = []

        async for message in query(prompt=user_message, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)

        return "\n".join(response_parts)

    return asyncio.run(run_query())
