"""
Agent Forge - Qdrant Ingestion Script

Ingests all Indian Family Law statutory acts into the Qdrant Cloud vector
database with dense multilingual embeddings + BM25 sparse vectors.

Usage:
    cd backend
    python scripts/ingest_to_qdrant.py

The script will:
1. Setup the Qdrant collection with hybrid vector config.
2. Fetch all Family Law acts from the Government API (if key provided)
   OR load from local PDF/text files in data/raw_acts/.
3. Chunk statutes at section level preserving legal hierarchy.
4. Compute Gemini multilingual embeddings.
5. Upload to Qdrant with rich metadata payload.
"""

import asyncio
import logging
import os
import sys
import re
import uuid
from typing import Iterator

# ── Setup path for local imports ──────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.core.config import get_settings
from app.rag.qdrant_client import get_qdrant_client, setup_collection, embed_query, DENSE_VECTOR_NAME, SPARSE_VECTOR_NAME
from app.rag.govt_api_client import fetch_full_act, FAMILY_LAW_ACTS

from qdrant_client import models as qdrant_models

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("ingest")
settings = get_settings()

BATCH_SIZE = 20          # Upload N points per batch to Qdrant
EMBEDDING_DIM = 768      # Gemini text-embedding-004 dimension


# ------------------------------------------------------------------ #
# BM25 Sparse Vectorizer (matches qdrant_client.py tokenizer)
# ------------------------------------------------------------------ #

def _bm25_tokenize(text: str) -> tuple[list[int], list[float]]:
    """Tokenizes text into unique, sorted sparse BM25 indices and values."""
    from collections import Counter
    text = text.lower()
    tokens = re.findall(r'\b[a-z0-9]+\b', text)
    if not tokens:
        return [0], [1.0]
    counts = Counter(tokens)
    total = sum(counts.values())

    # Map to hash modulo and aggregate duplicates
    sparse_map: dict[int, float] = {}
    for token, count in counts.items():
        idx = abs(hash(token)) % 100_000
        sparse_map[idx] = sparse_map.get(idx, 0.0) + (count / total)

    sorted_indices = sorted(sparse_map.keys())
    sorted_values = [sparse_map[i] for i in sorted_indices]
    return sorted_indices, sorted_values


# ------------------------------------------------------------------ #
# Section-Level Chunker
# ------------------------------------------------------------------ #

def chunk_sections(sections: list[dict]) -> Iterator[dict]:
    """
    Yields section-level chunks preserving legal hierarchy metadata.

    Each chunk contains:
    - act_name, section_number, section_title, chapter
    - content: Full section text (sub-sections, provisos, explanations)
    - source_url, domain, language
    """
    for section in sections:
        content = section.get("content", "").strip()
        if not content or len(content) < 30:
            continue  # Skip empty or trivial sections

        # For very long sections (>2000 chars), split into sub-chunks
        if len(content) > 2000:
            sub_chunks = _split_long_section(content)
            for i, sub_content in enumerate(sub_chunks):
                yield {
                    **section,
                    "content": sub_content,
                    "chunk_index": i,
                    "total_chunks": len(sub_chunks),
                }
        else:
            yield {**section, "chunk_index": 0, "total_chunks": 1}


def _split_long_section(text: str, max_chars: int = 1800) -> list[str]:
    """Splits a long section by sub-section markers, preserving legal meaning."""
    # Try to split on sub-section patterns: (1), (2), (a), (b)
    parts = re.split(r'(?=\(\d+\)|\([a-z]\))', text)
    chunks = []
    current = ""
    for part in parts:
        if len(current) + len(part) <= max_chars:
            current += part
        else:
            if current.strip():
                chunks.append(current.strip())
            current = part
    if current.strip():
        chunks.append(current.strip())
    return chunks if chunks else [text[:max_chars]]


# ------------------------------------------------------------------ #
# Qdrant Point Builder
# ------------------------------------------------------------------ #

async def build_qdrant_point(chunk: dict) -> qdrant_models.PointStruct:
    """Builds a Qdrant PointStruct with dense + sparse vectors and payload."""
    # Build the text to embed: combine title + content for richer semantic meaning
    embed_text = (
        f"{chunk.get('act_name', '')} "
        f"Section {chunk.get('section_number', '')} "
        f"{chunk.get('section_title', '')}. "
        f"{chunk.get('content', '')}"
    )

    # Dense embedding (Gemini multilingual)
    dense_vector = await embed_query(embed_text[:2000])  # Limit to avoid token overflow

    # Sparse BM25 vector
    sparse_indices, sparse_values = _bm25_tokenize(embed_text)

    payload = {
        "act_name": chunk.get("act_name", ""),
        "act_key": chunk.get("act_key", ""),
        "domain": chunk.get("domain", ""),
        "section_number": chunk.get("section_number", ""),
        "section_title": chunk.get("section_title", ""),
        "chapter": chunk.get("chapter", ""),
        "content": chunk.get("content", ""),
        "source_url": chunk.get("source_url", "https://indiacode.nic.in"),
        "language": chunk.get("language", "en"),
        "chunk_index": chunk.get("chunk_index", 0),
        "total_chunks": chunk.get("total_chunks", 1),
    }

    return qdrant_models.PointStruct(
        id=str(uuid.uuid4()),
        vector={
            DENSE_VECTOR_NAME: dense_vector,
            SPARSE_VECTOR_NAME: qdrant_models.SparseVector(
                indices=sparse_indices,
                values=sparse_values,
            ),
        },
        payload=payload,
    )


