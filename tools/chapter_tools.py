"""Chapter/Textbook management tools for Classavo MCP Server.

Handles course chapters (interactive textbooks) including content reading and navigation.
"""

import logging
import random
import string
import uuid
from typing import Any, Dict, List, Optional

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

        # Get chapter/file details
        chapter_info = await client.get(f"/api/file/{chapter_id}")

        title = chapter_info.get("title", "")

        # The 'content' field from API has this structure:
        # {
        #   "static_content": [...],  // The actual Plate.js nodes
        #   "properties": {...},
        #   "questions": [...]  // Full question objects
        # }
        raw_content = chapter_info.get("content")

        # Extract content array and plain text
        plain_text = ""
        content_array = []
        embedded_questions = []

        if isinstance(raw_content, dict):
            # Standard format: extract from static_content
            content_array = raw_content.get("static_content", [])
            if not content_array:
                # Fallback: try 'content' key
                content_array = raw_content.get("content", [])

            plain_text = extract_text_from_plate_content(content_array)

            # Extract questions from the 'questions' array
            questions_list = raw_content.get("questions", [])
            for q in questions_list:
                q_title = extract_text_from_plate_content(q.get("title", []))
                answers = []
                for ans in q.get("answer", []):
                    ans_title = extract_text_from_plate_content(ans.get("title", []))
                    answers.append({
                        "text": ans_title,
                        "is_correct": ans.get("is_correct", False),
                    })
                embedded_questions.append({
                    "identity": q.get("identity"),
                    "question": q_title,
                    "question_type": q.get("question_type"),
                    "points": q.get("points"),
                    "answers": answers,
                })

        elif isinstance(raw_content, list):
            # Direct array format
            content_array = raw_content
            plain_text = extract_text_from_plate_content(raw_content)

        if ctx:
            if plain_text:
                await ctx.info(f"Loaded chapter: {len(plain_text)} chars, {len(embedded_questions)} questions")
            else:
                await ctx.info(f"Chapter loaded: {len(content_array)} nodes, {len(embedded_questions)} questions")

        # Debug: Include info about content structure
        content_type = type(raw_content).__name__
        content_length = len(content_array)

        return {
            "status": "success",
            "chapter_id": chapter_id,
            "title": title,
            "text": plain_text,  # Plain text for easy reading/summarization
            "embedded_questions": embedded_questions,  # Questions embedded in the chapter
            "debug_content_type": content_type,  # For debugging: 'dict', 'list', or 'NoneType'
            "debug_content_nodes": content_length,  # Number of content nodes
        }

    except Exception as e:
        error_msg = f"Failed to get chapter content: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def generate_question_id() -> str:
    """Generate a UUID for a new question."""
    return str(uuid.uuid4())


def generate_node_id() -> str:
    """Generate a short ID for Plate.js nodes."""
    return ''.join(random.choices(string.ascii_letters + string.digits + '_-', k=10))


def create_plate_text(text: str) -> list:
    """Create a Plate.js paragraph with text."""
    return [{"type": "p", "children": [{"text": text}], "id": generate_node_id()}]


def create_plate_title(text: str) -> list:
    """
    Create a Plate.js title array for question text.

    Classavo expects title as a JSON array of Plate.js nodes, not HTML strings.
    """
    return [{"type": "p", "children": [{"text": text}], "id": generate_node_id()}]


def create_mcq_question_data(
    question_text: str,
    options: list,
    correct_index: int,
    points: str = "0.50",
    points_participation: str = "0.50",
) -> tuple:
    """
    Create MCQ question data for embedding in a chapter.

    Based on Classavo API schema (from content (1).json):
    - question_type: 1 = MULTIPLE_CHOICE
    - questions_and_answers_list: Array with title as Plate.js JSON array
    - answer: Array of {identity, title (Plate.js array), is_correct, index}

    Args:
        question_text: The question text
        options: List of answer option strings
        correct_index: Index of the correct answer (0-based)
        points: Points for correct answer
        points_participation: Participation points

    Returns:
        Tuple of (question_key, question_node, question_data)
    """
    # Generate a temporary key for the new question (used to link node to data)
    question_key = f"new-question-{generate_node_id()}"

    # Create the content node that embeds the question
    question_node = {
        "type": "classavo_chapter_question",
        "question_id": question_key,  # Temporary key, backend replaces with UUID
        "children": [{"text": ""}],
        "id": generate_node_id(),
    }

    # Create answer objects with Plate.js title format (index is 1-based)
    answers = []
    for i, option_text in enumerate(options):
        answers.append({
            "identity": f"option-{generate_node_id()}",
            "title": [{"type": "p", "children": [{"text": option_text}], "id": generate_node_id()}],
            "is_correct": i == correct_index,
            "index": i + 1,  # 1-based index
        })

    # Create the question data using questions_and_answers_list format
    question_data = {
        "questions_and_answers_list": [{
            "identity": question_key,
            "title": create_plate_title(question_text),
            "answer": answers,
        }],
        "question_type": 1,  # 1 = MULTIPLE_CHOICE
        "points": points,
        "points_participation": points_participation,
        "points_multiple_correct_policy": 5,
        "max_attempts": 1,
        "message_if_correct": "",
        "message_if_incorrect": "",
        "use_ai_message": True,
        "is_extra_credit": False,
        "feedback_type": 1,
        "feedback_timing": 1,
        "feedback_delay_days": 0,
        "identity": question_key,
    }

    return question_key, question_node, question_data


