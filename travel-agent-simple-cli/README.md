# Flight Booking Agent — Naive Single-Shot Approach

> **⚠️ This example is intentionally broken.** It demonstrates *why* a single-shot
> `query()` approach fails for conversational tasks like flight booking. After
> running it, proceed to the improved version that uses `ClaudeSDKClient` for
> real multi-turn conversations.

## What This Example Teaches

When building an AI agent that needs to collect information from a user, you
might reach for the simplest tool available — the `query()` function from the
Claude Agent SDK. It sends one prompt, gets one response, and you're done.

For some tasks, that's perfect. "Summarize this document." "Convert this code
from Python to Rust." One input, one output.

But flight booking isn't that kind of task. A real user doesn't type:

```
My name is Jordan Smith, I want to fly from New York JFK to Los Angeles LAX
on June 15th 2025, returning June 22nd, and I'd like a window seat please.
```

A real user types:

```
I want to fly to Paris
```

And then expects the agent to *ask follow-up questions* — and actually *listen*
to the answers. That requires a **conversation loop**, which `query()` simply
cannot do.

## The Two Runs

Run this example **twice** to see both sides:

### Run 1: The Unlikely Case (Everything in One Message)

```
You: My name is Jordan, flying from Chicago to Tokyo on July 10th, window seat.
```

Claude will confirm the details and offer to search. This works — but only
because the user happened to provide everything upfront. In practice, almost
no one talks to a booking agent this way.

### Run 2: The Likely Case (Partial Information)

```
You: I want to fly to Paris
```

Claude will respond with something like: *"I'd love to help you book a flight
to Paris! I just need a few more details. What city will you be departing
from?"*

And then... the program exits. The user **cannot answer**. The conversation
is over. The booking fails.

**This is the core lesson:** `query()` gives you exactly one exchange — one
user message, one assistant response. For any task that requires back-and-forth
dialogue, you need `ClaudeSDKClient` instead.

## Prerequisites

- **Python 3.10+**
- **uv** — Python package manager ([install uv](https://docs.astral.sh/uv/getting-started/installation/))
- **Anthropic API key** — Get one at [console.anthropic.com](https://console.anthropic.com/)

## Setup

### 1. Clone or navigate to this project

```bash
cd flight-agent-naive
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

This creates a virtual environment and installs the Claude Agent SDK and
python-dotenv.

## Running the Example

```bash
uv run python main.py
```

You'll see a prompt asking for your flight request. Try it twice — once with
complete information, once with partial information — to experience the
limitation firsthand.

## Project Structure

```
travel-agent-simple-cli/
├── .env.example      # Template for API key configuration
├── .gitignore         # Keeps .env and Python artifacts out of git
├── main.py            # The naive agent — heavily commented to explain the failure
├── pyproject.toml     # Project config and dependencies (used by uv)
└── README.md          # This file
```

## Understanding the Code

The code in `main.py` is thoroughly documented with inline comments that
explain not just *what* the code does, but *why it fails*. Key sections:

1. **System Prompt** — A well-written prompt that instructs Claude to collect
   five pieces of information. The prompt itself is good; the delivery
   mechanism is the problem.

2. **query() Call** — The single-shot function that sends one prompt and
   receives one response. This is where the architectural limitation lives.

3. **Exit Message** — After Claude responds, the program prints a clear
   message explaining that the conversation cannot continue.

## What's Next

The next example in this series replaces `query()` with `ClaudeSDKClient`,
which enables:

- **Multi-turn conversations** — The user and Claude go back and forth naturally
- **Custom tools** — A `search_flights` tool that Claude calls once all info is collected
- **Persistent conversation state** — Claude remembers everything said so far

The system prompt stays almost identical — proving that the prompt wasn't the
problem. The architecture was.

## Key Takeaway

| Approach | Best For | Limitation |
|---|---|---|
| `query()` | Single-shot tasks (summarize, convert, analyze) | No conversation — one prompt, one response |
| `ClaudeSDKClient` | Multi-turn interactions (booking, support, interviews) | Requires more setup, but supports real dialogue |

Choose the right tool for the job. When your agent needs to have a
**conversation**, reach for `ClaudeSDKClient`.
