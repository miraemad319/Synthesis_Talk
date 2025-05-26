import nltk
from nltk.tokenize import sent_tokenize

# Ensure the punkt tokenizer is available for sentence splitting
nltk.download('punkt')

# Split large text into smaller chunks, grouped by sentence
# max_tokens is an approximate max character count per chunk
def split_into_chunks(text, max_tokens=500):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""

    # Add sentences to a chunk until the size exceeds max_tokens
    for sent in sentences:
        if len(current_chunk) + len(sent) < max_tokens:
            current_chunk += " " + sent
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sent

    # Add any leftover sentence(s) as a final chunk
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