# Question type constants
QUESTION_TYPES = {
    "multiple_choice": 1,
    "mcq": 1,
    "written": 2,
    "written_answer": 2,
    "fill_blank": 3,
    "fill_in_the_blank": 3,
    "matching": 4,
    "file_upload": 5,
    "discussion": 7,
    "equation": 100,
    "formula": 100,
}


def create_question_node(question_key: str) -> dict:
    """Create a Plate.js node for embedding a question in chapter content."""
    return {
        "type": "classavo_chapter_question",
        "question_id": question_key,
        "children": [{"text": ""}],
        "id": generate_node_id(),
    }


def create_written_question_data(
    question_text: str,
    rubric: str = "",
    points: str = "0.50",
    points_participation: str = "0.50",
) -> tuple:
    """
    Create Written Answer question data.

    Based on Classavo API schema (from content (1).json):
    - question_type: 2 = WRITTEN_ANSWER
    - questions_and_answers_list with Plate.js title format
    - answer: Array with rubric

    Args:
        question_text: The question text
        rubric: Grading rubric/guidelines
        points: Points for the question
        points_participation: Participation points

    Returns:
        Tuple of (question_key, question_node, question_data)
    """
    question_key = f"new-question-{generate_node_id()}"
    question_node = create_question_node(question_key)

    question_data = {
        "questions_and_answers_list": [{
            "identity": question_key,
            "title": create_plate_title(question_text),
            "answer": [{"rubric": rubric, "index": 0}],
        }],
        "question_type": 2,  # WRITTEN_ANSWER
        "points": points,
        "points_participation": points_participation,
        "points_multiple_correct_policy": 5,
        "max_attempts": 1,
        "message_if_correct": "",
        "message_if_incorrect": "",
        "use_ai_message": True,
        "is_extra_credit": False,
        "feedback_type": 1,
        "feedback_timing": 2,
        "feedback_delay_days": 0,
        "identity": question_key,
    }

    return question_key, question_node, question_data


def create_fill_blank_title(question_text: str, num_blanks: int) -> list:
    """
    Create a Plate.js title array for fill-in-the-blank questions.

    The title must contain classavo_question_blank nodes as children.
    Supports placeholders: [BLANK1], [BLANK], ___, {BLANK}, etc.

    Args:
        question_text: Question text with optional placeholders
        num_blanks: Number of blanks to insert

    Returns:
        Plate.js title array with embedded blank nodes
    """
    import re

    # Define placeholder patterns
    placeholder_pattern = r'\[BLANK\d*\]|\[blank\d*\]|\{BLANK\d*\}|\{blank\d*\}|_{3,}'

    # Split text by placeholders
    parts = re.split(f'({placeholder_pattern})', question_text)

    # Build children array with text and blank nodes
    children = []
    blank_count = 0

    for part in parts:
        if not part:
            continue
        if re.match(placeholder_pattern, part):
            # This is a placeholder - replace with blank node
            if blank_count < num_blanks:
                blank_count += 1
                children.append({
                    "type": "classavo_question_blank",
                    "classavo_data": blank_count,
                    "children": [{"text": ""}],
                    "id": generate_node_id(),
                })
        else:
            # Regular text
            children.append({"text": part})

    # If no placeholders were found, append blanks at the end
    while blank_count < num_blanks:
        blank_count += 1
        if children and isinstance(children[-1], dict) and "text" in children[-1]:
            # Add space before blank if last element is text
            children[-1]["text"] = children[-1]["text"].rstrip() + " "
        children.append({
            "type": "classavo_question_blank",
            "classavo_data": blank_count,
            "children": [{"text": ""}],
            "id": generate_node_id(),
        })

    # Ensure we have at least one text node if children is empty
    if not children:
        children = [{"text": ""}]

    return [{"type": "p", "children": children, "id": generate_node_id()}]


