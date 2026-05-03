from __future__ import annotations

import csv
import logging
import os
import re
from functools import lru_cache
from pathlib import Path

try:
    import numpy as np
except Exception as err:  # pragma: no cover - handled gracefully at runtime
    np = None
    NUMPY_IMPORT_ERROR: Exception | None = err
else:
    NUMPY_IMPORT_ERROR = None

try:
    import pandas as pd
except Exception as err:  # pragma: no cover - handled gracefully at runtime
    pd = None
    PANDAS_IMPORT_ERROR: Exception | None = err
else:
    PANDAS_IMPORT_ERROR = None

try:
    from openai import AzureOpenAI
except Exception as err:  # pragma: no cover - handled gracefully at runtime
    AzureOpenAI = None
    OPENAI_IMPORT_ERROR: Exception | None = err
else:
    OPENAI_IMPORT_ERROR = None

try:
    from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity
except Exception:  # pragma: no cover - NumPy fallback is used when sklearn is unavailable
    sklearn_cosine_similarity = None


logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
EMB_CSV = BASE_DIR / "embeddings" / "eduyou_embeddings_text-embedding-3-small.csv"
SOURCE_DOCS_CSV = BASE_DIR / "eduyou_cip_docs_for_embedding.csv"
TOP_K_DEFAULT = 5
MAX_CONTEXT_CHARS_DEFAULT = 5000

RAG_TRIGGER_PHRASES = (
    "major",
    "majors",
    "program",
    "programs",
    "field of study",
    "cip",
    "cip code",
    "career",
    "careers",
    "occupation",
    "occupations",
    "job",
    "jobs",
    "what can i do with",
    "salary by major",
    "earnings by major",
    "degree level",
    "associate degree",
    "associate's degree",
    "bachelor degree",
    "bachelor's degree",
    "master degree",
    "master's degree",
    "doctoral degree",
    "doctorate",
    "certificate",
    "diploma",
)

TEXT_COLUMN_CANDIDATES = ("text", "text_x", "text_y")
SOURCE_DOCS_COLUMNS = (
    "doc_id",
    "cip4",
    "degree_level",
    "cip_title",
    "median_earnings_4yr_nat",
    "text",
)
POLITICAL_TITLE_ALIASES = {
    "political science": (
        "political science and government",
    ),
    "politics": (
        "political science and government",
    ),
    "government": (
        "political science and government",
        "public administration",
    ),
    "public policy": (
        "public policy analysis",
        "public administration",
    ),
    "policy": (
        "public policy analysis",
    ),
    "public administration": (
        "public administration",
    ),
    "international relations": (
        "international relations and national security studies",
    ),
    "foreign policy": (
        "international relations and national security studies",
        "public policy analysis",
    ),
    "national security": (
        "international relations and national security studies",
    ),
}
RAG_FOCUS_STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "becoming",
    "best",
    "beyond",
    "by",
    "can",
    "career",
    "careers",
    "compare",
    "comparison",
    "degree",
    "degrees",
    "do",
    "field",
    "fields",
    "flexibility",
    "for",
    "from",
    "get",
    "good",
    "has",
    "have",
    "how",
    "i",
    "if",
    "in",
    "interested",
    "interest",
    "into",
    "is",
    "jobs",
    "just",
    "level",
    "levels",
    "like",
    "long",
    "major",
    "majors",
    "me",
    "my",
    "of",
    "or",
    "path",
    "paths",
    "program",
    "programs",
    "public",
    "salary",
    "science",
    "should",
    "strong",
    "student",
    "students",
    "term",
    "than",
    "that",
    "the",
    "them",
    "these",
    "they",
    "this",
    "those",
    "think",
    "top",
    "upside",
    "want",
    "what",
    "with",
}


def _normalize_phrase(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.casefold())).strip()


def _normalize_focus_token(token: str) -> str:
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("s") and len(token) > 4:
        return token[:-1]
    return token


