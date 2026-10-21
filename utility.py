import os
import time
from typing import TypedDict

from langchain_core.messages import HumanMessage

from pathlib import Path
import shutil
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from ChatBot.rag_config import CHROMA_ROOT, model, STORES
from ChatBot.prompt import ROUTER_PROMPT


class RAGState(TypedDict):
    question: str
    topic: str            # ← chosen by router
    context: str
    sources: list[str]
    answer: str
    summary: str
    key_points: list[str]


def build_pdf_store(topic_name: str, pdf: Path) -> Chroma:
    """Load one PDF and build its persistent Chroma vector store."""

    # 1. Validate the PDF
    if not pdf.exists() or pdf.suffix.lower() != ".pdf":
        raise FileNotFoundError(f"PDF not found: {pdf}")

    print(f"  📖 Loading {pdf.name}")

    # 2. Load PDF pages
    docs = PyMuPDFLoader(str(pdf)).load()

    # 3. Add metadata to every page
    for doc in docs:
        doc.metadata["book"] = pdf.stem
        doc.metadata["topic"] = topic_name

    # 4. Split pages into smaller chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(docs)
    print(f"  ✂️ {len(chunks)} chunks")

    if not chunks:
        raise ValueError(f"No text extracted from {pdf.name}")

    # 5. Define the persistent storage directory
    persist_dir = CHROMA_ROOT / topic_name

    # 6. Remove the previous index, if it exists
    if persist_dir.exists():
        print(f"  🗑️ Removing old index: {persist_dir}")
        shutil.rmtree(persist_dir)

    # 7. Create embeddings and save them in Chroma
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=topic_name,
        persist_directory=str(persist_dir),
    )

    print(f"  💾 Saved vector store: {persist_dir}")
    print(f"  ✅ Indexed {len(chunks)} chunks")

    return store

def detect_topic(pdf: Path) -> str:
    filename = pdf.stem.lower().replace("-", " ").replace("_", " ")

    if "machine learning" in filename:
        return "machine_learning"

    elif "deep learning" in filename:
        return "deep_learning"

    elif (
        "dsa" in filename
        or "data structures" in filename
        or "algorithms" in filename
    ):
        return "dsa"

    elif (
        "let us c" in filename
        or "c programming" in filename
        or "c language" in filename
        or filename.strip() == "c"
    ):
        return "c_programming"

    return "general"


def router_node(state: RAGState):
    """Choose the correct topic retriever using the LLM."""

    q = state["question"]

    print("\n========== ROUTER DEBUG ==========")
    print("Question received:", repr(q))

    prompt = ROUTER_PROMPT.format(question=q)

    resp = model.invoke([
        HumanMessage(content=prompt)
    ])

    print("Raw LLM response:", repr(resp.content))

    topic = (
        resp.content
        .strip()
        .lower()
        .strip('"')
        .strip("'")
        .strip()
    )

    print("Normalized topic:", repr(topic))

    topic_mapping = {
        "machine_learning": "ml",
        "deep_learning": "dl",
        "ml": "ml",
        "dl": "dl",
        "dsa": "dsa",
        "c": "c_programming",
        "c programming": "c_programming",
        "c_programming": "c_programming",
        "general": "general",
    }

    topic = topic_mapping.get(topic)

    valid_topics = {
        "ml", "dl", "dsa", "c_programming", "general"
    }

    if topic not in valid_topics:
        raise ValueError(
            f"Unexpected router output: {resp.content!r}"
        )


    return {"topic": topic}



