---
name: heptabase
description: >
  Interact with a user's Heptabase knowledge base — save notes, search content,
  read cards/whiteboards/journals, and work with PDFs. Use this skill whenever the
  user mentions Heptabase, wants to save something to their knowledge base, search
  their notes or whiteboards, append to a daily journal, retrieve cards or PDF
  content, or any task involving personal knowledge management in Heptabase.
  Also trigger when the user says things like "save this to my notes",
  "check my knowledge base", "look up my research", "add to today's journal",
  "find that whiteboard", or references reading/writing Heptabase content —
  even if they don't say "Heptabase" explicitly but it's clear from context
  that their knowledge base is Heptabase.
---

# Heptabase Skill

A CLI tool that wraps the Heptabase MCP Server, giving agents full read/write
access to a user's Heptabase knowledge base (cards, journals, whiteboards, PDFs).

## How It Works

The CLI (`scripts/heptabase.py`) connects to the Heptabase MCP API via
`npx mcp-remote`. It supports two connection modes:

- **Direct mode** (default): spins up a fresh MCP session per command.
  Each call triggers OAuth in the browser (30–120s). Fine for one-off tasks.
- **Daemon mode** (`HEPTABASE_USE_DAEMON=true`): a long-running process holds
  the MCP session open. Subsequent calls complete in under 1 second.
  Use this for any workflow that involves multiple commands.

## Prerequisites

Before running any command, ensure the Daemon is running if the task involves
more than a single call. The user may need to complete OAuth in a browser the
first time.

```bash
# Check if Daemon is already up
SKILL_DIR="<path-to-this-skill>"
$SKILL_DIR/heptabase daemon status

# If not running, start it (user must complete OAuth in browser)
nohup $SKILL_DIR/heptabase daemon start > /tmp/heptabase-daemon.log 2>&1 &
export HEPTABASE_USE_DAEMON=true
```

`SKILL_DIR` is the directory containing this SKILL.md file. If you're
reading this file, you already know the path — use its parent directory.
Typical location: `~/.openclaw/skills/heptabase`.

---

## Command Reference

All commands are invoked via the wrapper script:

```bash
$SKILL_DIR/heptabase <command> [options]
```

### Writing

| Command | Purpose | Example |
|---------|---------|---------|
| `save --title "T" --content "C"` | Create a new card | `save --title "Meeting Notes" --content "Discussed Q2 roadmap..."` |
| `append-journal "text"` | Append to today's journal | `append-journal "Finished refactoring auth module"` |

Content is Markdown. For `save`, the title becomes the card's h1 heading automatically.

### Searching

| Command | Purpose | Constraints |
|---------|---------|-------------|
| `search "q1" "q2" [--types T]` | Semantic search across objects | 1–3 queries; types: `card,journal,webCard,pdfCard` etc. |
| `search-whiteboard "kw1" "kw2"` | Find whiteboards by keyword | 1–5 keywords, OR logic |
| `search-pdf <pdf_id> "kw1" "kw2"` | Search within a specific PDF | 1–5 keywords, BM25 matching |

Searching returns previews with object IDs. To chain commands, extract the
`id` field from search results and pass it to `get`, `get-whiteboard`,
`search-pdf`, or `get-pdf`. See `docs/API-SCHEMA.md` for full response schemas.

### Reading

| Command | Purpose | Notes |
|---------|---------|-------|
| `get <id> [--type T]` | Read a single object | Default type: `card`. Do NOT use on `pdfCard` (too large). |
| `get-whiteboard <id>` | Read all objects on a whiteboard | Returns structure + partial content |
| `get-journal --start-date D1 --end-date D2` | Read journal entries in range | Max 92 days per call |
| `get-pdf <pdf_id> --start N --end M` | Read specific PDF pages | Pages are 1-indexed, inclusive |

### Daemon Management

| Command | Purpose |
|---------|---------|
| `daemon start` | Start daemon (foreground; use `nohup` for background) |
| `daemon stop` | Stop running daemon |
| `daemon status` | Check if daemon is alive |

---

## Decision Guide — Choosing the Right Approach

Use this to pick the right sequence of commands for common agent tasks:

**"Save/store this content"**
→ `save --title "..." --content "..."`
→ Before saving, consider searching first to avoid duplicates.

**"Record something in today's journal"**
→ `append-journal "..."`

**"Find information in my notes"**
→ `search "query1" "query2"` (semantic, good for concepts)
→ If results reference a whiteboard, follow up with `get-whiteboard`
→ If you need full content of a card, follow up with `get <id>`

**"Find a specific whiteboard"**
→ `search-whiteboard "keyword1" "keyword2"`
→ Then `get-whiteboard <id>` for the full structure

**"Find something inside a PDF"**
→ First: `search "topic" --types pdfCard` to locate the PDF
→ Then: `search-pdf <pdf_id> "keyword1" "keyword2"` to find relevant sections
→ Then: `get-pdf <pdf_id> --start N --end M` to read those pages

**"Review my recent journal entries"**
→ `get-journal --start-date YYYY-MM-DD --end-date YYYY-MM-DD`
→ If the range exceeds 92 days, split into multiple calls.

**"Check if something already exists before writing"**
→ Always `search` before `save` to prevent duplicate cards.

---

## Important Constraints

- **Write-only**: Heptabase MCP only supports creating new content. You cannot
  edit or delete existing cards/journals. Warn the user if they expect edits.
- **Journal range limit**: 92 days max per `get-journal` call. For a full year,
  make 4 sequential calls.
- **PDF pages**: If the user wants more than ~100 pages, confirm before
  proceeding — the response can be very large.
- **Search query limits**: semantic search takes 1–3 queries;
  whiteboard/PDF search takes 1–5 keywords.
- **Avoid `get` on pdfCard type**: PDF cards can be huge. Use `search-pdf` +
  `get-pdf` instead.
- **OAuth**: Direct mode requires browser-based OAuth every time. If the user
  reports slow performance, suggest enabling Daemon mode.

---

## Reference Documentation

For deeper details, read these files from the `docs/` directory:

| File | When to read it |
|------|-----------------|
| `docs/API-SCHEMA.md` | Need exact parameter names, types, enum values, or API constraints |
| `docs/QUICK-REFERENCE.md` | Quick copy-paste command examples |
| `docs/DEVELOPMENT.md` | Understanding internals or debugging connection issues |
| `docs/TESTING.md` | Running tests or validating the CLI tool |