def _tokenize_focus_terms(value: str) -> set[str]:
    tokens = set()
    for raw_token in re.findall(r"[a-z0-9]+", value.casefold()):
        token = _normalize_focus_token(raw_token)
        if len(token) < 3:
            continue
        if token in RAG_FOCUS_STOPWORDS:
            continue
        tokens.add(token)
    return tokens


def _require_dependencies() -> None:
    if NUMPY_IMPORT_ERROR is not None:
        raise RuntimeError(
            "RAG retrieval requires NumPy. Install the packages in requirements.txt."
        ) from NUMPY_IMPORT_ERROR
    if PANDAS_IMPORT_ERROR is not None:
        raise RuntimeError(
            "RAG retrieval requires pandas. Install the packages in requirements.txt."
        ) from PANDAS_IMPORT_ERROR
    if OPENAI_IMPORT_ERROR is not None:
        raise RuntimeError(
            "RAG retrieval requires the OpenAI package. Install the packages in requirements.txt."
        ) from OPENAI_IMPORT_ERROR


def _cosine_similarity(matrix: "np.ndarray", query_vector: "np.ndarray") -> "np.ndarray":
    if sklearn_cosine_similarity is not None:
        return sklearn_cosine_similarity(matrix, query_vector)

    matrix_norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    query_norms = np.linalg.norm(query_vector, axis=1, keepdims=True)
    safe_matrix = matrix / np.clip(matrix_norms, 1e-12, None)
    safe_query = query_vector / np.clip(query_norms, 1e-12, None)
    return safe_matrix @ safe_query.T


def _resolve_text_column(columns: list[str]) -> str:
    for candidate in TEXT_COLUMN_CANDIDATES:
        if candidate in columns:
            return candidate
    raise ValueError(
        "Embeddings CSV must contain a text column. Expected one of: "
        + ", ".join(TEXT_COLUMN_CANDIDATES)
    )


def _degree_priority(degree_level: str) -> int:
    order = {
        "Bachelor's Degree": 0,
        "Master's Degree": 1,
        "Associate's Degree": 2,
        "Graduate/Professional Certificate": 3,
        "Post-baccalaureate Certificate": 4,
        "Doctoral Degree": 5,
        "First Professional Degree": 6,
        "Undergraduate Certificate or Diploma": 7,
        "Non-Credential Program (Preparatory Coursework/Teacher Certification)": 8,
    }
    return order.get(str(degree_level), 99)


@lru_cache(maxsize=1)
def _load_embedding_assets() -> tuple["pd.DataFrame", str, "np.ndarray", tuple[str, ...]]:
    _require_dependencies()
    if not EMB_CSV.exists():
        raise FileNotFoundError(f"Embeddings file not found: {EMB_CSV}")

    embs = pd.read_csv(EMB_CSV)
    text_column = _resolve_text_column(embs.columns.tolist())
    embed_cols = tuple(column for column in embs.columns if column.startswith("dim_"))
    if not embed_cols:
        raise ValueError("No embedding dimensions were found in the embeddings CSV.")

    matrix = embs.loc[:, embed_cols].astype("float32").values
    return embs, text_column, matrix, embed_cols


@lru_cache(maxsize=1)
def _load_source_docs() -> tuple[dict[str, list[dict]], tuple[str, ...]]:
    if not SOURCE_DOCS_CSV.exists():
        raise FileNotFoundError(f"Source docs CSV not found: {SOURCE_DOCS_CSV}")

    grouped_rows: dict[str, list[dict]] = {}
    ordered_titles: list[str] = []
    with SOURCE_DOCS_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in SOURCE_DOCS_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(
                "Source docs CSV is missing required columns: " + ", ".join(missing)
            )

        for row in reader:
            cip_title = str(row.get("cip_title", "")).strip()
            text = str(row.get("text", "")).strip()
            if not cip_title or not text:
                continue

            normalized_title = _normalize_phrase(cip_title)
            record = {column: str(row.get(column, "")).strip() for column in SOURCE_DOCS_COLUMNS}
            record["normalized_title"] = normalized_title
            record["title_focus_tokens"] = _tokenize_focus_terms(normalized_title)
            grouped_rows.setdefault(normalized_title, []).append(record)
            if normalized_title not in ordered_titles:
                ordered_titles.append(normalized_title)

    return grouped_rows, tuple(ordered_titles)


