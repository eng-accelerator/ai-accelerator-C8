import csv
import json
import os
import pathlib
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None

BASE_DIR = pathlib.Path(__file__).resolve().parent


@dataclass
class TextChunk:
    source: str
    chunk_id: int
    text: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = None


def load_documents(directory: str) -> List[Dict[str, Any]]:
    """Load text-like documents from a local folder."""
    directory_path = pathlib.Path(directory)
    documents: List[Dict[str, Any]] = []

    for path in sorted(directory_path.glob("**/*")):
        if path.is_dir():
            continue

        suffix = path.suffix.lower()
        if suffix in {".txt", ".md", ".html", ".htm"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
        elif suffix == ".csv":
            text = _load_csv_as_text(path)
        elif suffix == ".json":
            text = _load_json_as_text(path)
        else:
            continue

        documents.append({"path": str(path), "text": text})

    return documents


def _load_csv_as_text(path: pathlib.Path) -> str:
    rows: List[str] = []
    with path.open(encoding="utf-8", errors="ignore", newline="") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            rows.append(" | ".join(row))
    return "\n".join(rows)


def _load_json_as_text(path: pathlib.Path) -> str:
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except json.JSONDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")

    if isinstance(payload, dict):
        return json.dumps(payload, indent=2)
    if isinstance(payload, list):
        return json.dumps(payload, indent=2)
    return str(payload)


def clean_text(text: str) -> str:
    """Normalize whitespace and remove control characters."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks for embedding and retrieval."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks: List[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks


def create_text_chunks(
    documents: List[Dict[str, Any]],
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[TextChunk]:
    """Convert each document to a list of text chunks."""
    chunks: List[TextChunk] = []
    for doc in documents:
        text = clean_text(doc["text"])
        for idx, chunk in enumerate(chunk_text(text, chunk_size=chunk_size, overlap=overlap)):
            chunks.append(
                TextChunk(
                    source=doc["path"],
                    chunk_id=idx,
                    text=chunk,
                    metadata={"source": doc["path"], "chunk_id": idx},
                )
            )
    return chunks


def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """Generate an embedding for a single text string."""
    if openai is None:
        raise RuntimeError(
            "The openai package is required to generate embeddings. Install it with `pip install openai`."
        )

    if not hasattr(openai, "Embedding") and not hasattr(openai, "embeddings"):
        raise RuntimeError("OpenAI client is not configured correctly.")

    client = getattr(openai, "OpenAI", openai)
    response = client.Embeddings.create(input=text, model=model)
    return response.data[0].embedding


def build_vector_index(chunks: List[TextChunk], model: str = "text-embedding-3-small") -> None:
    """Embed all chunks and attach embeddings in place."""
    for chunk in chunks:
        if chunk.embedding is None:
            chunk.embedding = get_embedding(chunk.text, model=model)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def retrieve_chunks(
    query: str,
    chunks: List[TextChunk],
    top_k: int = 5,
    model: str = "text-embedding-3-small",
) -> List[TextChunk]:
    """Retrieve the most relevant text chunks for a query."""
    query_embedding = get_embedding(query, model=model)
    scored: List[Tuple[float, TextChunk]] = []
    for chunk in chunks:
        if chunk.embedding is None:
            raise RuntimeError("All chunks must be embedded before retrieval.")
        score = cosine_similarity(query_embedding, chunk.embedding)
        scored.append((score, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:top_k]]


def build_prompt(question: str, retrieved_chunks: Iterable[TextChunk]) -> str:
    """Compose the final prompt for the LLM using retrieved context."""
    context = "\n\n".join(
        f"Source: {chunk.source}\nText: {chunk.text}" for chunk in retrieved_chunks
    )
    prompt = (
        "You are a helpful assistant. Answer the question using only the information provided in the context. "
        "If the answer is not present in the context, say 'I don't know.'\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    )
    return prompt


def generate_answer(
    prompt: str,
    model: str = "gpt-4.1-mini",
    max_tokens: int = 512,
    temperature: float = 0.0,
) -> str:
    """Invoke the LLM to answer a question using the composed prompt."""
    if openai is None:
        raise RuntimeError(
            "The openai package is required to generate completions. Install it with `pip install openai`."
        )

    client = getattr(openai, "OpenAI", openai)
    response = client.responses.create(
        model=model,
        input=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    if hasattr(response, "output"):
        if isinstance(response.output, list):
            return "\n".join(str(item.get("content", "")) for item in response.output)
        return str(response.output)
    return str(response)


def answer_query(
    question: str,
    chunks: List[TextChunk],
    retrieve_top_k: int = 5,
    embedding_model: str = "text-embedding-3-small",
    llm_model: str = "gpt-4.1-mini",
) -> Dict[str, Any]:
    """Run one full RAG query: retrieve relevant chunks and ask the LLM."""
    related = retrieve_chunks(question, chunks, top_k=retrieve_top_k, model=embedding_model)
    prompt = build_prompt(question, related)
    answer = generate_answer(prompt, model=llm_model)
    return {
        "question": question,
        "answer": answer,
        "sources": [chunk.source for chunk in related],
        "retrieved": [chunk.text for chunk in related],
    }


@lru_cache(maxsize=1)
def get_default_document_directory() -> str:
    return str(BASE_DIR)


if __name__ == "__main__":
    print("RAG pipeline example")
    document_dir = get_default_document_directory()
    docs = load_documents(document_dir)
    if not docs:
        raise SystemExit("No documents found in the current folder. Add .txt, .md, .csv, or .json files.")
    chunks = create_text_chunks(docs)
    build_vector_index(chunks)
    sample_question = "What is the grading scale?"
    result = answer_query(sample_question, chunks)
    print(json.dumps(result, indent=2))