def create_fill_blank_question_data(
    question_text: str,
    blanks: list,
    points: str = "0.50",
    points_participation: str = "0.50",
) -> tuple:
    """
    Create Fill in the Blank question data.

    Based on Classavo API schema (from content (1).json):
    - question_type: 3 = FILL_IN_THE_BLANK
    - title: Plate.js array with classavo_question_blank nodes embedded in children
    - answer: Array with blank_index, word, and tolerance settings

    Args:
        question_text: Question text, optionally with [BLANK1], ___, etc. placeholders
        blanks: List of correct answers for each blank, e.g., ["Paris", "France"]
        points: Points for the question
        points_participation: Participation points

    Returns:
        Tuple of (question_key, question_node, question_data)
    """
    question_key = f"new-question-{generate_node_id()}"
    question_node = create_question_node(question_key)

    # Create title with embedded blank nodes (Plate.js format)
    title = create_fill_blank_title(question_text, len(blanks))

    # Create answer objects for each blank
    answers = []
    for i, word in enumerate(blanks):
        answers.append({
            "index": i,
            "blank_index": i + 1,
            "identity": f"blank-{generate_node_id()}",
            "word": word,
            "is_case_sensitive": False,
            "is_space_sensitive": False,
            "is_numeric": False,
            "tolerance": "0",
            "is_tolerance_percentage": False,
            "significant_figures": 0,
        })

    question_data = {
        "questions_and_answers_list": [{
            "identity": question_key,
            "title": title,
            "answer": answers,
        }],
        "question_type": 3,  # FILL_IN_THE_BLANK
        "points": points,
        "points_participation": points_participation,
        "points_multiple_correct_policy": 5,
        "max_attempts": 2,
        "message_if_correct": "",
        "message_if_incorrect": "",
        "use_ai_message": True,
        "is_extra_credit": False,
        "feedback_type": 1,
        "feedback_timing": 1,
        "feedback_delay_days": 0,
        "identity": question_key,
    }

    return question_key, question_node, question_data


def create_matching_question_data(
    question_text: str,
    pairs: list,
    points: str = "0.50",
    points_participation: str = "0.50",
) -> tuple:
    """
    Create Matching question data.

    Based on Classavo API schema:
    - question_type: 4 = MATCHING
    - questions_and_answers_list with Plate.js title format
    - answer: Array with prompt_title, match_title as Plate.js arrays

    Args:
        question_text: The question/instruction text
        pairs: List of tuples/dicts with prompt and match, e.g., [{"prompt": "A", "match": "1"}, ...]
        points: Points for the question
        points_participation: Participation points

    Returns:
        Tuple of (question_key, question_node, question_data)
    """
    question_key = f"new-question-{generate_node_id()}"
    question_node = create_question_node(question_key)

    # Create answer objects for matching pairs with Plate.js format
    answers = []
    for i, pair in enumerate(pairs):
        if isinstance(pair, dict):
            prompt = pair.get("prompt", "")
            match = pair.get("match", "")
        elif isinstance(pair, (list, tuple)) and len(pair) >= 2:
            prompt, match = pair[0], pair[1]
        else:
            continue

        answers.append({
            "identity": f"match-{generate_node_id()}",
            "prompt_title": [{"type": "p", "children": [{"text": prompt}], "id": generate_node_id()}],
            "match_title": [{"type": "p", "children": [{"text": match}], "id": generate_node_id()}],
            "match_id": i + 1,
            "index": i,
        })

    question_data = {
        "questions_and_answers_list": [{
            "identity": question_key,
            "title": create_plate_title(question_text),
            "answer": answers,
        }],
        "question_type": 4,  # MATCHING
        "points": points,
        "points_participation": points_participation,
        "points_multiple_correct_policy": 5,
        "max_attempts": 2,
        "message_if_correct": "",
        "message_if_incorrect": "",
        "use_ai_message": True,
        "is_extra_credit": False,
        "feedback_type": 1,
        "feedback_timing": 1,
        "feedback_delay_days": 0,
        "identity": question_key,
    }

    return question_key, question_node, question_data