@lru_cache(maxsize=1)
def _known_cip_titles() -> tuple[str, ...]:
    try:
        _, ordered_titles = _load_source_docs()
    except Exception:
        return ()
    return ordered_titles


def _embedding_model_name() -> str:
    return (
        os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        or os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")
        or "text-embedding-3-small"
    )


@lru_cache(maxsize=1)
def _get_client() -> "AzureOpenAI":
    _require_dependencies()

    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not api_key or not endpoint:
        raise RuntimeError(
            "Azure embedding credentials are missing. Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT."
        )

    return AzureOpenAI(
        api_key=api_key,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview"),
        azure_endpoint=endpoint,
    )


def looks_like_rag_question(question: str) -> bool:
    normalized_question = _normalize_phrase(question)
    if not normalized_question:
        return False

    if any(phrase in normalized_question for phrase in RAG_TRIGGER_PHRASES):
        return True

    return any(title and title in normalized_question for title in _known_cip_titles())


def is_rag_available() -> bool:
    try:
        _load_source_docs()
    except Exception:
        return False
    return True


def _extract_alias_title_targets(normalized_query: str) -> set[str]:
    targets = set()
    for phrase, aliased_titles in POLITICAL_TITLE_ALIASES.items():
        if phrase in normalized_query:
            targets.update(aliased_titles)
    return {_normalize_phrase(title) for title in targets if title}


def _retrieve_source_title_matches(query: str, top_k: int) -> list[dict]:
    normalized_query = _normalize_phrase(query)
    query_focus_tokens = _tokenize_focus_terms(normalized_query)
    grouped_rows, _ = _load_source_docs()
    alias_targets = _extract_alias_title_targets(normalized_query)

    ranked_titles: list[tuple[float, str]] = []
    for normalized_title, rows in grouped_rows.items():
        title_focus_tokens = rows[0]["title_focus_tokens"] if rows else set()
        overlap = len(query_focus_tokens & title_focus_tokens)
        phrase_hit = bool(normalized_title and normalized_title in normalized_query)
        alias_hit = normalized_title in alias_targets
        if not (alias_hit or phrase_hit or overlap > 0):
            continue

        score = float(overlap)
        if phrase_hit:
            score += 2.0
        if alias_hit:
            score += 1.5
        ranked_titles.append((score, normalized_title))

    if not ranked_titles:
        return []

    ranked_titles.sort(key=lambda item: (item[0], item[1]), reverse=True)
    selected_title_groups: list[list[dict]] = []
    for _, normalized_title in ranked_titles[: max(top_k, 6)]:
        rows = list(grouped_rows.get(normalized_title, []))
        rows.sort(
            key=lambda row: (
                _degree_priority(row.get("degree_level", "")),
                -float(row.get("median_earnings_4yr_nat") or 0),
            )
        )
        if rows:
            selected_title_groups.append(rows)

    matches: list[dict] = []
    group_index = 0
    while len(matches) < top_k and selected_title_groups:
        active_groups = 0
        for rows in selected_title_groups:
            if group_index >= len(rows):
                continue
            row = rows[group_index]
            matches.append(
                {
                    "doc_id": row.get("doc_id", ""),
                    "cip4": row.get("cip4", ""),
                    "degree_level": row.get("degree_level", ""),
                    "cip_title": row.get("cip_title", ""),
                    "median_earnings_4yr_nat": row.get("median_earnings_4yr_nat"),
                    "score": float(max(ranked_titles)[0]),
                    "text": row.get("text", ""),
                }
            )
            active_groups += 1
            if len(matches) >= top_k:
                break
        if active_groups == 0:
            break
        group_index += 1

    return matches


