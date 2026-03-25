# Drupal Translator MCP 

Small MCP server for reading and updating Drupal article content through JSON:API. I made this for a talk at **DrupalCon Chicago 2026**, as a proof-of-concept to see if a translator could translate articles by using their favorite AI client, instead of generating machine translations and typing them directly into Drupal.

This is just an initial proof of concept. Feel free to grab this and build on it!

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

- Python 3.13+ (though you can almost certainly get this to work on earlier Python versions)
- A Drupal site with JSON:API enabled

## Setup

1. Install dependencies:

```bash
uv sync
```

2. Create a `.env` file in the project root to give the server basic info about your Drupal site

```env
DRUPAL_BASE_URL=https://your-drupal-site.example
DRUPAL_USERNAME=your-username
DRUPAL_PASSWORD=your-password
```

3. Add the server to your favorite AI client. Assuming you're running this on your machine, you'll
want to use a client that runs on your desktop machine.
Your client may have an interface for adding local MCP servers, but at press time (3/25/2026), in Claude Desktop,
at least, you need to edit a JSON file directly. Other AI clients I've seen use the same JSON format.

So, for Claude, for example, find the file located here:
* Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
* Windows: `%APPDATA%\Claude\claude_desktop_config.json`
* Linux: `~/.config/Claude/claude-desktop-config.json`

You'll insert JSON that looks something like this:
```json
{
  "mcpServers": {
    "drupal translation friend": {
      "command": "/Users/{your user name}/.local/bin/uv",
      "args": [
        "--directory",
        "/Users/sofo/{your user name}/drupal-translation-mcp",
        "run",
        "fastmcp",
        "run",
        "main.py"
      ]
    }
  }
}
```

## Notes

- The server uses Drupal JSON:API endpoints under `/jsonapi/node/article`.
- For write operations to work, JSON:API must be configured for write access.
