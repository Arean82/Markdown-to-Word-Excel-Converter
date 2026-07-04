# ==================================================================
# File: addons/md2docx-python-main/md2docx_python/src/docx2md_python.py
# Description: 
# ==================================================================

from docx import Document
import re


def word_to_markdown(word_file, markdown_file):
    """
    Convert a Word document to Markdown format

    Args:
        word_file (str): Path to the input Word document
        markdown_file (str): Path to the output Markdown file
    """
    # Open the Word document
    doc = Document(word_file)
    markdown_content = []

    for paragraph in doc.paragraphs:
        # Skip empty paragraphs
        if not paragraph.text.strip():
            continue

        # Get paragraph style
        style = paragraph.style.name.lower()

        # Handle code blocks
        if style.startswith("code block") or style.startswith("source code"):
            markdown_content.append(f"```\n{paragraph.text.strip()}\n```\n\n")
            continue

        # Handle headings
        if style.startswith("heading"):
            level = style[-1]  # Get heading level from style name
            markdown_content.append(f"{'#' * int(level)} {paragraph.text.strip()}\n")
            continue

        # Handle lists
        if style.startswith("list bullet"):
            markdown_content.append(f"* {paragraph.text.strip()}\n")
            continue
        if style.startswith("list number"):
            markdown_content.append(f"1. {paragraph.text.strip()}\n")
            continue

        # Handle regular paragraphs with formatting
        formatted_text = ""
        for run in paragraph.runs:
            text = run.text
            if text.strip():
                # Handle inline code (typically monospace font)
                if run.font.name in [
                    "Consolas",
                    "Courier New",
                    "Monaco",
                ] or style.startswith("code"):
                    if "\n" in text:
                        text = f"```\n{text}\n```"
                    else:
                        text = f"`{text}`"
                # Apply bold
                elif run.bold:
                    text = f"**{text}**"
                # Apply italic
                elif run.italic:
                    text = f"*{text}*"
                # Apply both bold and italic
                elif run.bold and run.italic:
                    text = f"***{text}***"
                formatted_text += text

        if formatted_text:
            markdown_content.append(f"{formatted_text}\n")

        # Add an extra newline after paragraphs
        markdown_content.append("\n")

    # Write to markdown file
    with open(markdown_file, "w", encoding="utf-8") as f:
        f.writelines(markdown_content)


def clean_markdown_text(text):
    """
    Clean and normalize markdown text

    Args:
        text (str): Text to clean

    Returns:
        str: Cleaned text
    """
    # Remove multiple spaces
    text = re.sub(r"\s+", " ", text)
    # Remove multiple newlines
    text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)
    return text.strip()
