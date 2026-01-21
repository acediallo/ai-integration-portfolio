"""
Article Extractor Module
Extracts article content from URLs using newspaper3k library.
Handles messy HTML and extracts clean article text, title, and metadata.
"""

from newspaper import Article
from typing import Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_article(url: str, language: str = 'en') -> Dict[str, Optional[str]]:
    """
    Extract article content from a given URL.
    
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
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")
    
    if not url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid URL format: {url}. Must start with http:// or https://")
    
    result = {
        'title': None,
        'text': None,
        'authors': None,
        'publish_date': None,
        'url': url,
        'success': False,
        'error': None
    }
    
    try:
        logger.info(f"Extracting article from: {url}")
        
        # Create Article object
        article = Article(url, language=language)
        
        # Download and parse the article
        article.download()
        article.parse()
        
        # Extract content
        result['title'] = article.title
        result['text'] = article.text
        result['authors'] = article.authors if article.authors else None
        result['publish_date'] = article.publish_date.isoformat() if article.publish_date else None
        result['success'] = True
        
        # Validate that we got meaningful content
        if not result['text'] or len(result['text'].strip()) < 50:
            result['success'] = False
            result['error'] = "Extracted text is too short or empty. Article may not have been parsed correctly."
            logger.warning(f"Warning: {result['error']}")
        else:
            logger.info(f"Successfully extracted article: '{result['title']}' ({len(result['text'])} characters)")
        
    except Exception as e:
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
    result = extract_article(url)
    if result['success']:
        return result['text']
    else:
        logger.error(f"Extraction failed: {result.get('error', 'Unknown error')}")
        return None


if __name__ == "__main__":
    # Test with a sample article URL
    import sys
    
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        # Default test URL - replace with a real article URL
        test_url = "https://fr.wikipedia.org/wiki/Blog"
        print("Usage: python article_extractor.py <article_url>")
        print(f"Testing with default URL: {test_url}\n")
    
    print("=" * 50)
    result = extract_article(test_url)
    
    if result['success']:
        print(f"✓ Success!")
        print(f"Title: {result['title']}")
        print(f"Text length: {len(result['text'])} characters")
        print(f"Authors: {result['authors']}")
        print(f"Publish date: {result['publish_date']}")
        print(f"\nFirst 200 chars of text:\n{result['text'][:200]}...")
    else:
        print(f"✗ Failed: {result['error']}")
