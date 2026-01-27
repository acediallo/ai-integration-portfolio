"""
main.py

Interactive CLI tool to:
- Extract article content from a URL
- Analyze the article with OpenAI (summary, sentiment, key points, reading time)
- Show human-readable results in the terminal
- Save full extraction + analysis data to a JSON file in outputs/
"""

import json  # For saving results as JSON
import logging  # For logging actions and errors
from datetime import datetime  # For timestamps in filenames and logs
from pathlib import Path  # For filesystem paths (outputs directory, files)
from typing import Dict, Any  # Type hints for dictionaries

from article_extractor import extract_article  # Our article extraction module
from text_analyzer import analyze_article  # Our article analysis module


# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def sanitize_filename(text: str) -> str:
    """
    Convert a title or arbitrary string into a safe filename.

    - Lowercase
    - Replace spaces and special characters with hyphens
    - Remove characters that are not alphanumeric, dash, or underscore
    """
    # Fallback in case text is empty
    if not text:
        return "article"

    # Normalize and replace spaces with hyphens
    cleaned = text.strip().lower().replace(" ", "-")

    # Keep only allowed characters (a-z, 0-9, dash, underscore)
    allowed_chars = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    cleaned = "".join(c for c in cleaned if c in allowed_chars)

    # Fallback if everything was removed
    return cleaned or "article"


def ensure_output_dir() -> Path:
    """
    Ensure that the outputs/ directory exists and return its Path.
    """
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    return output_dir


def display_results(article: Dict[str, Any], analysis: Dict[str, Any]) -> None:
    """
    Print human-readable analysis results to the console.
    Follows the format provided in the requirements.
    """
    title = article.get("title") or "Untitled article"
    authors = article.get("authors") or []
    publish_date = article.get("publish_date") or "Unknown"

    # Authors can be a list or string depending on extractor
    if isinstance(authors, list):
        authors_display = ", ".join(authors) if authors else "Unknown"
    else:
        authors_display = str(authors)

    summary = analysis.get("summary", "")
    sentiment = analysis.get("sentiment", {})
    sentiment_label = sentiment.get("label", "unknown")
    sentiment_confidence = sentiment.get("confidence", 0.0) * 100  # convert to %
    key_points = analysis.get("key_points", [])
    reading_time = analysis.get("reading_time_minutes", 0)

    tokens = analysis.get("tokens_used", {})
    prompt_tokens = tokens.get("prompt", 0)
    completion_tokens = tokens.get("completion", 0)
    total_tokens = tokens.get("total", 0)

    cost = analysis.get("cost_usd", 0.0)

    separator = "═" * 47
    sub_separator = "─" * 47

    print(separator)
    print("ARTICLE ANALYSIS RESULTS")
    print(separator)
    print(f"Title: {title}")
    print(f"Authors: {authors_display}")
    print(f"Published: {publish_date}")
    print("SUMMARY:")
    print(summary)
    print(f"SENTIMENT: {sentiment_label} (confidence: {sentiment_confidence:.2f}%)")
    print("KEY POINTS:")
    for point in key_points:
        print(f"• {point}")
    print(f"READING TIME: {reading_time} minutes")
    print(sub_separator)
    print("COST ANALYSIS")
    print(sub_separator)
    print(
        f"Tokens Used: {prompt_tokens} input + "
        f"{completion_tokens} output = {total_tokens} total"
    )
    print(f"Cost: ${cost:.6f} USD")
    print(separator)


def save_results_to_file(
    output_dir: Path,
    article: Dict[str, Any],
    analysis: Dict[str, Any],
) -> Path:
    """
    Save the combined article extraction + analysis data to a JSON file.

    Filename pattern:
        outputs/[sanitized-title]-[timestamp].json
    """
    title = article.get("title") or "article"
    safe_title = sanitize_filename(title)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{safe_title}-{timestamp}.json"

    output_path = output_dir / filename

    combined_data = {
        "article": article,
        "analysis": analysis,
        "saved_at": datetime.now().isoformat(),
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)

    logger.info(f"Results saved to: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Main interactive loop
# ---------------------------------------------------------------------------
def main() -> None:
    """
    Main interactive function:
    - Prompts user for a URL
    - Extracts and analyzes article
    - Displays results
    - Saves JSON output
    - Repeats until user exits
    """
    output_dir = ensure_output_dir()

    total_articles = 0
    total_cost = 0.0

    print("===============================================")
    print("AI Content Analyzer - Article Extraction & Analysis")
    print("Model: gpt-4o-mini | Temperature: 0.3")
    print("Press Ctrl+C at any time to exit.")
    print("===============================================")

    try:
        while True:
            url = input("\nEnter article URL (or 'q' to quit): ").strip()

            if not url:
                print("Please enter a non-empty URL.")
                continue

            if url.lower() in {"q", "quit", "exit"}:
                break

            logger.info(f"Starting analysis for URL: {url}")

            # ------------------------------------------------------------------
            # Article extraction
            # ------------------------------------------------------------------
            try:
                article = extract_article(url)
            except ValueError as ve:
                # Input validation error from extractor
                logger.error(f"Invalid URL: {ve}")
                print(f"Error: {ve}")
                print("Please try again with a valid URL.")
                continue
            except Exception as e:
                # Unexpected extraction error
                logger.error(f"Unexpected error during extraction: {e}")
                print(f"Unexpected error during extraction: {e}")
                print("Please try again or use a different URL.")
                continue

            if not article.get("success", False):
                error_msg = article.get("error", "Unknown extraction error.")
                logger.error(f"Article extraction failed: {error_msg}")
                print(f"Article extraction failed: {error_msg}")
                print("Please try another URL.")
                continue

            # ------------------------------------------------------------------
            # Article analysis
            # ------------------------------------------------------------------
            analysis = analyze_article(article)

            if not analysis.get("success", False):
                error_msg = analysis.get("error", "Unknown analysis error.")
                logger.error(f"Article analysis failed: {error_msg}")
                print(f"Article analysis failed: {error_msg}")
                print("You can try another article.")
                continue

            # ------------------------------------------------------------------
            # Display and save results
            # ------------------------------------------------------------------
            display_results(article, analysis)

            output_path = save_results_to_file(output_dir, article, analysis)
            print(f"Results saved to: {output_path}")

            # Update session stats
            total_articles += 1
            total_cost += float(analysis.get("cost_usd", 0.0))

            # Ask user if they want to analyze another article
            again = input("\nAnalyze another article? (y/n): ").strip().lower()
            if again not in {"y", "yes"}:
                break

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\n\nKeyboard interrupt detected. Exiting...")
        logger.info("User interrupted the session with Ctrl+C.")

    # ----------------------------------------------------------------------
    # Session summary
    # ----------------------------------------------------------------------
    print("\n===============================================")
    print("Session Summary")
    print("===============================================")
    print(f"Articles analyzed: {total_articles}")
    print(f"Total cost: ${total_cost:.6f} USD")
    print("Thank you for using AI Content Analyzer!")
    print("Goodbye 👋")

    logger.info(
        f"Session ended. Articles analyzed: {total_articles}, "
        f"Total cost: ${total_cost:.6f}"
    )


if __name__ == "__main__":
    main()

