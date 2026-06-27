"""
travel-agent-better/agent.py
============================
Flight booking agent logic: system prompt, custom tool, MCP server,
and the multi-turn conversation handler.

This module contains all the Claude Agent SDK logic, separated from
the Flask web layer (app.py) so it can be used independently.

KEY CONCEPT — Session Persistence 
    We use the SDK's built-in session persistence.
    The SDK mirrors each turn's transcript to an InMemorySessionStore, and
    on the next request we pass `resume=session_id` so the Claude Agent SDK 
    fast-loads the transcript from the store.
"""

import asyncio
import uuid

from claude_agent_sdk import (
    tool,
    create_sdk_mcp_server,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    AssistantMessage,
    TextBlock,
    # InMemorySessionStore is an in-memory dict-backed implementation of the
    # SessionStore protocol. It stores transcript entries in a Python dict,
    # keyed by project_key/session_id. Perfect for demos — but data is lost
    # when the process exits. For production, you'd implement SessionStore
    # backed by a database or file system.
    InMemorySessionStore,
)


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

1. Passenger name — The full name of the person traveling.
2. Origin — The city or airport the user is departing from.
3. Destination — The city or airport the user wants to fly to.
4. Travel dates — The departure date (and return date if round-trip).
5. Seating preference — Window, aisle, or middle seat.

RULES:
- Be conversational and natural. Greet the user warmly.
- If the user provides some but not all of the required information, ask
  follow-up questions for the missing details. Do NOT guess or assume.
- You may collect information in ANY order. The user might volunteer some
  details upfront — acknowledge what they've given and ask for what's missing.
- Once you have ALL five pieces of information, confirm the details back
  to the user. If they confirm, call the search_flights tool to find flights.
- If the user wants to change any detail, update it and re-confirm.
- After receiving flight results, present them clearly and ask if the user
  wants to book one of the options.
