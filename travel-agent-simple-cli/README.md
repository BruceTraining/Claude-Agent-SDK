# travel-agent-simple-cli — Naive Single-Shot Approach

> **⚠️ This example is intentionally broken.** It demonstrates *why* a single-shot
> `query()` approach fails for conversational tasks like flight booking. 


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
cd travel-agent-simple-cli
```

### 2. Create your environment file

```bash
cp .env.example .env
```

Create `.env` and add  your actual Anthropic API key:

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