def create_file_upload_question_data(
    question_text: str,
    instructions: str = "",
    points: str = "0.50",
    points_participation: str = "0.50",
) -> tuple:
    """
    Create File Upload question data.

    Based on Classavo API schema:
    - question_type: 5 = FILE_UPLOAD
    - questions_and_answers_list with Plate.js title format

    Args:
        question_text: The question text
        instructions: Additional upload instructions
        points: Points for the question
        points_participation: Participation points

    Returns:
        Tuple of (question_key, question_node, question_data)
    """
    question_key = f"new-question-{generate_node_id()}"
    question_node = create_question_node(question_key)

    # For file upload, answer contains title (instructions) as Plate.js format
    answer_title = create_plate_title(instructions) if instructions else []

    question_data = {
        "questions_and_answers_list": [{
            "identity": question_key,
            "title": create_plate_title(question_text),
            "answer": [{"title": answer_title, "answer": []}],
        }],
        "question_type": 5,  # FILE_UPLOAD
        "points": points,
        "points_participation": points_participation,
        "points_multiple_correct_policy": 5,
        "max_attempts": 1,
        "message_if_correct": "",
        "message_if_incorrect": "",
        "use_ai_message": True,
        "is_extra_credit": False,
        "feedback_type": 1,
        "feedback_timing": 2,
        "feedback_delay_days": 0,
        "identity": question_key,
    }

    return question_key, question_node, question_data


def create_discussion_question_data(
    question_text: str,
    response_visibility: str = "everyone",
    anonymous_to: str = "noone",
    points: str = "0",
    points_participation: str = "5.0",
) -> tuple:
    """
    Create Discussion question data.

    Based on Classavo API schema:
    - question_type: 7 = DISCUSSION
    - questions_and_answers_list with Plate.js title format

    Args:
        question_text: The discussion prompt
        response_visibility: "everyone" or "instructors_only"
        anonymous_to: "noone" or "students_only"
        points: Points (typically 0 for discussions)
        points_participation: Participation points

    Returns:
        Tuple of (question_key, question_node, question_data)
    """
    question_key = f"new-question-{generate_node_id()}"
    question_node = create_question_node(question_key)

    question_data = {
        "questions_and_answers_list": [{
            "identity": question_key,
            "title": create_plate_title(question_text),
            "answer": [],
        }],
        "question_type": 7,  # DISCUSSION
        "response_visibility": response_visibility,
        "anonymous_to": anonymous_to,
        "blocked_words": [],
        "points": points,
        "points_participation": points_participation,
        "points_multiple_correct_policy": 5,
        "max_attempts": 1,
        "message_if_correct": "",
        "message_if_incorrect": "",
        "use_ai_message": False,
        "is_extra_credit": False,
        "feedback_type": 1,
        "feedback_timing": 1,
        "feedback_delay_days": 0,
        "identity": question_key,
    }

    return question_key, question_node, question_data


def create_equation_question_data(
    question_text: str,
    correct_answer: str,
    points: str = "0.50",
    points_participation: str = "0.50",
) -> tuple:
    """
    Create Equation/Formula question data.

    Based on Classavo API schema:
    - question_type: 100 = EQUATION
    - questions_and_answers_list with Plate.js title format

    Args:
        question_text: The question text
        correct_answer: The correct formula/equation (LaTeX or plain text)
        points: Points for the question
        points_participation: Participation points

    Returns:
        Tuple of (question_key, question_node, question_data)
    """
    question_key = f"new-question-{generate_node_id()}"
    question_node = create_question_node(question_key)

    question_data = {
        "questions_and_answers_list": [{
            "identity": question_key,
            "title": create_plate_title(question_text),
            "answer": [{"identity": "", "correct_input": correct_answer, "index": 0}],
        }],
        "question_type": 100,  # EQUATION
        "points": points,
        "points_participation": points_participation,
        "points_multiple_correct_policy": 5,
        "max_attempts": 2,
        "message_if_correct": "",
        "message_if_incorrect": "",
        "use_ai_message": True,
        "is_extra_credit": False,
        "feedback_type": 1,
        "feedback_timing": 1,
        "feedback_delay_days": 0,
        "identity": question_key,
    }

    return question_key, question_node, question_data


