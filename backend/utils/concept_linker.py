from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def find_relevant_chunks(message, document_chunks, top_k=3):
    """
    Finds the most relevant chunks from document_chunks based on semantic similarity to the user message.

    Parameters:
    - message (str): The user's query or prompt.
    - document_chunks (List[Tuple[str, str]]): Each item is (chunk_text, filename)
    - top_k (int): Number of most relevant chunks to return.

    Returns:
    - List[Tuple[str, str]]: Top-k relevant chunks with filenames
    """
    texts = [chunk[0] for chunk in document_chunks]
    if not texts:
        return []

    vectorizer = TfidfVectorizer().fit([message] + texts)
    message_vec = vectorizer.transform([message])
    text_vecs = vectorizer.transform(texts)

    scores = cosine_similarity(message_vec, text_vecs)[0]
    top_indices = scores.argsort()[-top_k:][::-1]

    return [document_chunks[i] for i in top_indices if scores[i] > 0.1]


