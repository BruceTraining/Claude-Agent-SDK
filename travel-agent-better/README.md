# Flight Booking Agent — ClaudeSDKClient Version

> **✅ This is the correct approach.** After seeing the naive `query()` examples
> fail, this version shows how `ClaudeSDKClient` with a custom tool enables
> real multi-turn conversations for flight booking.

## What Changed (and What Didn't)

The system prompt is nearly identical to the naive version. The instructions
to Claude — "collect these five pieces of information, be friendly, don't
guess" — didn't change. **The prompt was never the problem.**

What changed is the architecture:

| Component | Naive Version | This Version |
|---|---|---|
| SDK function | `query()` — single-shot | `ClaudeSDKClient` — multi-turn |
| Conversation | One exchange, then dead | Persistent across messages |
| Tools | None | `search_flights` via `@tool` decorator |
| User experience | Dead end after first response | Natural back-and-forth dialogue |

## How It Works

### The Conversation Flow

```
User: "I want to fly to Paris"
Agent: "I'd love to help! Where will you be flying from?"

User: "Chicago"
Agent: "When would you like to travel?"

User: "Next Friday, back on Sunday"
Agent: "Do you have a seating preference — window, aisle, or middle?"

User: "Window. My name is Alex."
Agent: "Let me confirm: Alex, Chicago → Paris, departing June 13,
        returning June 15, window seat. Shall I search for flights?"

User: "Yes!"
Agent: [calls search_flights tool automatically]
Agent: "Here are 3 flights I found:
        Option 1: United UA 1234, 8:15 AM, $342
        Option 2: Delta DL 5678, 12:45 PM, $289
        Option 3: American AA 9012, 6:30 PM, $315"
```

The user provides information naturally, in any order, across as many messages
as they want. Claude tracks what's been collected and asks for what's missing.

### The Agent Loop

When Claude has all five pieces of information and the user confirms, Claude
calls the `search_flights` tool. Here's what happens inside the SDK:

1. Claude generates a `tool_use` response with the collected parameters
2. The SDK detects the `tool_use` stop reason
3. The SDK calls our `search_flights` function with the parameters
4. Our function returns simulated flight results
5. The SDK sends the results back to Claude as a `tool_result`
6. Claude formats the results into a friendly response
7. Claude generates an `end_turn` response
8. The SDK returns the final text to us

We don't write any of that loop logic. The SDK manages it entirely. We just
define the tool and collect the response.

### The Custom Tool

The `search_flights` tool is defined with three pieces:

```python
@tool(
    "search_flights",                    # Name Claude uses to call it
    "Search for available flights...",   # Description (helps Claude know WHEN to use it)
    {                                    # Input schema (Claude fills these from conversation)
        "passenger_name": str,
        "origin": str,
        "destination": str,
        "departure_date": str,
        "return_date": str,
        "seat_preference": str,
    }
)
async def search_flights(args: dict) -> dict:
    # Return simulated flight data
    ...
```

The `@tool` decorator + `create_sdk_mcp_server` registers this function as an
in-process MCP server. No subprocess, no external service — it runs in the
same Python process as the Flask app.

### Session Persistence (No Replay)

Since Flask handles each HTTP request independently, we can't keep a live
`ClaudeSDKClient` connection across requests. A naive fix would be to store the
full conversation history and *replay* it through the API on every request —
but that means redundant API calls and re-executed tool calls that grow with
every turn.

Instead, this version uses the SDK's built-in **session persistence**:

- A shared `InMemorySessionStore` mirrors each turn's transcript in memory.
- Each browser session maps to an SDK `session_id` (a UUID).
- On the next request we pass `resume=session_id` to `ClaudeAgentOptions`. The
  SDK loads the transcript from the store and spawns the CLI with
  `--resume <session_id>`, so the subprocess fast-loads the prior context.

No replay loop, no redundant API calls, no re-executed tools. See
[`HANDOFF.md`](HANDOFF.md) for the design rationale and the alternatives that
were considered.

`InMemorySessionStore` is perfect for demos but loses all data when the process
exits. For production you would implement the `SessionStore` protocol
(`append()` + `load()`) backed by a database, Redis, or the filesystem.

## Prerequisites

- **Python 3.10+**
- **uv** — Python package manager ([install uv](https://docs.astral.sh/uv/getting-started/installation/))
- **Anthropic API key** — Get one at [console.anthropic.com](https://console.anthropic.com/)

## Setup

### 1. Navigate to this project

```bash
cd travel-agent-better
```

### 2. Create your environment file

```bash
cp .env.example .env
```

Edit `.env` and replace `your-api-key-here` with your actual Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Install dependencies with uv

```bash
uv sync
```

## Running the Example

```bash
uv run python app.py
```

Open your browser to **http://localhost:8000** and start chatting.

Try providing your flight details one piece at a time to see the multi-turn
conversation in action. Then try giving everything at once to see Claude skip
straight to confirmation and searching.

## Project Structure

```
travel-agent-better/
├── .env.example      # Template for API key configuration
├── .gitignore        # Keeps .env and Python artifacts out of git
├── agent.py          # Agent logic — system prompt, search_flights tool,
│                     #   MCP server, and session-persistent conversation handler
├── app.py            # Flask app — routes, browser/SDK session mapping
├── pyproject.toml    # Project config and dependencies (used by uv)
├── HANDOFF.md        # Design notes on eliminating conversation replay
├── tutorial.md       # Comparative tutorial vs. the naive query() version
└── README.md         # This file
```

## Key Concepts Demonstrated

### 1. ClaudeSDKClient vs query()

`query()` creates a new session for each call — no memory, no continuity.
`ClaudeSDKClient` maintains a session where each `client.query()` call adds
to the ongoing conversation. Claude sees everything said before.

### 2. Custom Tools with @tool

The `@tool` decorator turns a Python function into something Claude can call.
The SDK runs it as an in-process MCP (Model Context Protocol) server. Claude
sees the tool's name, description, and parameter schema, and decides when to
invoke it based on the conversation.

### 3. The Agent Loop Is Invisible

When Claude calls `search_flights`, the SDK automatically executes the tool,
feeds the result back to Claude, and lets Claude generate the final response.
You don't write that loop — the SDK handles it. This is what makes the Agent
SDK more than just an API wrapper.

### 4. System Prompt Didn't Change

Compare the system prompt in this version to the naive version. They're nearly
identical. The prompt was always good — the delivery mechanism was the problem.
The right architecture (ClaudeSDKClient + tools) makes the same prompt work
the way it was intended to.

## What's Next

This example demonstrates the core pattern. To build a production flight
booking agent, you would:

- Replace the mock `search_flights` data with a real flight API
- Add a `book_flight` tool for completing the reservation
- Use WebSockets or SSE for real-time streaming responses
- Use Managed Agents for persistent server-side sessions
- Add authentication and user accounts
- Replace `InMemorySessionStore` with a `SessionStore` backed by a database,
  Redis, or the filesystem so conversations survive restarts and scale beyond
  a single process