def _retrieve_from_topic(state: RAGState, topic: str):
    """Retrieve relevant documents from the selected topic store."""

    # Map router labels to actual Chroma store keys
    store_mapping = {
        "ml": "machine_learning",
        "dl": "deep_learning",
        "dsa": "dsa",
        "c_programming": "c_programming",
        "general": "general",

        # Also support full topic names
        "machine_learning": "machine_learning",
        "deep_learning": "deep_learning",
    }

    if topic not in store_mapping:
        raise ValueError(f"Unknown topic: {topic}")

    store_key = store_mapping[topic]

    if store_key not in STORES:
        raise KeyError(
            f"Vector store '{store_key}' not found. "
            f"Available stores: {list(STORES.keys())}"
        )

    # Search for the five most relevant document chunks
    docs = STORES[store_key].similarity_search(
        state["question"],
        k=5
    )

    # Combine retrieved chunks into context
    context = "\n\n---\n\n".join(
        f"[{d.metadata.get('book', 'Unknown book')} | "
        f"Page {d.metadata.get('page', 'Unknown')}]\n"
        f"{d.page_content}"
        for d in docs
    )

    # Collect source book names
    sources = sorted({
        d.metadata.get("book", "Unknown book")
        for d in docs
    })

    print(f"📚 Retrieved {len(docs)} chunks from {store_key}")

    return {
        "context": context,
        "sources": sources
    }


# Individual retrieval nodes
def retrieve_ml(state: RAGState):
    return _retrieve_from_topic(state, "ml")


def retrieve_dl(state: RAGState):
    return _retrieve_from_topic(state, "dl")


def retrieve_dsa(state: RAGState):
    return _retrieve_from_topic(state, "dsa")


def retrieve_c_programming(state: RAGState):
    return _retrieve_from_topic(state, "c_programming")


def retrieve_general(state: RAGState):
    return _retrieve_from_topic(state, "general")

def answer_node(state: RAGState):
    prompt = f"""
You are a friendly teacher who explains technical topics
to beginners in very easy language.

Instructions:
- Explain the topic step by step.
- Use simple English and short sentences.
- Explain difficult words with simple examples.
- Use a real-life example whenever possible.
- Include formulas when helpful and explain each symbol.
- Use headings to organize the answer.
- Use retrieved context when relevant.
- If the user asks for code and the context explains the concept
  but contains no implementation, generate correct code using
  your programming knowledge.
- Never claim generated code came from the PDF unless it did.
- If the context is insufficient or irrelevant, answer using
  your general knowledge when appropriate.

Context:
{state.get('context', '')}

Question: {state['question']}
"""

    answer_parts = []

    for chunk in model.stream(
        [HumanMessage(content=prompt)]
    ):
        if isinstance(chunk.content, str) and chunk.content:
            print(chunk.content, end="", flush=True)
            answer_parts.append(chunk.content)
    time.sleep(0.05)
    print()  # Move to the next terminal line

    return {"answer": "".join(answer_parts)}


def summary_node(state: RAGState):
    prompt = f"""
You are a friendly teacher explaining a topic to a beginner.

Create a summary in 2-3 sentences using very easy English.

Instructions:
- Explain only the main idea.
- Use short and simple sentences.
- Avoid difficult technical words.
- If a technical word is necessary, explain it simply.
- Use ONLY the provided context.
- Do not add unsupported information.
- If the context does not contain enough information,
  say so honestly.

Context:
{state['context']}

Question: {state['question']}

Return only the summary.
"""
    response = model.invoke([HumanMessage(content=prompt)])
    return {"summary": response.content}



def key_points_node(state: RAGState):
    prompt = f"""
You are a friendly teacher explaining a topic to a beginner.

Create 4-6 important points using very easy English.

Instructions:
- Write one short, complete sentence per line.
- Do not use numbering or bullet symbols.
- Include only the most important information.
- Explain technical terms in simple language when necessary.
- Use ONLY the provided context.
- Do not repeat the same idea.
- If the context does not contain enough information,
  provide only the points supported by it.

Context:
{state['context']}

Question: {state['question']}

Return only the key points, one per line.
"""
    resp = model.invoke([HumanMessage(content=prompt)])

    points = [
        line.strip().lstrip("-•* ").strip()
        for line in resp.content.splitlines()
        if line.strip()
    ]

    return {"key_points": points}
# 3. Router selects exactly one retriever
def route_by_topic(state: RAGState) -> str:
    topic = state["topic"]
    return f"retrieve_{topic}"

