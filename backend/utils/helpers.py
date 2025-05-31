import re
import json
import hashlib
import datetime
from typing import List, Dict, Any, Optional, Union
from pathlib import Path


def extract_search_query(message: str) -> Optional[str]:
    """
    Extracts a search query from a user message if it starts with something like:
    'search: ...' or 'find: ...'

    Parameters:
    - message (str): The user's input message

    Returns:
    - str or None: The extracted search query if found, otherwise None
    """
    # Matches phrases like 'search: topic here' or 'find: topic here'
    pattern = r"(?:search|find)[:\-]\s*(.+)"
    match = re.search(pattern, message, re.IGNORECASE)
    
    if match:
        return match.group(1).strip()  # Return just the search term
    return None


def clean_text(text: str) -> str:
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.,!?;:\-\'\"()]', ' ', text)
    
    # Remove excessive punctuation
    text = re.sub(r'[.]{3,}', '...', text)
    text = re.sub(r'[!]{2,}', '!', text)
    text = re.sub(r'[?]{2,}', '?', text)
    
    return text.strip()


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix"""
    if len(text) <= max_length:
        return text
    
    # Try to cut at word boundary
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # If we can cut at word boundary without losing too much
        truncated = truncated[:last_space]
    
    return truncated + suffix


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text using simple frequency analysis"""
    if not text:
        return []
    
    # Clean and tokenize
    text = clean_text(text.lower())
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
        'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
        'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might',
        'this', 'that', 'these', 'those', 'can', 'did', 'not', 'you',
        'your', 'they', 'them', 'their', 'we', 'our', 'she', 'her',
        'he', 'his', 'him', 'it', 'its', 'my', 'me', 'am', 'an', 'a'
    }
    
    # Count word frequencies
    word_freq = {}
    for word in words:
        if word not in stop_words and len(word) >= 3:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:max_keywords]]


def generate_session_id() -> str:
    """Generate a unique session ID"""
    timestamp = datetime.datetime.now().isoformat()
    hash_input = f"{timestamp}_{datetime.datetime.now().microsecond}"
    return hashlib.md5(hash_input.encode()).hexdigest()[:16]


def validate_json_structure(data: Any, required_fields: List[str]) -> Dict[str, Any]:
    """Validate JSON data structure"""
    result = {"valid": True, "errors": [], "warnings": []}
    
    if not isinstance(data, dict):
        result["valid"] = False
        result["errors"].append("Data must be a JSON object")
        return result
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            result["valid"] = False
            result["errors"].append(f"Missing required field: {field}")
    
    return result


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)


def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system storage"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 255:
        name, ext = Path(filename).stem, Path(filename).suffix
        filename = name[:255-len(ext)] + ext
    
    return filename or "unnamed_file"


def detect_language(text: str) -> str:
    """Simple language detection based on common words"""
    if not text:
        return "unknown"
    
    text_lower = text.lower()
    
    # Simple heuristics based on common words
    english_indicators = ['the', 'and', 'or', 'is', 'are', 'was', 'were', 'have', 'has']
    spanish_indicators = ['el', 'la', 'y', 'o', 'es', 'son', 'fue', 'fueron', 'tiene', 'ha']
    french_indicators = ['le', 'la', 'et', 'ou', 'est', 'sont', 'était', 'étaient', 'avoir', 'a']
    
    english_count = sum(1 for word in english_indicators if f' {word} ' in f' {text_lower} ')
    spanish_count = sum(1 for word in spanish_indicators if f' {word} ' in f' {text_lower} ')
    french_count = sum(1 for word in french_indicators if f' {word} ' in f' {text_lower} ')
    
    if english_count >= spanish_count and english_count >= french_count:
        return "english"
    elif spanish_count >= french_count:
        return "spanish"
    elif french_count > 0:
        return "french"
    else:
        return "unknown"


def create_summary_stats(text: str) -> Dict[str, Any]:
    """Create basic statistics about text content"""
    if not text:
        return {
            "character_count": 0,
            "word_count": 0,
            "sentence_count": 0,
            "paragraph_count": 0,
            "avg_words_per_sentence": 0,
            "keywords": []
        }
    
    # Count characters
    char_count = len(text)
    
    # Count words
    words = re.findall(r'\b\w+\b', text)
    word_count = len(words)
    
    # Count sentences (approximate)
    sentences = re.split(r'[.!?]+', text)
    sentence_count = len([s for s in sentences if s.strip()])
    
    # Count paragraphs
    paragraphs = text.split('\n\n')
    paragraph_count = len([p for p in paragraphs if p.strip()])
    
    # Calculate average words per sentence
    avg_words_per_sentence = word_count / sentence_count if sentence_count > 0 else 0
    
    # Extract keywords
    keywords = extract_keywords(text, max_keywords=5)
    
    return {
        "character_count": char_count,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "paragraph_count": paragraph_count,
        "avg_words_per_sentence": round(avg_words_per_sentence, 2),
        "keywords": keywords,
        "estimated_reading_time": round(word_count / 200, 1)  # Assuming 200 WPM
    }


def is_question(text: str) -> bool:
    """Detect if text is likely a question"""
    if not text:
        return False
    
    text = text.strip()
    
    # Direct question indicators
    if text.endswith('?'):
        return True
    
    # Question words at the beginning
    question_words = [
        'what', 'when', 'where', 'who', 'whom', 'whose', 'why', 'which', 
        'how', 'can', 'could', 'would', 'should', 'do', 'does', 'did',
        'is', 'are', 'was', 'were', 'will', 'shall', 'may', 'might'
    ]
    
    first_word = text.split()[0].lower() if text.split() else ""
    return first_word in question_words


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text"""
    if not text:
        return ""
    
    # Replace multiple whitespace characters with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Normalize line endings
    text = re.sub(r'\r\n|\r|\n', '\n', text)
    
    # Remove trailing whitespace from lines
    lines = text.split('\n')
    lines = [line.rstrip() for line in lines]
    
    return '\n'.join(lines).strip()
