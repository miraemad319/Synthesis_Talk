# backend/utils/concept_linker.py

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def find_relevant_chunks(
    message: str,
    document_chunks: list[tuple[str, str]],
    top_k: int = 3,
    min_threshold: float = 0.0,
) -> list[tuple[str, str]]:
    """
    Finds up to top_k chunks from document_chunks that are most similar to the user message.
    - If no chunk has cosine similarity > min_threshold, we fall back to returning
      the top_k highest‐scoring chunks (even if their score < min_threshold), as long as
      there is at least one chunk in document_chunks.
    - This ensures the LLM always receives some document context if any chunks exist.

    Parameters:
    - message (str): The user's query or prompt.
    - document_chunks (List[Tuple[str, str]]): Each item is (chunk_text, filename).
    - top_k (int): Number of most relevant chunks to return.
    - min_threshold (float): Minimum cosine similarity to enforce. If all scores are below
      this threshold, we still return the top_k chunks by score. Default is 0.0.

    Returns:
    - List[Tuple[str, str]]: Up to top_k relevant (chunk_text, filename) pairs.
    """

    # Extract just the chunk texts into a list
    texts = [chunk_text for (chunk_text, _filename) in document_chunks]
    if not texts:
        # No document content at all
        return []

    # Build a TF‐IDF model on [message] + all chunk texts
    vectorizer = TfidfVectorizer(stop_words="english").fit([message] + texts)
    message_vec = vectorizer.transform([message])     # shape (1, n_features)
    text_vecs = vectorizer.transform(texts)           # shape (len(texts), n_features)

    # Compute cosine similarity between the message and each chunk
    scores = cosine_similarity(message_vec, text_vecs)[0]  # array of length len(texts)

    # Pair up each chunk with its score and original filename
    scored_chunks = [
        (scores[i], document_chunks[i][0], document_chunks[i][1])
        for i in range(len(texts))
    ]

    # Sort by descending similarity
    scored_chunks.sort(key=lambda x: x[0], reverse=True)

    # First, collect all chunks whose score >= min_threshold
    above_threshold = [
        (chunk_text, filename)
        for score, chunk_text, filename in scored_chunks
        if score >= min_threshold
    ]

    if above_threshold:
        # If we have at least one chunk above the threshold, return up to top_k of them
        return above_threshold[:top_k]

    # Otherwise, no chunk passed the threshold. Fall back to returning the top_k highest scores:
    fallback = [
        (chunk_text, filename)
        for score, chunk_text, filename in scored_chunks[:top_k]
    ]
    return fallback



