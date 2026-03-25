# Drupal MCP

Small MCP server for reading and updating Drupal article content through JSON:API. I made this for a talk at **DrupalCon Chicago 2026**, as a proof-of-concept to see if a translator could translate articles by using their favorite AI client, instead of generating machine translations and typing them directly into Drupal.

## What it does

This server exposes MCP tools to:
- list article nodes and available translations
- fetch article body content in a selected language
- update or create translated article body content

It is intended for translation-oriented workflows where an AI assistant needs safe, structured access to Drupal content.

## Available MCP tools

- `get_articles()`  
  Returns article node metadata (`nid`, `uuid`, `title`, `langcode`) plus detected translation languages.

- `get_article_body(uuid: str, langcode: str)`  
  Returns the node body for a given language, including `value` and `format`.

- `set_article_translation(uuid: str, langcode: str, body_value: str, body_format: str)`  
  Writes translated body content for an article and returns confirmation data.

## Requirements

- Python 3.13+
- A Drupal site with JSON:API enabled
- A Drupal user with permission to read and write article content via JSON:API

## Setup

1. Install dependencies:

```bash
uv sync
```

2. Create a `.env` file in the project root:

```env
DRUPAL_BASE_URL=https://your-drupal-site.example
DRUPAL_USERNAME=your-username
DRUPAL_PASSWORD=your-password
```

3. Run the server:

```bash
uv run python main.py
```

## Notes

- The server uses Drupal JSON:API endpoints under `/jsonapi/node/article`.
- For write operations to work, JSON:API must be configured for write access in Drupal admin.
