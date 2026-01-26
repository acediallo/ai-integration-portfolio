"""
Article Extractor Module
Extracts article content from URLs using newspaper3k library.
Handles messy HTML and extracts clean article text, title, and metadata.
"""

# newspaper3k library: Extracts and parses article content from web pages
# Article class is the main tool - it downloads HTML and extracts clean text
from newspaper import Article

# typing module: Provides type hints for better code documentation
# Dict[str, Optional[str]] means: a dictionary with string keys, values can be strings or None
# Optional[str] means: the value can be a string or None
from typing import Dict, Optional

# logging module: Records events/messages during program execution
# Useful for debugging and tracking what the program is doing
import logging

# requests library: Used by newspaper3k internally for HTTP requests
# We import it to catch timeout exceptions from network requests
import requests

# Exception types for timeout errors:
# - RequestsTimeout: When requests library times out
# - SocketTimeout: When socket connection times out  
# - TimeoutError: General Python timeout exception
# We rename them with 'as' to avoid naming conflicts
from requests.exceptions import Timeout as RequestsTimeout
from socket import timeout as SocketTimeout

# Configure logging: Set up how log messages are displayed
# level=logging.INFO means: show INFO, WARNING, and ERROR messages (not DEBUG)
logging.basicConfig(level=logging.INFO)

# Create a logger object for this specific module
# __name__ is a special variable that contains the module's name
# This helps identify which module logged the message
logger = logging.getLogger(__name__)


def extract_article(url: str, language: str = 'en') -> Dict[str, Optional[str]]:
    """
    Extract article content from a given URL.
    
    Function signature explanation:
    - url: str = parameter named 'url' that must be a string
    - language: str = 'en' = parameter with default value 'en' (English)
    - -> Dict[str, Optional[str]] = return type annotation (returns a dictionary)
    
    Args:
        url: The URL of the article to extract
        language: Language code for the article (default: 'en')
    
    Returns:
        Dictionary containing:
            - title: Article title
            - text: Main article text content
            - authors: List of authors (if available)
            - publish_date: Publication date (if available)
            - url: Original URL
            - success: Boolean indicating if extraction was successful
            - error: Error message if extraction failed
    
    Raises:
        ValueError: If URL is invalid or empty
        Exception: For network or parsing errors
    """
    # Input validation: Check if URL is empty or not a string
    # 'not url' checks for empty string, None, or False
    # isinstance(url, str) checks if url is actually a string type
    if not url or not isinstance(url, str):
        # raise: Stops execution and throws an error
        # ValueError: Specific exception type for invalid input values
        raise ValueError("URL must be a non-empty string")
    
    # Check if URL starts with http:// or https://
    # startswith() can take a tuple of strings to check multiple options
    # f"..." is an f-string: allows embedding variables in strings using {variable}
    if not url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid URL format: {url}. Must start with http:// or https://")
    
    # Initialize result dictionary with default values
    # None = Python's way of saying "no value" or "empty"
    # We'll fill these in if extraction succeeds
    result = {
        'title': None,
        'text': None,
        'authors': None,
        'publish_date': None,
        'url': url,  # Store the original URL
        'success': False,  # Start as False, set to True if successful
        'error': None  # Will contain error message if something goes wrong
    }
    
    # try/except block: Attempts code, catches errors if they occur
    # This prevents the program from crashing on errors
    try:
        # logger.info(): Logs an informational message (not an error)
        logger.info(f"Extracting article from: {url}")
        
        # Create Article object from newspaper3k library
        # This object will handle downloading and parsing the web page
        article = Article(url, language=language)
        
        # Download and parse the article with timeout handling
        # Nested try/except: Catches timeout errors specifically before general errors
        try:
            # article.download(): Downloads the HTML from the URL
            # timeout=15: If download takes more than 15 seconds, raise timeout error
            article.download(timeout=15)
        except (RequestsTimeout, SocketTimeout, TimeoutError) as timeout_error:
            # This catches multiple exception types in one block
            # The parentheses create a tuple of exception types to catch
            # 'as timeout_error' stores the exception object (we don't use it, but it's available)
            timeout_msg = f"Request timed out after 15 seconds while downloading from {url}"
            result['error'] = timeout_msg
            result['success'] = False
            logger.error(timeout_msg)  # logger.error(): Logs an error message
            return result  # Exit early - no point continuing if download failed
        
        # article.parse(): Analyzes the HTML and extracts article content
        # This removes ads, menus, and other non-article content
        article.parse()
        
        # Extract content from the parsed article object
        # These are attributes of the Article object set by parse()
        result['title'] = article.title
        result['text'] = article.text
        # Ternary operator: value_if_true if condition else value_if_false
        # If article.authors exists and is not empty, use it; otherwise use None
        result['authors'] = article.authors if article.authors else None
        # isoformat(): Converts datetime object to ISO format string (e.g., "2024-01-15T10:30:00")
        # We check if publish_date exists first to avoid errors
        result['publish_date'] = article.publish_date.isoformat() if article.publish_date else None
        result['success'] = True  # Mark as successful
        
        # Validate that we got meaningful content
        # .strip() removes whitespace from beginning/end of string
        # len() returns the length of the string
        if not result['text'] or len(result['text'].strip()) < 50:
            result['success'] = False
            result['error'] = "Extracted text is too short or empty. Article may not have been parsed correctly."
            logger.warning(f"Warning: {result['error']}")  # logger.warning(): Logs a warning
        else:
            logger.info(f"Successfully extracted article: '{result['title']}' ({len(result['text'])} characters)")
        
    except Exception as e:
        # Catches ANY exception not caught by the timeout handler above
        # 'as e' stores the exception object
        # str(e) converts the exception to a readable string message
        error_msg = f"Failed to extract article from {url}: {str(e)}"
        result['error'] = error_msg
        result['success'] = False
        logger.error(error_msg)
    
    return result


