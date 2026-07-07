# Northstar Property Management — Glean Chatbot

Uses Glean **Indexing**, **Search**, and **Chat** APIs. One Python file per API + one MCP file.

```
config.py       # reads .env
indexing.py     # Indexing API
search.py       # Search API
chat.py         # Chat API (calls search, then chat)
mcp_server.py   # MCP tool
validate.py     # live Q&A validation
documents/      # policy docs to index
requirements.txt
mcp.json.example
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # fill in values below
```

Requires Python 3.10+.

## Environment variables

Copy `.env.example` to `.env` and fill in your Glean sandbox credentials.

### Required

| Variable | Description |
| --- | --- |
| `GLEAN_INDEXING_API_TOKEN` | Token for the Indexing API. Used by `indexing.py` to upload documents. |
| `GLEAN_SEARCH_API_TOKEN` | Token for the Search API. Used by `search.py` to find relevant snippets. |
| `GLEAN_CLIENT_API_TOKEN` | Token for the Client/Chat API. Used by `chat.py` to generate answers. |

## Run

Activate the venv first (`source .venv/bin/activate`), then:
```bash
# Index documents into Glean
python indexing.py
```

`indexing.py` reads the policy docs in `documents/` (using `glean_index_manifest.json`) and uploads them to your Glean datasource via the Indexing API. Run this once before searching or chatting.

```bash
# Ask a question
python chat.py "When is rent considered late?"
```

`chat.py` runs a question through the Search API first (to find relevant policy snippets), then the Chat API (to generate a grounded answer with sources). You can ask property management questions like *"What is the pet policy?"* or *"What will my rent be if I want to stay shorter than 12 months?"*

```bash
# MCP server (for Cursor / Claude Desktop)
python mcp_server.py
```

## Validation

After indexing, run `validate.py` to check that basic policy questions return expected facts from the docs (late fee, pet rent, lease premiums, maintenance SLAs):

```bash
python validate.py
```

Each case prints PASS/FAIL. Requires all three API tokens in `.env`. Expect ~1–2 minutes total (live Search + Chat per question).

## MCP setup (Claude Desktop)

Use this to ask Northstar Property Management policy questions directly in Claude via the `ask_glean_chatbot` tool.

1. **Index documents first** — run `python indexing.py` so Glean has the policy docs to search.

2. **Open Claude Developer settings** — in Claude Desktop, go to **Settings → Developer → Edit Config**. This opens `claude_desktop_config.json` (on Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`).

3. **Add the MCP server** — copy [`mcp.json.example`](mcp.json.example) into the `mcpServers` section and fill in your paths:

```json
{
  "mcpServers": {
    "Northstar PM Chatbot": {
      "command": "/path/to/repo/.venv/bin/python",
      "args": ["/path/to/repo/mcp_server.py"]
    }
  }
}
```

Replace both `/path/to/repo` with your clone path (e.g. `/Users/you/glean-property-management-example`). If you already have other MCP servers, add this entry alongside them — don't replace the whole file.

4. **Restart Claude Desktop** — quit and reopen the app.

5. **Test it** — start a new chat and ask Northstar Property Management policy questions, e.g.:
   - *"What is the pet policy at Northstar?"*
   - *"When is rent considered late?"*
   - *"What are the maintenance response times?"*

Claude should call `ask_glean` and return an answer with sources. Responses can take 15–45 seconds. Credentials load from `.env` automatically — no need to put tokens in the Claude config.
