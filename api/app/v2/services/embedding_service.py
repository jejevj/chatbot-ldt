"""
Embedding service — generate vector 384 dimensi menggunakan sentence-transformers
"""
import logging
from typing import List

logger = logging.getLogger(__name__)

_model = None


def get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Embedding model loaded: all-MiniLM-L6-v2")
        except ImportError:
            raise RuntimeError("Install sentence-transformers untuk fitur embedding")
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Encode list of texts → list of 384-dim vectors"""
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.tolist()


def embed_single(text: str) -> List[float]:
    return embed_texts([text])[0]