def extract_article_simple(url: str) -> Optional[str]:
    """
    Simple wrapper that returns just the article text.
    Useful for quick extraction when you only need the text content.
    
    Args:
        url: The URL of the article to extract
    
    Returns:
        Article text as string, or None if extraction failed
    """
    # Call the main extract_article function
    result = extract_article(url)
    
    # Check if extraction was successful
    if result['success']:
        # Return just the text content
        return result['text']
    else:
        # .get() method: Safely gets a dictionary value
        # .get('error', 'Unknown error') means: get 'error' key, or use 'Unknown error' if key doesn't exist
        # This prevents KeyError if 'error' key is missing
        logger.error(f"Extraction failed: {result.get('error', 'Unknown error')}")
        return None


# __name__ == "__main__": Special Python pattern
# When you run a file directly (python article_extractor.py), __name__ is set to "__main__"
# When you import the file (import article_extractor), __name__ is set to "article_extractor"
# This block only runs when the file is executed directly, not when imported
if __name__ == "__main__":
    # sys module: Provides access to system-specific parameters and functions
    # sys.argv: List of command-line arguments passed to the script
    # sys.argv[0] = script name, sys.argv[1] = first argument, etc.
    import sys
    
    # Check if user provided a URL as command-line argument
    # len(sys.argv) > 1 means: there's at least one argument (the URL)
    if len(sys.argv) > 1:
        test_url = sys.argv[1]  # Get the URL from command line
    else:
        # Default test URL - replace with a real article URL
        test_url = "https://fr.wikipedia.org/wiki/Blog"
        print("Usage: python article_extractor.py <article_url>")
        print(f"Testing with default URL: {test_url}\n")
    
    # String multiplication: "=" * 50 creates a string of 50 equal signs
    # Used for visual separator in output
    print("=" * 50)
    result = extract_article(test_url)
    
    if result['success']:
        print(f"✓ Success!")
        print(f"Title: {result['title']}")
        print(f"Text length: {len(result['text'])} characters")
        print(f"Authors: {result['authors']}")
        print(f"Publish date: {result['publish_date']}")
        # String slicing: result['text'][:200] gets first 200 characters
        # [:200] means: from start (index 0) to index 200 (exclusive)
        print(f"\nFirst 200 chars of text:\n{result['text'][:200]}...")
    else:
        print(f"✗ Failed: {result['error']}")
