"""
text_analyzer.py

Analyze article content using the OpenAI GPT-4o-mini model.

This module takes the structured article data from `article_extractor.py`
and returns a structured JSON-like dictionary with:
- summary
- sentiment
- key points
- estimated reading time
- token usage
- cost in USD
"""

# Standard library imports
import json  # For working with JSON strings (convert between str and dict)
import logging  # For logging info/warnings/errors
from typing import Any, Dict, Optional  # Type hints for better readability

# Third-party imports
# OpenAI Python SDK: used to call the OpenAI API
from openai import OpenAI

# Local imports
# We reuse the same API key pattern as in the Morning Update project
from config import API_KEY_OPENAI


# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
# Configure logging similar to article_extractor.py
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# OpenAI client setup
# ---------------------------------------------------------------------------
# Create a single OpenAI client instance for this module
# This follows the same pattern as morning_update/openai_client.py
client = OpenAI(api_key=API_KEY_OPENAI)


# ---------------------------------------------------------------------------
# Cost calculation
# ---------------------------------------------------------------------------
def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculate the cost in USD for using gpt-4o-mini.

    Pricing (given in the requirement):
    - $0.150 per 1M input (prompt) tokens
    - $0.600 per 1M output (completion) tokens

    Note: Token counts from the API are raw integers (e.g., 1234),
    so we convert to millions of tokens for the cost.
    """
    # Prices per 1,000,000 tokens
    input_price_per_million = 0.150
    output_price_per_million = 0.600

    # Convert token counts to "millions of tokens" by dividing by 1_000_000
    input_cost = (prompt_tokens / 1_000_000) * input_price_per_million
    output_cost = (completion_tokens / 1_000_000) * output_price_per_million

    total_cost = input_cost + output_cost
    return total_cost


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------
def analyze_article(article_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze article content using OpenAI GPT-4o-mini.

    Parameters:
        article_data: dict from article_extractor containing:
            - title
            - text
            - authors
            - publish_date
            - (and any other fields, but we mainly use title and text)

    Returns:
        A dictionary with the following structure:
        {
            'summary': '...',
            'sentiment': {...},
            'key_points': [...],
            'reading_time_minutes': int,
            'tokens_used': {'prompt': int, 'completion': int, 'total': int},
            'cost_usd': float,
            'success': True/False,
            'error': None or str
        }
    """
    # Prepare base result structure with default values
    result: Dict[str, Any] = {
        "summary": "",
        "sentiment": {
            "label": "",
            "confidence": 0.0,
        },
        "key_points": [],
        "reading_time_minutes": 0,
        "tokens_used": {
            "prompt": 0,
            "completion": 0,
            "total": 0,
        },
        "cost_usd": 0.0,
        "success": False,
        "error": None,
    }

    # Basic validation: we require at least some text
    title = article_data.get("title") or "Untitled article"
    text = article_data.get("text") or ""

    if not text.strip():
        # No article text to analyze
        msg = "Article text is empty. Cannot analyze."
        logger.error(msg)
        result["error"] = msg
        return result

    # -----------------------------------------------------------------------
    # Build system and user prompts
    # -----------------------------------------------------------------------
    # System prompt: tells the model how it should behave and what to output
    system_prompt = """
You are an AI assistant that analyzes news/articles.
You MUST respond with ONLY valid JSON. Do NOT include any explanations,
comments, or extra text outside of the JSON.

The JSON MUST have this exact structure:
{
  "summary": "3-5 sentence summary",
  "sentiment": {
    "label": "positive|neutral|negative",
    "confidence": 0.85
  },
  "key_points": ["point 1", "point 2", "point 3"],
  "reading_time_minutes": 5
}

Rules:
- "summary" should be 3-5 sentences describing the main ideas of the article.
- "sentiment.label" must be exactly one of: "positive", "neutral", "negative".
- "sentiment.confidence" must be a number between 0 and 1.
- "key_points" must be a JSON array of short bullet-point style strings.
- "reading_time_minutes" must be an integer estimate of reading time.
"""

    # User prompt: includes the article content and asks for analysis
    user_prompt = f"""
Analyze the following article and return ONLY the JSON object in the exact format
described in the system prompt. Do not wrap it in backticks and do not add
any explanation text.

Article title:
{title}

Article text:
{text}
"""

    try:
        logger.info("Calling OpenAI API for article analysis...")

        # Call the OpenAI Chat Completions API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            # Lower temperature for more consistent, deterministic output
            temperature=0.3,
        )

        # Extract token usage information from response
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage is not None else 0
        completion_tokens = usage.completion_tokens if usage is not None else 0
        total_tokens = prompt_tokens + completion_tokens

        # Store token usage in result
        result["tokens_used"] = {
            "prompt": prompt_tokens,
            "completion": completion_tokens,
            "total": total_tokens,
        }

        # Calculate cost
        result["cost_usd"] = calculate_cost(prompt_tokens, completion_tokens)

        # Extract the model's text output (should be a JSON string)
        content: Optional[str] = response.choices[0].message.content

        if not content:
            msg = "OpenAI response content is empty."
            logger.error(msg)
            result["error"] = msg
            return result

        # -------------------------------------------------------------------
        # Parse the JSON response from the model
        # -------------------------------------------------------------------
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as json_error:
            # Model did not return valid JSON
            msg = f"Failed to parse JSON from model response: {json_error}"
            logger.error(msg)
            result["error"] = msg
            return result

        # At this point, parsed should be a dict with the expected structure
        # We copy the fields we're interested in into the result
        result["summary"] = parsed.get("summary", "")
        result["sentiment"] = parsed.get(
            "sentiment",
            {"label": "", "confidence": 0.0},
        )
        result["key_points"] = parsed.get("key_points", [])
        result["reading_time_minutes"] = parsed.get("reading_time_minutes", 0)

        result["success"] = True
        result["error"] = None

        logger.info(
            "Article analysis completed successfully. "
            f"Tokens used: prompt={prompt_tokens}, completion={completion_tokens}, "
            f"cost=${result['cost_usd']:.6f}"
        )

        return result

    except Exception as e:
        # Catch any unexpected errors (network issues, API problems, etc.)
        error_msg = f"Error during article analysis: {str(e)}"
        logger.error(error_msg)
        result["error"] = error_msg
        result["success"] = False
        return result


# ---------------------------------------------------------------------------
# __main__ block for testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Simple manual test for analyze_article().

    You can run this file directly:
        python text_analyzer.py

    Or modify the sample_article below to test different inputs.
    """

    # Example article data similar to what article_extractor would produce
    sample_article = {
        "title": "AI Transforms News Analysis",
        "text": (
            "Artificial intelligence is increasingly being used to analyze news articles, "
            "summarize key points, and detect sentiment. This helps readers quickly "
            "understand complex topics and stay informed without reading full-length "
            "articles. However, it also raises questions about bias, transparency, and "
            "the role of human journalists in the future media landscape."
        ),
        "authors": ["Jane Doe"],
        "publish_date": "2026-01-27T10:00:00",
    }

    print("Testing analyze_article() with sample article data...")
    analysis_result = analyze_article(sample_article)

    print("\nAnalysis result:")
    print(json.dumps(analysis_result, indent=2))

