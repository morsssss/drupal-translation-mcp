"""
Drupal Translation MCP Server
Provides tools to retrieve and update article content for translation workflows.

Usage:
    pip install fastmcp httpx
    python drupal_translation_mcp.py

Configuration (set as environment variables or edit the defaults below):
    DRUPAL_BASE_URL  - e.g. https://drupal-dos.ddev.site if yer working locally
    DRUPAL_USERNAME  - Drupal user with JSON:API write access
    DRUPAL_PASSWORD  - Drupal password
"""

import os
from dotenv import load_dotenv
import httpx
import sys
from fastmcp import FastMCP

# --- Configuration ---
DRUPAL_BASE_URL = os.environ.get("DRUPAL_BASE_URL", "https://drupal-dos.ddev.site")
USERNAME = os.environ.get("DRUPAL_USERNAME", "admin")
PASSWORD = os.environ.get("DRUPAL_PASSWORD", "admin")

mcp = FastMCP(
    name="Drupal article translator",
    instructions="Tools for reading and writing content on a Drupal site, "
                 "to support translation workflows using Content Translation."
)


def auth() -> tuple[str, str]:
    return (USERNAME, PASSWORD)


def jsonapi_headers(langcode: str | None = None) -> dict:
    headers = {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }

    if langcode:
        headers.update({
            "Content-Language": langcode,
            "Accept-Language": langcode
        })

    return headers


# ---------------------------------------------------------------------------
# Tool 1: List articles with their node ID, title, and translated languages
# ---------------------------------------------------------------------------
@mcp.tool()
def get_articles() -> list[dict]:
    """
    Retrieve information on all article nodes in a Drupal site. Use this to discover what content the site contains, and what languages that content can be translated into.
    For each article, this returns:
    - nid: the numeric node ID
    - uuid: the UUID (needed for other tools)
    - title: the article title
    - langcode: the original language
    - translations: list of language codes the article has been translated into
    """
    url = f"{DRUPAL_BASE_URL}/jsonapi/node/article"
    params = {
        "fields[node--article]": "drupal_internal__nid,title,langcode,path",
        "page[limit]": 50,
    }

    with httpx.Client(verify=False) as client:
        response = client.get(url, params=params, auth=auth(), headers=jsonapi_headers())
        response.raise_for_status()
        data = response.json()

    articles = []
    for item in data.get("data", []):
        uuid = item["id"]
        attrs = item.get("attributes", {})
        nid = attrs.get("drupal_internal__nid")
        title = attrs.get("title")
        langcode = attrs.get("langcode")

        # Fetch available translations for this node
        translations = get_node_translations(uuid, langcode)

        articles.append({
            "nid": nid,
            "uuid": uuid,
            "title": title,
            "langcode": langcode,
            "translations": translations,
        })

    return articles


# ---------------------------------------------------------------------------
# Tool 2: Get the body content of a specific node
# ---------------------------------------------------------------------------
@mcp.tool()
def get_article_body(uuid: str, langcode: str = "en") -> dict:
    """
    Retrieve the body content of an article node in a given language.

    Args:
        uuid: The node UUID (from get_articles)
        langcode: Language code to retrieve, e.g. "en", "fr", "de" (default: "en")

    Returns:
        A dict with uuid, nid, title, langcode, and body (value + summary)
    """

    url = f"{DRUPAL_BASE_URL}/jsonapi/node/article/{uuid}"
    params = {
        "fields[node--article]": "drupal_internal__nid,title,langcode,body"
    }

    with httpx.Client(verify=False) as client:
        response = client.get(
            url,
            params=params,
            auth=auth(),
            headers=jsonapi_headers(langcode),
        )
        response.raise_for_status()
        data = response.json()

    attrs = data["data"].get("attributes", {})
    body = attrs.get("body") or {}

    return {
        "uuid": uuid,
        "nid": attrs.get("drupal_internal__nid"),
        "langcode": attrs.get("langcode"),
        "body": {
            "value": body.get("value", ""),
            "format": body.get("format", "basic_html"),
        },
    }


# ---------------------------------------------------------------------------
# Tool 3: Set (create or update) the body content of a node in a given language
# ---------------------------------------------------------------------------
@mcp.tool()
def set_article_translation(
    uuid: str,
    langcode: str,
    body_value: str,
    body_format: str = "basic_html"
) -> dict:
    """
    Create or update the translation of an article's body in a given language.
    If the translation doesn't exist yet, this creates it.
    If it already exists, this updates it.

    Args:
        uuid: The node UUID (from get_articles)
        langcode: Target language code, e.g. "fr", "de"
        title: Translated title
        body_value: Translated body HTML/text
        body_summary: Optional translated summary
        body_format: Drupal text format (default: "basic_html")

    Returns:
        A dict confirming the update with the node's uuid and langcode
    """
    url = f"{DRUPAL_BASE_URL}/{langcode}/jsonapi/node/article/{uuid}"

    payload = {
        "data": {
            "type": "node--article",
            "id": uuid,
            "attributes": {
                "body": {
                    "value": body_value,
                    "format": body_format
                },
            },
        }
    }

    with httpx.Client(verify=False) as client:
        response = client.patch(
            url,
            json=payload,
            auth=auth(),
            headers=jsonapi_headers(langcode),
        )
        print(response.request.url, file=sys.stderr)
        print(response.request.headers, file=sys.stderr)
        print(response.request.content, file=sys.stderr)
        response.raise_for_status()
        data = response.json()

    attrs = data["data"].get("attributes", {})
    return {
        "uuid": uuid,
        "nid": attrs.get("drupal_internal__nid"),
        "langcode": attrs.get("langcode"),
        "status": "updated"
    }

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def get_node_translations(uuid: str, source_langcode: str) -> list[str]:
    """
    Check which languages a node has been translated into by probing
    the JSON:API endpoint with different Accept-Language headers.
    Falls back to returning just the source language if detection fails.
    """
    # Fetch the node's translation links from the resource object
    url = f"{DRUPAL_BASE_URL}/jsonapi/node/article/{uuid}"
    translations = [source_langcode]

    with httpx.Client(verify=False) as client:
        response = client.get(url, auth=auth(), headers=jsonapi_headers())
        if response.status_code != 200:
            return translations
        data = response.json()

    # Drupal exposes available translations in the links object
    links = data.get("data", {}).get("links", {})
    for key in links:
        # Translation links are keyed like "translation--fr", "translation--de" etc.
        if key.startswith("translation--"):
            lang = key.replace("translation--", "")
            if lang not in translations:
                translations.append(lang)

    return translations



if __name__ == "__main__":
    mcp.run()
