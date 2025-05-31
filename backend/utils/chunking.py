import nltk
import re
import logging
from typing import List, Tuple
from nltk.tokenize import sent_tokenize

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _ensure_nltk_data() -> bool:
    """Ensure NLTK punkt tokenizer is available with comprehensive error handling"""
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('tokenizers/punkt_tab')
        return True
    except LookupError:
        try:
            logger.info("Downloading NLTK punkt tokenizer...")
            nltk.download("punkt", quiet=True)
            nltk.download("punkt_tab", quiet=True)  # For newer NLTK versions
            logger.info("NLTK tokenizer downloaded successfully")
            return True
        except Exception as e:
            logger.warning(f"Could not download NLTK data: {e}")
            return False

def _simple_sentence_split(text: str) -> List[str]:
    """Enhanced fallback sentence splitting when NLTK is not available"""
    if not text or not isinstance(text, str):
        return []
    
    # Enhanced regex patterns for better sentence detection
    patterns = [
        r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\!|\?)\s+(?=[A-Z])',  # Standard sentence endings
        r'(?<=\.)\s+(?=[A-Z])',  # Period followed by capital letter
        r'(?<=\!)\s+(?=[A-Z])',  # Exclamation followed by capital letter
        r'(?<=\?)\s+(?=[A-Z])',  # Question mark followed by capital letter
    ]
    
    # Try each pattern until we get reasonable results
    for pattern in patterns:
        try:
            sentences = re.split(pattern, text.strip())
            sentences = [s.strip() for s in sentences if s.strip()]
            if sentences:
                return sentences
        except Exception as e:
            logger.warning(f"Regex pattern failed: {e}")
            continue
    
    # Final fallback: split by periods and filter
    sentences = text.split('.')
    return [s.strip() + '.' for s in sentences if s.strip()]

def split_into_chunks(text: str, max_tokens: int = 500, min_chunk_size: int = 50) -> List[str]:
    """
    Enhanced text chunking with better error handling and optimization
    
    Args:
        text: Input text to chunk
        max_tokens: Approximate maximum characters per chunk
        min_chunk_size: Minimum chunk size to avoid tiny fragments
    
    Returns:
        List of text chunks
    """
    if not text or not isinstance(text, str):
        logger.warning("Invalid input text provided to chunking function")
        return []
    
    text = text.strip()
    if len(text) < min_chunk_size:
        return [text] if text else []
    
    # Try NLTK first, fallback to regex
    sentences = []
    if _ensure_nltk_data():
        try:
            sentences = sent_tokenize(text)
            logger.debug(f"NLTK tokenization successful: {len(sentences)} sentences")
        except Exception as e:
            logger.warning(f"NLTK tokenization failed: {e}, using fallback")
            sentences = _simple_sentence_split(text)
    else:
        sentences = _simple_sentence_split(text)
    
    if not sentences:
        # If sentence splitting completely fails, create chunks by character count
        return [text[i:i+max_tokens] for i in range(0, len(text), max_tokens)]
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Check if adding this sentence would exceed max_tokens
        potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
        
        if len(potential_chunk) <= max_tokens:
            current_chunk = potential_chunk
        else:
            # Save current chunk if it meets minimum size
            if current_chunk and len(current_chunk) >= min_chunk_size:
                chunks.append(current_chunk.strip())
            
            # Start new chunk with current sentence
            if len(sentence) > max_tokens:
                # Handle very long sentences by splitting them
                words = sentence.split()
                temp_chunk = ""
                for word in words:
                    if len(temp_chunk + " " + word) <= max_tokens:
                        temp_chunk = temp_chunk + " " + word if temp_chunk else word
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk.strip())
                        temp_chunk = word
                if temp_chunk:
                    current_chunk = temp_chunk
            else:
                current_chunk = sentence
    
    # Add final chunk if it exists and meets minimum size
    if current_chunk and len(current_chunk) >= min_chunk_size:
        chunks.append(current_chunk.strip())
    elif current_chunk and chunks:
        # If final chunk is too small but we have other chunks, append to last chunk
        chunks[-1] += " " + current_chunk
    elif current_chunk:
        # If it's the only chunk, keep it regardless of size
        chunks.append(current_chunk.strip())
    
    logger.info(f"Text chunking complete: {len(chunks)} chunks created")
    return chunks

def get_chunk_metadata(chunks: List[str]) -> List[Tuple[str, dict]]:
    """
    Get metadata for chunks including word count, character count, etc.
    
    Args:
        chunks: List of text chunks
        
    Returns:
        List of tuples (chunk_text, metadata_dict)
    """
    result = []
    for i, chunk in enumerate(chunks):
        metadata = {
            'chunk_id': i,
            'char_count': len(chunk),
            'word_count': len(chunk.split()),
            'sentence_count': len(sent_tokenize(chunk)) if _ensure_nltk_data() else chunk.count('.') + chunk.count('!') + chunk.count('?')
        }
        result.append((chunk, metadata))
    
    return result
