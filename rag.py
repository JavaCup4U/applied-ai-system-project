from __future__ import annotations
import logging
import os
import re
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Common English suffixes to strip so "vaccinate" and "vaccination" both become "vaccin"
_SUFFIXES = ("ation", "ations", "ating", "ated", "ates", "ate", "ions", "ing", "ion", "ies", "ed", "ly", "al", "s")

def _stem(word: str) -> str:
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) > 3:
            return word[: -len(suffix)]
    return word

def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"\b[a-z]+\b", text.lower())
    return [_stem(t) for t in tokens if len(t) > 2 and t not in ENGLISH_STOP_WORDS]


class PetCareRetriever:
    """Searches the pet care knowledge base using TF-IDF cosine similarity."""

    def __init__(self, knowledge_dir: str = "knowledge_base"):
        self.chunks: List[str] = []
        self.sources: List[str] = []
        self.vectorizer = TfidfVectorizer(tokenizer=_tokenize, ngram_range=(1, 2), sublinear_tf=True)
        self.matrix = None
        self._load_and_chunk(knowledge_dir)
        if self.chunks:
            self.matrix = self.vectorizer.fit_transform(self.chunks)
        logger.info("RAG retriever loaded %d chunks from '%s'", len(self.chunks), knowledge_dir)

    def _load_and_chunk(self, knowledge_dir: str) -> None:
        if not os.path.isdir(knowledge_dir):
            logger.warning("Knowledge base directory not found: %s", knowledge_dir)
            return
        for fname in sorted(os.listdir(knowledge_dir)):
            if not fname.endswith(".txt"):
                continue
            path = os.path.join(knowledge_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            # Split by blank lines so each section (e.g. VACCINATION SCHEDULE)
            # becomes its own chunk instead of being mixed with unrelated content.
            sections = [s.strip() for s in text.split("\n\n") if s.strip()]
            for section in sections:
                # Skip title-only lines (no real content to search)
                if len(section.split()) < 8:
                    continue
                self.chunks.append(section)
                self.sources.append(fname)

    def search(self, query: str, top_k: int = 5) -> List[str]:
        """Return the top_k most relevant knowledge base chunks for the query."""
        if self.matrix is None or not query.strip():
            return []
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix).flatten()
        top_indices = scores.argsort()[::-1][:top_k]
        results = []
        for idx in top_indices:
            if scores[idx] > 0.01:
                results.append(f"[{self.sources[idx]}]\n{self.chunks[idx]}")
        logger.info("RAG search '%s' → %d results", query[:60], len(results))
        return results