@mcp.tool(
    name="add_any_chapter_question",
    description="[PROFESSOR ONLY] Add any type of question to a chapter. "
    "Supported types: 'mcq' (multiple choice), 'written' (written answer), 'fill_blank', "
    "'matching', 'file_upload', 'discussion', 'equation'. "
    "Each type requires different parameters in the question_data JSON.",
    tags={"chapters", "professor", "questions", "content"},
)
async def add_any_chapter_question(
    chapter_id: str,
    question_type: str,
    question_text: str,
    question_data: str = "{}",
    points: str = "1.0",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Add any type of question to a chapter.

    Args:
        chapter_id: The chapter UUID/identity
        question_type: Type of question - 'mcq', 'written', 'fill_blank', 'matching',
                       'file_upload', 'discussion', 'equation'
        question_text: The question text
        question_data: JSON string with type-specific data:
            - mcq: {"options": ["A", "B", "C"], "correct_index": 0}
            - written: {"rubric": "Grading guidelines..."} (optional)
            - fill_blank: {"blanks": ["answer1", "answer2"]} (answers for each blank)
            - matching: {"pairs": [{"prompt": "A", "match": "1"}, ...]}
            - file_upload: {"instructions": "Upload a PDF..."} (optional)
            - discussion: {"visibility": "everyone", "anonymous": "noone"} (optional)
            - equation: {"correct_answer": "x^2 + 2x + 1"}
        points: Points for the question (default "1.0")
        ctx: MCP context for logging

    Returns:
        Dict with created question info
    """
    import json

    try:
        if ctx:
            await ctx.info(f"Adding {question_type} question to chapter {chapter_id}...")

        # Parse question_data JSON
        try:
            data = json.loads(question_data) if question_data else {}
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid question_data JSON: {e}")

        # Validate question type
        q_type_lower = question_type.lower().replace("-", "_").replace(" ", "_")
        if q_type_lower not in QUESTION_TYPES:
            raise ValueError(
                f"Unknown question type '{question_type}'. "
                f"Supported: mcq, written, fill_blank, matching, file_upload, discussion, equation"
            )

        client = get_client()

        # Get current chapter content
        chapter_info = await client.get(f"/api/file/{chapter_id}")
        raw_content = chapter_info.get("content")

        # Extract content array from static_content
        content_array = []
        if isinstance(raw_content, dict):
            content_array = raw_content.get("static_content", [])
            if not content_array:
                content_array = raw_content.get("content", [])
        elif isinstance(raw_content, list):
            content_array = raw_content

        if not isinstance(content_array, list):
            content_array = []

        logger.info(f"Chapter {chapter_id}: Found {len(content_array)} existing content nodes")

        # SAFETY CHECK: Prevent content loss
        if len(content_array) == 0 and raw_content is not None:
            raise RuntimeError(
                f"Safety check failed: Could not extract content from chapter. "
                f"raw_content type: {type(raw_content).__name__}. Aborting to prevent content loss."
            )

        # Create question based on type
        if q_type_lower in ("mcq", "multiple_choice"):
            options = data.get("options", [])
            correct_index = data.get("correct_index", 0)
            if len(options) < 2:
                raise ValueError("MCQ requires at least 2 options in question_data")
            question_key, question_node, question_payload = create_mcq_question_data(
                question_text=question_text,
                options=options,
                correct_index=correct_index,
                points=points,
            )
        elif q_type_lower in ("written", "written_answer"):
            rubric = data.get("rubric", "")
            question_key, question_node, question_payload = create_written_question_data(
                question_text=question_text,
                rubric=rubric,
                points=points,
            )
        elif q_type_lower in ("fill_blank", "fill_in_the_blank"):
            blanks = data.get("blanks", [])
            if not blanks:
                raise ValueError("Fill in the blank requires 'blanks' array in question_data")
            question_key, question_node, question_payload = create_fill_blank_question_data(
                question_text=question_text,
                blanks=blanks,
                points=points,
            )
        elif q_type_lower == "matching":
            pairs = data.get("pairs", [])
            if len(pairs) < 2:
                raise ValueError("Matching requires at least 2 pairs in question_data")
            question_key, question_node, question_payload = create_matching_question_data(
                question_text=question_text,
                pairs=pairs,
                points=points,
            )
        elif q_type_lower == "file_upload":
            instructions = data.get("instructions", "")
            question_key, question_node, question_payload = create_file_upload_question_data(
                question_text=question_text,
                instructions=instructions,
                points=points,
            )
        elif q_type_lower == "discussion":
            visibility = data.get("visibility", "everyone")
            anonymous = data.get("anonymous", "noone")
            question_key, question_node, question_payload = create_discussion_question_data(
                question_text=question_text,
                response_visibility=visibility,
                anonymous_to=anonymous,
                points="0",  # Discussions typically don't have correctness points
                points_participation=points,
            )
        elif q_type_lower in ("equation", "formula"):
            correct_answer = data.get("correct_answer", "")
            if not correct_answer:
                raise ValueError("Equation requires 'correct_answer' in question_data")
            question_key, question_node, question_payload = create_equation_question_data(
                question_text=question_text,
                correct_answer=correct_answer,
                points=points,
            )
        else:
            raise ValueError(f"Unhandled question type: {q_type_lower}")

        # Make a copy and add question node
        updated_content = list(content_array)
        empty_para = {"type": "p", "id": generate_node_id(), "children": [{"text": ""}]}
        updated_content.append(question_node)
        updated_content.append(empty_para)

        # Build questions payload
        questions_payload = {
            "create": {question_key: question_payload},
            "edit": {},
            "delete": [],
        }

        logger.info(f"Sending content with {len(updated_content)} nodes, adding {question_type} question")

        # Update the chapter
        await client.put(
            f"/api/file/{chapter_id}",
            data={
                "content": updated_content,
                "questions": questions_payload,
            },
        )

        if ctx:
            await ctx.info(f"{question_type.upper()} question added successfully!")

        return {
            "status": "success",
            "message": f"{question_type} question added to chapter",
            "chapter_id": chapter_id,
            "question_id": question_key,
            "question_type": question_type,
            "question_text": question_text,
        }

    except Exception as e:
        error_msg = f"Failed to add chapter question: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="add_chapter_question",
    description="[PROFESSOR ONLY] Add a multiple choice question to a chapter. "
    "The question will be embedded directly in the chapter content. "
    "Options should be comma-separated, and correct_option_index is 0-based (0 for first option).",
    tags={"chapters", "professor", "questions", "content"},
)
async def add_chapter_question(
    chapter_id: str,
    question_text: str,
    options: str,
    correct_option_index: int,
    points: str = "1.0",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Add a multiple choice question to a chapter.

    Args:
        chapter_id: The chapter UUID/identity
        question_text: The question text
        options: Comma-separated answer options (e.g., "Option A, Option B, Option C, Option D")
        correct_option_index: Index of correct answer (0-based, e.g., 0 for first option)
        points: Points for the question (default "1.0")
        ctx: MCP context for logging

    Returns:
        Dict with created question info
    """
    try:
        if ctx:
            await ctx.info(f"Adding question to chapter {chapter_id}...")

        client = get_client()

        # Get current chapter content
        chapter_info = await client.get(f"/api/file/{chapter_id}")

        # The 'content' field from API has this structure:
        # {
        #   "static_content": [...],  // The actual Plate.js nodes
        #   "properties": {...},
        #   "data": {...},
        #   "chapter_assignment_identity": "uuid",
        #   "questions": [...]  // Full question objects (read-only)
        # }
        raw_content = chapter_info.get("content")

        # Debug: Log what we received
        logger.info(f"Chapter {chapter_id}: raw_content type = {type(raw_content).__name__}")
        if isinstance(raw_content, dict):
            logger.info(f"Chapter {chapter_id}: raw_content keys = {list(raw_content.keys())}")

        # Extract content array from static_content
        content_array = []
        if isinstance(raw_content, dict):
            # Standard format: extract from static_content
            content_array = raw_content.get("static_content", [])
            if not content_array:
                # Fallback: try 'content' key
                content_array = raw_content.get("content", [])
        elif isinstance(raw_content, list):
            # Direct array format (less common)
            content_array = raw_content

        # Ensure content_array is a list
        if not isinstance(content_array, list):
            logger.warning(f"Chapter {chapter_id}: content_array is {type(content_array)}, converting to list")
            content_array = []

        # Log current content for debugging
        logger.info(f"Chapter {chapter_id}: Found {len(content_array)} existing content nodes")

        # Parse options
        option_list = [opt.strip() for opt in options.split(",")]
        if len(option_list) < 2:
            raise ValueError("At least 2 options are required")
        if correct_option_index < 0 or correct_option_index >= len(option_list):
            raise ValueError(f"correct_option_index must be between 0 and {len(option_list) - 1}")

        # Create the question
        question_id, question_node, question_data = create_mcq_question_data(
            question_text=question_text,
            options=option_list,
            correct_index=correct_option_index,
            points=points,
        )

        # SAFETY CHECK: If we found no content but raw_content exists, abort to prevent data loss
        if len(content_array) == 0 and raw_content is not None:
            raise RuntimeError(
                f"Safety check failed: Could not extract content from chapter. "
                f"raw_content type: {type(raw_content).__name__}. "
                f"Aborting to prevent content loss. Please check the API response format."
            )

        # Make a copy of the content array to avoid modifying the original
        updated_content = list(content_array)

        # Add question node to the end of content
        # Also add an empty paragraph after the question
        empty_para = {"type": "p", "id": generate_node_id(), "children": [{"text": ""}]}
        updated_content.append(question_node)
        updated_content.append(empty_para)

        # For questions, we only add to 'create' - keep existing questions in edit
        # Clear create/delete for this request, only add our new question
        questions_payload = {
            "create": {question_id: question_data},
            "edit": {},  # Don't modify existing questions
            "delete": [],  # Don't delete any questions
        }

        logger.info(f"Sending content with {len(updated_content)} nodes, adding question {question_id}")

        # Update the chapter - content is array, questions is object
        result = await client.put(
            f"/api/file/{chapter_id}",
            data={
                "content": updated_content,
                "questions": questions_payload,
            },
        )

        if ctx:
            await ctx.info(f"Question added successfully!")

        return {
            "status": "success",
            "message": "Question added to chapter",
            "chapter_id": chapter_id,
            "question_id": question_id,
            "question_text": question_text,
            "options": option_list,
            "correct_option": option_list[correct_option_index],
        }

    except Exception as e:
        error_msg = f"Failed to add chapter question: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="add_multiple_chapter_questions",
    description="[PROFESSOR ONLY] Add multiple questions of any type to a chapter at once. "
    "Each question needs: question_type, question_text, and type-specific fields. "
    "Types: 'mcq', 'written', 'fill_blank', 'matching', 'file_upload', 'discussion', 'equation'. "
    "Examples: "
    "[{\"question_type\": \"mcq\", \"question_text\": \"What is X?\", \"options\": [\"A\", \"B\"], \"correct_index\": 0}, "
    "{\"question_type\": \"written\", \"question_text\": \"Explain Y.\", \"rubric\": \"Full sentences required\"}, "
    "{\"question_type\": \"fill_blank\", \"question_text\": \"The capital of France is [BLANK1].\", \"blanks\": [\"Paris\"]}, "
    "{\"question_type\": \"matching\", \"question_text\": \"Match the items.\", \"pairs\": [{\"prompt\": \"A\", \"match\": \"1\"}]}, "
    "{\"question_type\": \"equation\", \"question_text\": \"Solve: 2+2=\", \"correct_answer\": \"4\"}]",
    tags={"chapters", "professor", "questions", "content"},
)
async def add_multiple_chapter_questions(
    chapter_id: str,
    questions_json: str,
    default_points: str = "1.0",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Add multiple questions of any type to a chapter.

    Args:
        chapter_id: The chapter UUID/identity
        questions_json: JSON array of questions. Each question needs:
            - question_type: 'mcq', 'written', 'fill_blank', 'matching', 'file_upload', 'discussion', 'equation'
            - question_text: The question text
            - Type-specific fields:
                - mcq: options (array), correct_index (int)
                - written: rubric (optional string)
                - fill_blank: blanks (array of correct answers)
                - matching: pairs (array of {prompt, match})
                - file_upload: instructions (optional string)
                - discussion: visibility, anonymous (optional)
                - equation: correct_answer (string)
            - points (optional): Points for this question
        default_points: Default points for questions without explicit points
        ctx: MCP context for logging

    Returns:
        Dict with created questions info
    """
    import json

    try:
        if ctx:
            await ctx.info(f"Adding multiple questions to chapter {chapter_id}...")

        # Parse questions JSON
        try:
            questions_list = json.loads(questions_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if not isinstance(questions_list, list):
            raise ValueError("questions_json must be a JSON array")

        client = get_client()

        # Get current chapter content
        chapter_info = await client.get(f"/api/file/{chapter_id}")
        raw_content = chapter_info.get("content")

        logger.info(f"Chapter {chapter_id}: raw_content type = {type(raw_content).__name__}")

        # Extract content array from static_content
        content_array = []
        if isinstance(raw_content, dict):
            content_array = raw_content.get("static_content", [])
            if not content_array:
                content_array = raw_content.get("content", [])
        elif isinstance(raw_content, list):
            content_array = raw_content

        if not isinstance(content_array, list):
            content_array = []

        logger.info(f"Chapter {chapter_id}: Found {len(content_array)} existing content nodes")

        # SAFETY CHECK: Prevent content loss
        if len(content_array) == 0 and raw_content is not None:
            raise RuntimeError(
                f"Safety check failed: Could not extract content from chapter. Aborting to prevent content loss."
            )

        # Make a copy of the content array to preserve existing content
        updated_content = list(content_array)

        # Track new questions to create
        new_questions = {}
        added_questions = []
        errors = []

        for i, q in enumerate(questions_list):
            question_text = q.get("question_text", "")
            question_type = q.get("question_type", "mcq").lower().replace("-", "_").replace(" ", "_")
            points = q.get("points", default_points)

            if not question_text:
                errors.append(f"Question {i}: missing question_text")
                continue

            if question_type not in QUESTION_TYPES:
                errors.append(f"Question {i}: unknown type '{question_type}'")
                continue

            try:
                # Create question based on type
                if question_type in ("mcq", "multiple_choice"):
                    options = q.get("options", [])
                    correct_index = q.get("correct_index", q.get("correct_option_index", 0))
                    if len(options) < 2:
                        errors.append(f"Question {i}: MCQ needs at least 2 options")
                        continue
                    question_key, question_node, question_payload = create_mcq_question_data(
                        question_text=question_text,
                        options=options,
                        correct_index=correct_index,
                        points=points,
                    )
                elif question_type in ("written", "written_answer"):
                    rubric = q.get("rubric", "")
                    question_key, question_node, question_payload = create_written_question_data(
                        question_text=question_text,
                        rubric=rubric,
                        points=points,
                    )
                elif question_type in ("fill_blank", "fill_in_the_blank"):
                    blanks = q.get("blanks", [])
                    if not blanks:
                        errors.append(f"Question {i}: fill_blank needs 'blanks' array")
                        continue
                    question_key, question_node, question_payload = create_fill_blank_question_data(
                        question_text=question_text,
                        blanks=blanks,
                        points=points,
                    )
                elif question_type == "matching":
                    pairs = q.get("pairs", [])
                    if len(pairs) < 2:
                        errors.append(f"Question {i}: matching needs at least 2 pairs")
                        continue
                    question_key, question_node, question_payload = create_matching_question_data(
                        question_text=question_text,
                        pairs=pairs,
                        points=points,
                    )
                elif question_type == "file_upload":
                    instructions = q.get("instructions", "")
                    question_key, question_node, question_payload = create_file_upload_question_data(
                        question_text=question_text,
                        instructions=instructions,
                        points=points,
                    )
                elif question_type == "discussion":
                    visibility = q.get("visibility", "everyone")
                    anonymous = q.get("anonymous", "noone")
                    question_key, question_node, question_payload = create_discussion_question_data(
                        question_text=question_text,
                        response_visibility=visibility,
                        anonymous_to=anonymous,
                        points="0",
                        points_participation=points,
                    )
                elif question_type in ("equation", "formula"):
                    correct_answer = q.get("correct_answer", "")
                    if not correct_answer:
                        errors.append(f"Question {i}: equation needs 'correct_answer'")
                        continue
                    question_key, question_node, question_payload = create_equation_question_data(
                        question_text=question_text,
                        correct_answer=correct_answer,
                        points=points,
                    )
                else:
                    errors.append(f"Question {i}: unhandled type '{question_type}'")
                    continue

                # Add question node to content
                empty_para = {"type": "p", "id": generate_node_id(), "children": [{"text": ""}]}
                updated_content.append(question_node)
                updated_content.append(empty_para)

                # Add question data to create map
                new_questions[question_key] = question_payload

                added_questions.append({
                    "question_id": question_key,
                    "question_type": question_type,
                    "question_text": question_text,
                })

            except Exception as e:
                errors.append(f"Question {i}: {str(e)}")
                continue

        if not added_questions:
            raise ValueError(f"No valid questions to add. Errors: {errors}")

        # Build questions payload
        questions_payload = {
            "create": new_questions,
            "edit": {},
            "delete": [],
        }

        logger.info(f"Sending content with {len(updated_content)} nodes, adding {len(new_questions)} questions")

        # Update the chapter
        await client.put(
            f"/api/file/{chapter_id}",
            data={
                "content": updated_content,
                "questions": questions_payload,
            },
        )

        if ctx:
            await ctx.info(f"Added {len(added_questions)} questions successfully!")

        result = {
            "status": "success",
            "message": f"Added {len(added_questions)} questions to chapter",
            "chapter_id": chapter_id,
            "questions_added": added_questions,
        }

        if errors:
            result["warnings"] = errors

        return result

    except Exception as e:
        error_msg = f"Failed to add chapter questions: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)