# ------------------------------------------------------------------ #
# Main Ingestion Flow
# ------------------------------------------------------------------ #

async def ingest_all_acts():
    """Fetches all Family Law acts and ingests them into Qdrant."""
    logger.info("=" * 60)
    logger.info("Agent Forge — Qdrant Ingestion Script")
    logger.info("=" * 60)

    # Step 1: Setup Qdrant collection
    setup_collection(embedding_dim=EMBEDDING_DIM)

    client = get_qdrant_client()
    total_ingested = 0

    # Step 2: Fetch and ingest each act
    for act_key, act_info in FAMILY_LAW_ACTS.items():
        logger.info(f"\n📚 Processing: {act_info['name']}")

        try:
            if settings.govt_legal_api_key:
                # Fetch from Government API
                sections = await fetch_full_act(act_key)
                logger.info(f"   Fetched {len(sections)} sections from Government API.")
            else:
                # Try to load from local files in data/raw_acts/
                local_file = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "data", "raw_acts", f"{act_key}.txt"
                )
                if os.path.exists(local_file):
                    sections = _load_from_text_file(local_file, act_info)
                    logger.info(f"   Loaded {len(sections)} sections from local file.")
                else:
                    logger.warning(
                        f"   ⚠️  No API key and no local file found for {act_key}. "
                        f"Place '{act_key}.txt' in data/raw_acts/ to ingest this act."
                    )
                    continue

        except Exception as e:
            logger.error(f"   ❌ Failed to fetch {act_key}: {e}")
            continue

        # Step 3: Chunk sections
        chunks = list(chunk_sections(sections))
        logger.info(f"   Chunked into {len(chunks)} segments.")

        # Step 4: Build points and upload in batches
        batch: list[qdrant_models.PointStruct] = []
        for i, chunk in enumerate(chunks):
            try:
                point = await build_qdrant_point(chunk)
                batch.append(point)

                if len(batch) >= BATCH_SIZE:
                    client.upsert(
                        collection_name=settings.qdrant_collection,
                        points=batch,
                    )
                    total_ingested += len(batch)
                    logger.info(
                        f"   Uploaded batch [{i - BATCH_SIZE + 2}–{i + 1}] | "
                        f"Total: {total_ingested}"
                    )
                    batch = []
                    # Brief pause to avoid rate-limiting
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"   Error processing chunk {i}: {e}")
                continue

        # Upload remaining batch
        if batch:
            client.upsert(
                collection_name=settings.qdrant_collection,
                points=batch,
            )
            total_ingested += len(batch)
            logger.info(f"   Final batch uploaded. Total for this act: {len(chunks)}")

        logger.info(f"   ✅ '{act_info['name']}' ingested successfully.")

    logger.info("\n" + "=" * 60)
    logger.info(f"✅ Ingestion Complete! Total points in Qdrant: {total_ingested}")
    logger.info(f"   Collection: {settings.qdrant_collection}")
    logger.info(f"   URL: {settings.qdrant_url}")
    logger.info("=" * 60)


def _load_from_text_file(filepath: str, act_info: dict) -> list[dict]:
    """
    Loads sections from a plain text file.
    Expected format: Each section starts with 'SECTION <number>.' or similar.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # Simple section splitter for plain text acts
    pattern = re.compile(
        r'(?:^|\n)(?:Section|SECTION|Sec\.)\s+(\d+[A-Za-z]?)[.\s–-]+([^\n]+)',
        re.MULTILINE
    )
    matches = list(pattern.finditer(text))

    sections = []
    for i, match in enumerate(matches):
        section_num = match.group(1).strip()
        section_title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()

        sections.append({
            "act_name": act_info["name"],
            "act_key": list(FAMILY_LAW_ACTS.keys())[list(FAMILY_LAW_ACTS.values()).index(act_info)],
            "domain": act_info["domain"],
            "section_number": section_num,
            "section_title": section_title,
            "chapter": "",
            "content": content,
            "source_url": "https://indiacode.nic.in",
            "language": "en",
        })

    return sections


if __name__ == "__main__":
    asyncio.run(ingest_all_acts())
