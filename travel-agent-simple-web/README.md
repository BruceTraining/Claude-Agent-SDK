# Flight Booking Agent — Simple Web Version

> **Note:** This example uses `query()` — a single-shot API call with no
> conversation memory. Each message you send starts a fresh conversation.
> Claude can respond, but it cannot remember what you said before.

## What This Example Teaches

This is the simplest way to put a Claude agent behind a web form. It shows
how `query()` works and where it falls short: Claude asks follow-up questions
(name, origin, dates), but the next message you send doesn't carry any of that
context. Every submission is a clean slate.

The limitation isn't the UI — there's always a form to type into. The limitation
is that `query()` doesn't maintain conversation state. The next example
(`travel-agent-better`) solves this with `ClaudeSDKClient` and session
persistence.

## Try It

### The Unlikely Case (Everything in One Message)

```
My name is Jordan, flying from Chicago to Tokyo on July 10th, window seat.
```

Claude confirms the details. It works because all five required fields arrived
in a single prompt.

### The Likely Case (Partial Information)

```
I want to fly to Paris
```

Claude responds with follow-up questions. You can type an answer, but Claude
won't remember the original request — it treats every message independently.

## Prerequisites

- **Python 3.10+**
- **uv** — Python package manager ([install uv](https://docs.astral.sh/uv/getting-started/installation/))
- **Anthropic API key** — Get one at [console.anthropic.com](https://console.anthropic.com/)

## Setup

### 1. Navigate to this project

```bash
cd travel-agent-simple-web
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

This installs the Claude Agent SDK, Flask, and python-dotenv.

## Running the Example

```bash
uv run python app.py
```

Then open your browser to **http://localhost:8000**.

## Project Structure

```
travel-agent-simple-web/
├── .env.example      # Template for API key configuration
├── .gitignore        # Keeps .env and Python artifacts out of git
├── agent.py          # Agent logic — system prompt, query() call
├── app.py            # Flask app — single route, inline HTML
├── pyproject.toml    # Project config and dependencies (used by uv)
├── uv.lock           # Locked dependency versions
└── README.md         # This file
```

## How the Code Works

The application is split across two files:

- **`agent.py`** — Defines the system prompt and wraps the SDK's `query()`
  function. Uses `claude-haiku-4-5` for fast responses.
- **`app.py`** — A Flask app with one route (`/`). On GET it shows an intro
  and input form. On POST it sends the message to `get_claude_response()` and
  displays the result above the same form.

There are no templates, no static files, no CSS, and no JavaScript. The HTML
is returned as an inline f-string. This is intentional — the code should be
readable in under a minute.

## What's Next

The next example (`travel-agent-better`) replaces `query()` with
`ClaudeSDKClient` and adds session persistence so conversations span multiple
turns. It also adds a custom `search_flights` tool. The system prompt stays
nearly identical — proving that the prompt was never the problem. The
architecture was.
