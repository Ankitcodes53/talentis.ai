# services/local_embeddings.py
"""
Local embedding generation using sentence-transformers
Fallback when OpenAI API key is not available
"""
import logging

logger = logging.getLogger(__name__)

# Initialize sentence transformer model (lazy loaded)
_model = None

def _get_model():
    """Lazy load the sentence transformer model"""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            # all-MiniLM-L6-v2: 384 dimensions, fast, good quality
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            logger.info(f"Loading local embedding model: {model_name}")
            _model = SentenceTransformer(model_name)
            logger.info("Local embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer model: {e}")
            raise
    return _model


def text_to_embedding(text: str):
    """
    Convert text to embedding vector using local sentence-transformers
    Returns list[float] with 384 dimensions
    """
    if not text or not text.strip():
        # Return zero vector for empty text
        return [0.0] * 384
    
    try:
        model = _get_model()
        # Truncate text to reasonable length
        text = text[:8000]
        # Generate embedding
        embedding = model.encode(text, convert_to_numpy=True)
        # Convert numpy array to list
        return embedding.tolist()
    except Exception as e:
        logger.exception(f"Error generating local embedding: {e}")
        # Return zero vector on error
        return [0.0] * 384


def get_embedding_dimension():
    """Return the dimension of embeddings from this model"""
    return 384
