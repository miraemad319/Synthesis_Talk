import nltk
from nltk.tokenize import sent_tokenize

def _ensure_nltk_data():
    """Ensure NLTK punkt tokenizer is available"""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        try:
            nltk.download("punkt", quiet=True)
            nltk.download("punkt_tab", quiet=True)  # For newer NLTK versions
        except Exception as e:
            print(f"Warning: Could not download NLTK data: {e}")
            return False
    return True

def _simple_sentence_split(text):
    """Fallback sentence splitting when NLTK is not available"""
    import re
    # Simple regex-based sentence splitting
    sentences = re.split(r'[.!?]+\s+', text)
    return [s.strip() for s in sentences if s.strip()]

# Split large text into smaller chunks, grouped by sentence
# max_tokens is an approximate max character count per chunk
def split_into_chunks(text, max_tokens=500):
    # Ensure NLTK data is available
    if _ensure_nltk_data():
        try:
            sentences = sent_tokenize(text)
        except Exception as e:
            print(f"Warning: NLTK tokenization failed: {e}, using fallback")
            sentences = _simple_sentence_split(text)
    else:
        sentences = _simple_sentence_split(text)
    
    chunks = []
    current_chunk = ""

    # Add sentences to a chunk until the size exceeds max_tokens
    for sent in sentences:
        if len(current_chunk) + len(sent) < max_tokens:
            current_chunk += " " + sent
        else:
            if current_chunk.strip():  # Only add non-empty chunks
                chunks.append(current_chunk.strip())
            current_chunk = sent

    # Add any leftover sentence(s) as a final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
