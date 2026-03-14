# Heptabase MCP API Schema

> Auto-generated from MCP tool definitions. 9 endpoints total.

---

## Table of Contents

1. [append_to_journal](#1-append_to_journal)
2. [get_journal_range](#2-get_journal_range)
3. [get_object](#3-get_object)
4. [get_pdf_pages](#4-get_pdf_pages)
5. [get_whiteboard_with_objects](#5-get_whiteboard_with_objects)
6. [save_to_note_card](#6-save_to_note_card)
7. [search_pdf_content](#7-search_pdf_content)
8. [search_whiteboards](#8-search_whiteboards)
9. [semantic_search_objects](#9-semantic_search_objects)

---

## 1. `append_to_journal`

Append content to today's journal in Heptabase. If today's journal does not exist, it will be created.

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `content` | `string` | Yes | Content to append to the journal. In markdown format. Each block should be separated by an empty line. |

### Example

```json
{
  "content": "## Meeting Notes\n\nDiscussed project timeline.\n\n- Task A: due Friday\n- Task B: due next week"
}
```

---

## 2. `get_journal_range`

Retrieve daily journal entries within a date range (inclusive) from the user's Heptabase knowledge base.

### Constraints

- Each call can retrieve **at most 92 days** (approximately 3 months).
- For longer periods, make multiple calls (e.g., 4 calls for one year).

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `startDate` | `string` | Yes | The start date of the journal range (`YYYY-MM-DD`). Maximum 92 days between startDate and endDate. |
| `endDate` | `string` | Yes | The end date of the journal range (`YYYY-MM-DD`). Must be >= startDate and within 92 days of startDate. |

### Example

```json
{
  "startDate": "2026-01-01",
  "endDate": "2026-03-14"
}
```

---

## 3. `get_object`

Retrieve the complete content of an object from the user's Heptabase knowledge base.

### Details

- Returns full content of cards (notes, journals, media, highlights).
- Returns complete transcripts for video/audio cards.
- All content regardless of length (no chunk limits).
- **Do NOT use this on `pdfCard` objects** since they might be too large.

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `objectId` | `string` | Yes | The id of the object to retrieve. |
| `objectType` | `enum` | Yes | The type of the object. |

### `objectType` Enum Values

```
card, journal, videoCard, audioCard, imageCard,
highlightElement, textElement, videoElement, imageElement,
chat, chatMessage, chatMessagesElement, webCard, section
```

### Example

```json
{
  "objectId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "objectType": "card"
}
```

---

## 4. `get_pdf_pages`

Retrieve specific pages from a PDF card by page numbers from the user's Heptabase knowledge base.

### Constraints

- Page numbers start from **1** (not 0).
- Both `startPageNumber` and `endPageNumber` are **inclusive**.
- If you need significantly more than 100 pages, ask user for clarification first.

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `pdfCardId` | `string` | Yes | The UUID of the PDF card to get pages from. |
| `startPageNumber` | `integer` | Yes | The page number to start from (inclusive, starts from 1). |
| `endPageNumber` | `integer` | Yes | The page number to end at (inclusive). |

### Example

```json
{
  "pdfCardId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "startPageNumber": 1,
  "endPageNumber": 10
}
```

---

## 5. `get_whiteboard_with_objects`

List all objects on a whiteboard with their content from the user's Heptabase knowledge base.

### Details

- Returns complete whiteboard structure showing all objects and their relationships.
- Returns partial content of cards, sections, text elements, mindmaps, images.
- Returns connections between objects.

### Heptabase Structure

- Whiteboards are visual canvases containing multiple objects.
- Objects on the same whiteboard are typically related to the same topic.

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `whiteboardId` | `string` | Yes | The id of the whiteboard to retrieve with all its objects. |

### Example

```json
{
  "whiteboardId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

## 6. `save_to_note_card`

Save any information to a note card in the main space in Heptabase.

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `content` | `string` | Yes | Content of the card. In markdown format. Each block should be separated by an empty line. **The first line should be an h1**, which will be treated as the title of the card. |

### Example

```json
{
  "content": "# Project Architecture\n\nThis card describes the overall architecture.\n\n## Backend\n\n- FastAPI server\n- PostgreSQL database\n\n## Frontend\n\n- React + TypeScript"
}
```

---

## 7. `search_pdf_content`

Search within a large PDF using BM25 keyword matching (OR logic, fuzzy) from the user's Heptabase knowledge base.

### Details

- Returns up to 80 ranked chunks matching the keywords.
- Returns expanded contiguous ranges around matching chunks for context.
- You must first obtain the PDF card ID using other tools (e.g., `semantic_search_objects` or `get_object`).
- Use broad keywords, synonyms, and related terms to maximize coverage.

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `pdfCardId` | `string` | Yes | The UUID of the PDF card to search. |
| `keywords` | `string[]` | Yes | No more than 5 keywords. Use varied terms, synonyms, and related concepts. OR logic — diverse keywords = broader coverage. |

### Constraints

- `keywords`: min 1 item, max 5 items.

### Example

```json
{
  "pdfCardId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "keywords": ["neural network", "deep learning", "architecture"]
}
```

---

## 8. `search_whiteboards`

Search for whiteboards by keywords in the user's Heptabase knowledge base.

### Details

- Uses OR logic: diverse keywords = broader results.
- Results show whiteboard titles and basic info.
- Use `get_whiteboard_with_objects` to retrieve full content of relevant whiteboards.

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `keywords` | `string[]` | Yes | 1–5 keywords. Use varied terms, synonyms, and related concepts for broader coverage (OR logic). |

### Constraints

- `keywords`: min 1 item, max 5 items.

### Example

```json
{
  "keywords": ["project management", "productivity", "workflow"]
}
```

---

## 9. `semantic_search_objects`

Find WHICH objects exist on a topic in the user's Heptabase knowledge base using hybrid search (full-text + semantic).

### Details

- Use multiple queries from different perspectives (1–3 queries) for better coverage.
- Results show previews with titles and partial content.
- If you find relevant objects, use `get_object` to retrieve complete content.
- Returned objects may reference whiteboards they're on — use `search_whiteboards` to explore those.

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `queries` | `string[]` | Yes | Array of search queries in natural language (1–3 queries). Multiple queries from different perspectives improve coverage. |
| `resultObjectTypes` | `enum[]` | Yes | Filter for specific object types. Pass empty array `[]` to search all types. |

### `resultObjectTypes` Enum Values

```
card, pdfCard, mediaCard, highlightElement, journal, webCard
```

### Constraints

- `queries`: min 1 item, max 3 items.
- `resultObjectTypes`: min 0 items (empty array = search all).

### Example

```json
{
  "queries": ["climate change impacts", "environmental policy"],
  "resultObjectTypes": ["card", "journal"]
}
```

---

## API Workflow Patterns

### Pattern 1: Search → Read

```
semantic_search_objects → get_object (for full content)
```

### Pattern 2: Search → Whiteboard Exploration

```
search_whiteboards → get_whiteboard_with_objects → get_object (for specific items)
```

### Pattern 3: PDF Workflow

```
semantic_search_objects (find PDF) → search_pdf_content (find pages) → get_pdf_pages (read content)
```

### Pattern 4: Write Operations

```
append_to_journal → write to today's journal
save_to_note_card → create a new card in main space
```
