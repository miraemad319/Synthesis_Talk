import logging
from typing import List, Tuple, Optional, Dict, Any
from functools import lru_cache
import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConceptLinker:
    """
    Enhanced concept linking with caching and better performance
    """
    
    def __init__(self, cache_size: int = 128):
        self.vectorizer_cache: Dict[str, TfidfVectorizer] = {}
        self.similarity_cache: Dict[str, np.ndarray] = {}
        self.cache_size = cache_size
        
    def _get_cache_key(self, texts: List[str]) -> str:
        """Generate a cache key for a list of texts"""
        combined = "|".join(sorted(texts))
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _get_or_create_vectorizer(self, texts: List[str]) -> TfidfVectorizer:
        """Get cached vectorizer or create new one"""
        cache_key = self._get_cache_key(texts)
        
        if cache_key in self.vectorizer_cache:
            return self.vectorizer_cache[cache_key]
        
        # Clean cache if it's getting too large
        if len(self.vectorizer_cache) >= self.cache_size:
            # Remove oldest entries (simple FIFO)
            oldest_key = next(iter(self.vectorizer_cache))
            del self.vectorizer_cache[oldest_key]
            if oldest_key in self.similarity_cache:
                del self.similarity_cache[oldest_key]
        
        # Create new vectorizer
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,  # Limit features for performance
            ngram_range=(1, 2),  # Include bigrams for better context
            min_df=1,  # Minimum document frequency
            max_df=0.95  # Maximum document frequency
        )
        
        try:
            vectorizer.fit(texts)
            self.vectorizer_cache[cache_key] = vectorizer
            logger.debug(f"Created new vectorizer with cache key: {cache_key[:8]}...")
        except Exception as e:
            logger.error(f"Failed to create vectorizer: {e}")
            raise
        
        return vectorizer
    
    def find_relevant_chunks(
        self,
        message: str,
        document_chunks: List[Tuple[str, str]],
        top_k: int = 3,
        min_threshold: float = 0.1,
        boost_exact_matches: bool = True
    ) -> List[Tuple[str, str, float]]:
        """
        Enhanced chunk finding with scoring and better relevance detection
        
        Args:
            message: User's query
            document_chunks: List of (chunk_text, filename) tuples
            top_k: Number of chunks to return
            min_threshold: Minimum similarity threshold
            boost_exact_matches: Whether to boost exact keyword matches
            
        Returns:
            List of (chunk_text, filename, similarity_score) tuples
        """
        if not message or not isinstance(message, str):
            logger.warning("Invalid message provided")
            return []
        
        if not document_chunks:
            logger.info("No document chunks provided")
            return []
        
        message = message.strip().lower()
        texts = [chunk_text for chunk_text, _ in document_chunks]
        
        try:
            # Get or create vectorizer
            vectorizer = self._get_or_create_vectorizer([message] + texts)
            
            # Transform texts
            message_vec = vectorizer.transform([message])
            text_vecs = vectorizer.transform(texts)
            
            # Compute cosine similarity
            scores = cosine_similarity(message_vec, text_vecs)[0]
            
            # Apply exact match boosting
            if boost_exact_matches:
                scores = self._apply_exact_match_boost(message, texts, scores)
            
            # Create scored results
            scored_chunks = [
                (document_chunks[i][0], document_chunks[i][1], float(scores[i]))
                for i in range(len(texts))
            ]
            
            # Sort by score (descending)
            scored_chunks.sort(key=lambda x: x[2], reverse=True)
            
            # Filter by threshold and return top_k
            above_threshold = [
                chunk for chunk in scored_chunks
                if chunk[2] >= min_threshold
            ]
            
            if above_threshold:
                result = above_threshold[:top_k]
                logger.info(f"Found {len(result)} chunks above threshold {min_threshold}")
            else:
                # Fallback to top scores even if below threshold
                result = scored_chunks[:top_k]
                logger.info(f"No chunks above threshold, returning top {len(result)} by score")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in find_relevant_chunks: {e}")
            # Return first few chunks as fallback
            return [
                (chunk_text, filename, 0.0)
                for chunk_text, filename in document_chunks[:top_k]
            ]
    
    def _apply_exact_match_boost(
        self, 
        message: str, 
        texts: List[str], 
        scores: np.ndarray,
        boost_factor: float = 0.2
    ) -> np.ndarray:
        """Apply boosting for exact keyword matches"""
        message_words = set(message.lower().split())
        boosted_scores = scores.copy()
        
        for i, text in enumerate(texts):
            text_words = set(text.lower().split())
            # Calculate overlap ratio
            overlap = len(message_words.intersection(text_words))
            if overlap > 0:
                overlap_ratio = overlap / len(message_words)
                boost = overlap_ratio * boost_factor
                boosted_scores[i] += boost
        
        return boosted_scores
    
    def get_semantic_clusters(
        self, 
        document_chunks: List[Tuple[str, str]], 
        n_clusters: int = 5
    ) -> Dict[int, List[Tuple[str, str]]]:
        """
        Group document chunks into semantic clusters
        
        Args:
            document_chunks: List of (chunk_text, filename) tuples
            n_clusters: Number of clusters to create
            
        Returns:
            Dictionary mapping cluster_id to list of chunks
        """
        if not document_chunks or len(document_chunks) < n_clusters:
            return {0: document_chunks}
        
        try:
            from sklearn.cluster import KMeans
            
            texts = [chunk_text for chunk_text, _ in document_chunks]
            vectorizer = self._get_or_create_vectorizer(texts)
            text_vecs = vectorizer.transform(texts)
            
            # Perform clustering
            kmeans = KMeans(n_clusters=min(n_clusters, len(texts)), random_state=42)
            cluster_labels = kmeans.fit_predict(text_vecs.toarray())
            
            # Group chunks by cluster
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(document_chunks[i])
            
            logger.info(f"Created {len(clusters)} semantic clusters")
            return clusters
            
        except ImportError:
            logger.warning("sklearn.cluster not available for clustering")
            return {0: document_chunks}
        except Exception as e:
            logger.error(f"Error in semantic clustering: {e}")
            return {0: document_chunks}
    
    def clear_cache(self):
        """Clear all caches"""
        self.vectorizer_cache.clear()
        self.similarity_cache.clear()
        logger.info("Cleared concept linker cache")

# Global instance for backward compatibility
_global_linker = ConceptLinker()

def find_relevant_chunks(
    message: str,
    document_chunks: List[Tuple[str, str]],
    top_k: int = 3,
    min_threshold: float = 0.1,
) -> List[Tuple[str, str]]:
    """
    Backward compatible function that returns (chunk_text, filename) tuples
    """
    results = _global_linker.find_relevant_chunks(
        message, document_chunks, top_k, min_threshold
    )
    # Convert back to old format (without scores)
    return [(chunk_text, filename) for chunk_text, filename, _ in results]

def find_relevant_chunks_with_scores(
    message: str,
    document_chunks: List[Tuple[str, str]],
    top_k: int = 3,
    min_threshold: float = 0.1,
) -> List[Tuple[str, str, float]]:
    """
    Enhanced function that returns similarity scores
    """
    return _global_linker.find_relevant_chunks(
        message, document_chunks, top_k, min_threshold
    )

def get_semantic_clusters(
    document_chunks: List[Tuple[str, str]], 
    n_clusters: int = 5
) -> Dict[int, List[Tuple[str, str]]]:
    """
    Group document chunks into semantic clusters
    """
    return _global_linker.get_semantic_clusters(document_chunks, n_clusters)

def clear_concept_cache():
    """Clear the global concept linker cache"""
    _global_linker.clear_cache()


