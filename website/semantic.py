import re
import numpy as np
from flask import current_app
from . import db
from .models import Event, EventChunk, GENRE_CHOICES

MODEL_NAME = 'all-MiniLM-L6-v2'
EMBEDDING_DIM = 384    # output size of MODEL_NAME; stored vectors of any other size are ignored
CHUNK_WORDS = 70        # target words per chunk (model truncates at 256 word-pieces)
MIN_SCORE = 0.30        # minimum cosine similarity to count as a match

_model = None
_matrix_cache = None    # (event_ids array, embedding matrix), rebuilt after any reindex


def get_model():
    # lazy load model for performance reasons
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(texts):
    return get_model().encode(texts, normalize_embeddings=True).astype(np.float32)


def build_chunks(event):
    genre_label = dict(GENRE_CHOICES).get(event.genre, event.genre)
    header = f'{event.title}. {genre_label}. {event.location}.'

    # Pack sentences into chunks
    sentences = [s for s in re.split(r'(?<=[.!?])\s+', event.description.strip()) if s]
    chunks, current, words = [], [], 0
    for sentence in sentences:
        n = len(sentence.split())
        if current and words + n > CHUNK_WORDS:
            chunks.append(current)
            current, words = current[-1:], len(current[-1].split())
        current.append(sentence)
        words += n
    if current:
        chunks.append(current)

    return [f'{header} {" ".join(c)}' for c in chunks] or [header]


def index_event(event):
    EventChunk.query.filter_by(event_id=event.id).delete()
    texts = build_chunks(event)
    for i, (text, vector) in enumerate(zip(texts, embed(texts))):
        db.session.add(EventChunk(event_id=event.id, chunk_index=i, text=text,
                                  embedding=vector.tobytes()))
    db.session.commit()
    global _matrix_cache
    _matrix_cache = None


def _load_matrix():
    global _matrix_cache
    if _matrix_cache is None:
        rows = EventChunk.query.with_entities(EventChunk.id, EventChunk.event_id, EventChunk.embedding).all()
        ids, vectors = [], []
        for chunk_id, event_id, blob in rows:
            # skip malformed rows so one bad embedding doesn't disable search for every event
            if not isinstance(blob, (bytes, bytearray)) or len(blob) != EMBEDDING_DIM * 4:
                current_app.logger.warning('Skipping chunk %s with invalid embedding', chunk_id)
                continue
            ids.append(event_id)
            vectors.append(np.frombuffer(blob, dtype=np.float32))
        if not vectors:
            return None
        _matrix_cache = (np.array(ids), np.vstack(vectors))
    return _matrix_cache


def warm_up():
    """Load the model and embedding matrix now so the first search isn't slow."""
    get_model()
    _load_matrix()


def semantic_search(query, limit=5):
    """Return [(event_id, score)] best-first; an event's score is its best chunk's score."""
    cached = _load_matrix()
    if cached is None:
        return []
    ids, matrix = cached
    scores = matrix @ embed([query])[0]
    best = {}
    for event_id, score in zip(ids.tolist(), scores.tolist()):
        if score >= MIN_SCORE and score > best.get(event_id, -1):
            best[event_id] = score
    return sorted(best.items(), key=lambda kv: kv[1], reverse=True)[:limit]