def retrieve_matches(query: str, top_k: int = TOP_K_DEFAULT) -> list[dict]:
    cleaned_query = str(query).strip()
    if not cleaned_query:
        return []

    top_k = max(1, int(top_k))

    try:
        source_matches = _retrieve_source_title_matches(cleaned_query, top_k=top_k)
    except Exception:
        logger.exception("Source-doc title retrieval failed.")
        source_matches = []
    if source_matches:
        return source_matches

    embs, text_column, matrix, _ = _load_embedding_assets()
    client = _get_client()
    response = client.embeddings.create(
        model=_embedding_model_name(),
        input=cleaned_query,
    )
    query_vector = np.array(response.data[0].embedding, dtype="float32").reshape(1, -1)
    similarities = _cosine_similarity(matrix, query_vector).flatten()

    top_k = min(top_k, len(embs))
    candidate_pool_size = max(top_k * 8, 24)
    candidate_pool_size = min(candidate_pool_size, len(embs))
    top_indices = np.argsort(similarities)[-candidate_pool_size:][::-1]

    normalized_query = _normalize_phrase(cleaned_query)
    query_focus_tokens = _tokenize_focus_terms(normalized_query)
    if not query_focus_tokens:
        logger.info("RAG retrieval suppressed for generic query without a field anchor: %r", cleaned_query)
        return []
    ranked_candidates = []

    for index in top_indices:
        row = embs.iloc[int(index)]
        cip_title = str(row.get("cip_title", ""))
        normalized_title = _normalize_phrase(cip_title)
        title_focus_tokens = _tokenize_focus_terms(normalized_title)
        title_phrase_hit = bool(normalized_title and normalized_title in normalized_query)
        focus_overlap = len(query_focus_tokens & title_focus_tokens)
        overlap_ratio = (
            focus_overlap / len(query_focus_tokens)
            if query_focus_tokens
            else 0.0
        )
        passes_focus_gate = (
            not query_focus_tokens
            or title_phrase_hit
            or focus_overlap >= 2
            or overlap_ratio >= 0.34
        )
        if not passes_focus_gate:
            continue

        rerank_score = float(similarities[int(index)]) + (0.06 * focus_overlap)
        if title_phrase_hit:
            rerank_score += 0.12

        ranked_candidates.append(
            (
                rerank_score,
                {
                    "doc_id": str(row.get("doc_id", "")),
                    "cip4": str(row.get("cip4", "")),
                    "degree_level": str(row.get("degree_level", "")),
                    "cip_title": cip_title,
                    "median_earnings_4yr_nat": row.get("median_earnings_4yr_nat"),
                    "score": float(similarities[int(index)]),
                    "text": str(row.get(text_column, "")).strip(),
                },
            )
        )

    if query_focus_tokens and not ranked_candidates:
        logger.info(
            "RAG retrieval suppressed for unsupported or weakly matched query=%r focus_tokens=%s",
            cleaned_query,
            sorted(query_focus_tokens),
        )
        return []

    ranked_candidates.sort(key=lambda item: item[0], reverse=True)
    return [candidate for _, candidate in ranked_candidates[:top_k]]


def retrieve_context(
    query: str,
    top_k: int = TOP_K_DEFAULT,
    max_context_chars: int = MAX_CONTEXT_CHARS_DEFAULT,
) -> dict:
    matches = retrieve_matches(query, top_k=top_k)
    context_chunks = []
    chars_used = 0

    for index, match in enumerate(matches, start=1):
        text = match["text"].strip()
        if not text:
            continue

        header = (
            f"Retrieved program context {index} | similarity {match['score']:.3f} | "
            f"CIP {match['cip4']} | {match['cip_title']} | {match['degree_level']}\n"
        )
        remaining_chars = max_context_chars - chars_used - len(header)
        if remaining_chars <= 0:
            break

        snippet = text[:remaining_chars].strip()
        if not snippet:
            continue

        context_chunks.append(header + snippet)
        chars_used += len(header) + len(snippet) + 2

    return {
        "context": "\n\n".join(context_chunks).strip(),
        "matches": matches,
    }