- Keep responses concise but friendly and don't use emojii
"""



# ===========================================================================
# CUSTOM TOOL: search_flights
# ===========================================================================
# This is the tool that Claude will call once it has collected all five
# required pieces of information from the user.
#
@tool(
    "search_flights",
    """Search for available flights. Call this tool ONLY after collecting all
    required booking information: passenger name, origin city/airport,
    destination city/airport, travel date(s), and seating preference.""",
    {
        "passenger_name": str,
        "origin": str,
        "destination": str,
        "departure_date": str,
        "return_date": str,
        "seat_preference": str,
    }
)
async def search_flights(args: dict) -> dict:
    """
    Simulate a flight search and return mock results.

    In a real application, this function would:
    - Validate the input parameters
    - Call an external flight search API (Amadeus, Sabre, Skyscanner, etc.)
    - Parse and format the results
    - Handle errors (no flights found, API timeout, etc.)

    For this educational example, we return hardcoded flight options to
    demonstrate the tool execution flow without needing API credentials.

    Args:
        args: Dictionary containing passenger_name, origin, destination,
              departure_date, return_date, and seat_preference.

    Returns:
        MCP-formatted response with flight search results as text content.
    """

    #
    # Extract the booking details that Claude collected from the user.
    # These were populated by Claude from the natural language conversation.
    #
    name = args.get("passenger_name", "Unknown")
    origin = args.get("origin", "Unknown")
    destination = args.get("destination", "Unknown")
    departure = args.get("departure_date", "Unknown")
    return_date = args.get("return_date", "Not specified")
    seat = args.get("seat_preference", "No preference")

    # ------------------------------------------------------------------
    # Build simulated flight results.
    #
    # In a production system, this is where you'd make your API call:
    #   results = await flight_api.search(origin, destination, departure, ...)
    #
    # The mock data below shows what a real response might look like.
    # ------------------------------------------------------------------
    flights = [
        {
            "airline": "United Airlines",
            "flight_number": "UA 1234",
            "departure_time": "08:15 AM",
            "arrival_time": "11:30 AM",
            "duration": "3h 15m",
            "price": "$342",
            "seat_available": seat,
        },
        {
            "airline": "Delta Air Lines",
            "flight_number": "DL 5678",
            "departure_time": "12:45 PM",
            "arrival_time": "04:00 PM",
            "duration": "3h 15m",
            "price": "$289",
            "seat_available": seat,
        },
        {
            "airline": "American Airlines",
            "flight_number": "AA 9012",
            "departure_time": "06:30 PM",
            "arrival_time": "09:45 PM",
            "duration": "3h 15m",
            "price": "$315",
            "seat_available": seat,
        },
    ]

    # ------------------------------------------------------------------
    # Format the results as a text string.
    #
    # The MCP tool response format requires a "content" list with typed
    # blocks. Here we use a single "text" block containing the formatted
    # flight data. Claude will receive this text and present it to the
    # user in a conversational way.
    # ------------------------------------------------------------------
    result_text = f"Flight search results for {name}:\n"
    result_text += f"Route: {origin} → {destination}\n"
    result_text += f"Departure: {departure}\n"
    if return_date and return_date != "Not specified":
        result_text += f"Return: {return_date}\n"
    result_text += f"Seat preference: {seat}\n"
    result_text += "-" * 40 + "\n\n"

    for i, flight in enumerate(flights, 1):
        result_text += f"Option {i}: {flight['airline']}\n"
        result_text += f"  Flight: {flight['flight_number']}\n"
        result_text += f"  Departs: {flight['departure_time']}\n"
        result_text += f"  Arrives: {flight['arrival_time']}\n"
        result_text += f"  Duration: {flight['duration']}\n"
        result_text += f"  Price: {flight['price']}\n"
        result_text += f"  {seat} seat: Available\n\n"

    return {
        "content": [
            {"type": "text", "text": result_text}
        ]
    }


# ===========================================================================
# MCP SERVER SETUP
# ===========================================================================
# Bundle our custom tool into an MCP server. The ClaudeSDKClient will
# connect to this server and make the search_flights tool available to
# Claude during the conversation.
#
# Think of this as "registering" our tool with the agent. Claude will see
# the tool's name, description, and input schema, and can decide when to
# call it based on the conversation context.
# ===========================================================================
mcp_server = create_sdk_mcp_server(
    name="flight-tools",
    version="1.0.0",
    tools=[search_flights]
)


def get_agent_response(
    session_id: str | None,
    new_message: str,
    session_store: InMemorySessionStore,
) -> tuple[str, str]:
    """
    Send a message to Claude and get the response, using SDK session
    persistence to maintain conversation context across HTTP requests.

    HOW SESSION PERSISTENCE WORKS:
        1. First request (session_id is None):
           - We create a new ClaudeSDKClient with a fresh session_id.
           - The SDK mirrors the transcript to session_store via append().
           - We return the session_id so app.py can save it for next time.

        2. Subsequent requests (session_id is a UUID string):
           - We pass `resume=session_id` to ClaudeAgentOptions.
           - The SDK calls session_store.load() to get the prior transcript.
           - It writes that transcript to a temp file and spawns the CLI
             with `--resume <session_id>`, so the subprocess picks up
             where it left off.
           - No replay loop needed! The CLI fast-loads the transcript.

    THE AGENT LOOP HAPPENS HERE:
        When Claude decides to call search_flights, the SDK automatically:
        1. Executes the tool function
        2. Sends the result back to Claude
        3. Claude processes the result and generates a text response
        All of this happens inside the receive_response() loop — we don't
        need to write any of that logic ourselves.

    Args:
        session_id: The SDK session ID from a previous request, or None
                    if this is the first message in the conversation.
        new_message: The user's new message to send.
        session_store: The shared InMemorySessionStore instance that
                       mirrors transcript data across requests.

    Returns:
        A tuple of (response_text, session_id):
        - response_text: Claude's text response as a string.
        - session_id: The session ID to pass back on the next request.
                      On first call this is a new UUID; on subsequent
                      calls it's the same one passed in.
    """

    async def _run() -> tuple[str, str]:
        # =================================================================
        # BUILD OPTIONS
        # =================================================================
        # Start with the options that are the same for every request:
        # system prompt, MCP server, tool permissions, and session store.
        # =================================================================
        options = ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT,
            model=MODEL,

            # Connect our custom MCP server with the search_flights tool.
            # The key "flight-tools" matches the name we gave the server.
            mcp_servers={"flight-tools": mcp_server},

            # Pre-approve the search_flights tool so Claude can call it
            # without a permission prompt. The tool name follows the
            # pattern: mcp__<server-name>__<tool-name>
            allowed_tools=["mcp__flight-tools__search_flights"],

            # Disable built-in tools — we only want our custom tool.
            disallowed_tools=["Read", "Write", "Edit", "Bash", "Glob",
                              "Grep"],

            # ----------------------------------------------------------
            # SESSION PERSISTENCE 
            #
            # session_store: The InMemorySessionStore that the SDK will
            #   mirror transcript entries to after each turn. On resume,
            #   the SDK calls store.load() to get the prior transcript.
            #
            # session_store_flush="eager": Flush transcript entries to
            #   the store immediately after each frame, rather than
            #   batching them. This ensures the store is always up to
            #   date when the next HTTP request arrives. For a demo with
            #   one user, the overhead is negligible.
            # ----------------------------------------------------------
            session_store=session_store,
            session_store_flush="eager",
        )

        # =================================================================
        # RESUME vs. NEW SESSION
        # =================================================================
        # If we have a session_id from a prior request, tell the SDK to
        # resume that session. The SDK will:
        #   1. Call session_store.load() to get the transcript entries
        #   2. Write them to a temp JSONL file
        #   3. Spawn the CLI with --resume, so it picks up where it left off
        #
        # If session_id is None, this is a brand-new conversation. We
        # generate a UUID ourselves and pass it via options.session_id so
        # we know the ID to resume with on the next request.
        #
        # Why generate it ourselves? ClaudeSDKClient doesn't expose its
        # internal session_id as a public attribute. By setting it
        # explicitly, we control the ID and can return it to app.py.
        # =================================================================
        if session_id is not None:
            # Resume an existing conversation. The CLI subprocess will
            # fast-load the transcript from the session store instead of
            # replaying through the API.
            options.resume = session_id
            current_session_id = session_id
        else:
            # First request — generate a new UUID and tell the SDK to use
            # it as this session's ID. This way we know the ID without
            # needing to read it back from the claude_sdk_client
            current_session_id = str(uuid.uuid4())
            options.session_id = current_session_id

        # =================================================================
        # RUN THE AGENT LOOP
        # =================================================================
        async with ClaudeSDKClient(options=options) as claude_sdk_client:

            # ---------------------------------------------------------------
            # SEND THE USER'S MESSAGE
            #
            # No replay loop needed! If we passed `resume`, the CLI already
            # has the full conversation context. We just send the new message.
            #
            # Claude processes it in context and either:
            #   a) Asks a follow-up question (missing info)
            #   b) Confirms details and calls search_flights
            #   c) Presents flight results after tool execution
            # ---------------------------------------------------------------
            await claude_sdk_client.query(new_message)

            # ---------------------------------------------------------------
            # COLLECT CLAUDE'S RESPONSE
            #
            # receive_response() yields messages until Claude's turn is
            # complete. If Claude calls search_flights during this turn,
            # the SDK handles the tool execution internally:
            #
            #   Claude says "Let me search..." → tool_use stop_reason
            #   → SDK calls search_flights() → gets mock results
            #   → SDK sends results back to Claude → Claude formats them
            #   → Claude says "Here are your flights..." → end_turn
            #
            # We just collect the final text output. The agent loop is
            # invisible to us — the SDK manages it all.
            # ---------------------------------------------------------------
            response_parts = []
            async for message in claude_sdk_client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_parts.append(block.text)

            response_text = "\n".join(response_parts) if response_parts else "I didn't get a response. Please try again."
            return response_text, current_session_id

    return asyncio.run(_run())
