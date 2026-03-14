"""Chapter/Textbook management tools for Classavo MCP Server.

Handles course chapters (interactive textbooks) including content reading and navigation.
"""

import logging
from typing import Any, Dict, Optional

from fastmcp import Context

from tools import mcp
from auth import get_client

logger = logging.getLogger(__name__)


@mcp.tool(
    name="list_chapters",
    description="List all chapters (textbooks) for a course. "
    "Use the course public_id (e.g., 'W89PCC4'), not the UUID.",
    tags={"chapters", "professor", "student", "content"},
)
async def list_chapters(
    public_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List all chapters for a course.

    Args:
        public_id: The course public ID (e.g., 'W89PCC4')
        ctx: MCP context for logging

    Returns:
        Dict with list of chapters
    """
    try:
        if ctx:
            await ctx.info(f"Fetching chapters for course {public_id}...")

        client = get_client()
        result = await client.get(f"/api/courses/{public_id}/chapters")

        chapters = result if isinstance(result, list) else result.get("results", [])

        if ctx:
            await ctx.info(f"Found {len(chapters)} chapters")

        return {
            "status": "success",
            "public_id": public_id,
            "count": len(chapters),
            "chapters": chapters,
        }

    except Exception as e:
        error_msg = f"Failed to list chapters: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_chapter",
    description="Get detailed information about a chapter including its structure and content. "
    "Use this to read chapter text and summaries.",
    tags={"chapters", "professor", "student", "content"},
)
async def get_chapter(
    chapter_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get chapter details and content.

    Args:
        chapter_id: The chapter UUID/identity
        ctx: MCP context for logging

    Returns:
        Dict with chapter details and content
    """
    try:
        if ctx:
            await ctx.info(f"Fetching chapter {chapter_id}...")

        client = get_client()

        # Get file/chapter details
        chapter_info = await client.get(f"/api/file/{chapter_id}")

        # Get chapter headings (structure/TOC)
        try:
            headings = await client.get(f"/api/chapters/{chapter_id}/headings")
        except Exception:
            headings = []

        if ctx:
            await ctx.info(f"Loaded chapter: {chapter_info.get('title', 'Unknown')}")

        return {
            "status": "success",
            "chapter": chapter_info,
            "headings": headings,
        }

    except Exception as e:
        error_msg = f"Failed to get chapter: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_chapter_headings",
    description="Get the table of contents (headings/sections) for a chapter. "
    "Useful for understanding chapter structure before reading specific sections.",
    tags={"chapters", "professor", "student", "content"},
)
async def get_chapter_headings(
    chapter_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get chapter headings/table of contents.

    Args:
        chapter_id: The chapter UUID/identity
        ctx: MCP context for logging

    Returns:
        Dict with chapter headings
    """
    try:
        if ctx:
            await ctx.info(f"Fetching headings for chapter {chapter_id}...")

        client = get_client()
        result = await client.get(f"/api/chapters/{chapter_id}/headings")

        headings = result if isinstance(result, list) else result.get("headings", [])

        if ctx:
            await ctx.info(f"Found {len(headings)} headings")

        return {
            "status": "success",
            "chapter_id": chapter_id,
            "count": len(headings),
            "headings": headings,
        }

    except Exception as e:
        error_msg = f"Failed to get chapter headings: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def extract_text_from_plate_node(node: dict) -> str:
    """
    Extract text from a single Plate.js node.

    Args:
        node: A Plate.js node dict

    Returns:
        Text content of the node
    """
    if not isinstance(node, dict):
        return ""

    # Skip special node types that don't contain readable text
    node_type = node.get("type", "")
    if node_type in ("classavo_chapter_question",):
        return ""  # Questions are handled separately

    # If it has a 'text' field directly, return it
    if "text" in node:
        return node["text"]

    # Otherwise, recurse into children
    children = node.get("children", [])
    if children:
        child_texts = []
        for child in children:
            if isinstance(child, dict):
                text = extract_text_from_plate_node(child)
                if text:
                    child_texts.append(text)
            elif isinstance(child, str):
                child_texts.append(child)
        return "".join(child_texts)  # Join without newline for inline elements

    return ""


def extract_text_from_plate_content(content: any) -> str:
    """
    Extract plain text from Plate.js JSON content.

    Plate.js stores content as a tree of nodes with 'children' and 'text' fields.
    This recursively extracts all text content, preserving paragraph structure.

    Args:
        content: Plate.js JSON content (list or dict)

    Returns:
        Plain text string with paragraphs separated by newlines
    """
    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, dict):
        # Handle the root 'content' field if present
        if "content" in content and isinstance(content["content"], list):
            return extract_text_from_plate_content(content["content"])
        return extract_text_from_plate_node(content)

    if isinstance(content, list):
        paragraphs = []
        for item in content:
            if isinstance(item, dict):
                text = extract_text_from_plate_node(item)
                if text.strip():  # Skip empty paragraphs
                    # Add heading markers for better readability
                    node_type = item.get("type", "")
                    if node_type == "h1":
                        text = f"# {text}"
                    elif node_type == "h2":
                        text = f"## {text}"
                    elif node_type == "h3":
                        text = f"### {text}"
                    paragraphs.append(text)
        return "\n\n".join(paragraphs)

    return ""


def extract_questions_from_chapter(data: dict) -> list:
    """
    Extract embedded questions from chapter data.

    Args:
        data: Chapter data containing 'questions' field

    Returns:
        List of question dicts with id, title, and answers
    """
    questions = []
    questions_data = data.get("questions", {})

    # Process both 'create' and 'edit' sections
    for section in ["create", "edit"]:
        section_data = questions_data.get(section, {})
        for q_id, q_data in section_data.items():
            qa_list = q_data.get("questions_and_answers_list", [])
            for qa in qa_list:
                # Extract question title text
                title_content = qa.get("title", [])
                title_text = extract_text_from_plate_content(title_content)

                # Extract answers
                answers = []
                for ans in qa.get("answer", []):
                    ans_title = extract_text_from_plate_content(ans.get("title", []))
                    answers.append({
                        "text": ans_title,
                        "is_correct": ans.get("is_correct", False),
                    })

                questions.append({
                    "identity": qa.get("identity", q_id),
                    "question": title_text,
                    "question_type": q_data.get("question_type"),
                    "points": q_data.get("points"),
                    "answers": answers,
                })

    return questions


@mcp.tool(
    name="get_chapter_content",
    description="Get the full text content of a chapter for reading or summarization. "
    "Returns the chapter body text that can be used for AI analysis.",
    tags={"chapters", "professor", "student", "content", "read"},
)
async def get_chapter_content(
    chapter_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get chapter text content.

    Args:
        chapter_id: The chapter UUID/identity
        ctx: MCP context for logging

    Returns:
        Dict with chapter content including extracted plain text
    """
    try:
        if ctx:
            await ctx.info(f"Fetching content for chapter {chapter_id}...")

        client = get_client()

        # Get chapter/file details - content is in 'content' field as Plate.js JSON
        chapter_info = await client.get(f"/api/file/{chapter_id}")

        title = chapter_info.get("title", "")
        raw_content = chapter_info.get("content")  # Plate.js JSON content

        # Extract plain text from Plate.js content
        plain_text = ""
        if isinstance(raw_content, dict):
            # Content field contains 'content' array and 'questions' object
            content_array = raw_content.get("content", [])
            plain_text = extract_text_from_plate_content(content_array)
        elif isinstance(raw_content, list):
            plain_text = extract_text_from_plate_content(raw_content)

        # Extract embedded questions
        embedded_questions = []
        if isinstance(raw_content, dict):
            embedded_questions = extract_questions_from_chapter(raw_content)

        if ctx:
            if plain_text:
                await ctx.info(f"Loaded chapter: {len(plain_text)} chars, {len(embedded_questions)} questions")
            else:
                await ctx.info("Chapter loaded but content may be empty")

        return {
            "status": "success",
            "chapter_id": chapter_id,
            "title": title,
            "text": plain_text,  # Plain text for easy reading/summarization
            "embedded_questions": embedded_questions,  # Questions embedded in the chapter
        }

    except Exception as e:
        error_msg = f"Failed to get chapter content: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)
