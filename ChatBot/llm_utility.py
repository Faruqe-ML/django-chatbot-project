import os
from pathlib import Path

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_chroma import Chroma

from ChatBot.rag_config import CHROMA_ROOT, model, STORES
from utility import (
    RAGState,
    detect_topic,
    build_pdf_store,
    router_node,
    retrieve_ml,
    retrieve_dl,
    retrieve_dsa,
    retrieve_c_programming,
    retrieve_general,
    route_by_topic,
    answer_node,
    summary_node,
    key_points_node,
)

load_dotenv()

# --------------------------------------------------
# 1. Locate the PDF directory
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BOOKS_DIR = PROJECT_ROOT / "books"

BOOKS_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_ROOT.mkdir(parents=True, exist_ok=True)


pdf_files = sorted(BOOKS_DIR.glob("*.pdf"))


STORES.clear()

for pdf in pdf_files:
    topic_name = detect_topic(pdf)

    # General PDFs are not indexed as topic-specific stores here.
    if topic_name == "general":

        continue

    try:
        store = build_pdf_store(topic_name, pdf)
        STORES[topic_name] = store

    except Exception as exc:
        print(f"Failed: {pdf.name}")
        print(f"Error: {exc}\n")


def retrieve_general_node(state: RAGState):
    """Use a general PDF store if available; otherwise use no context."""

    if "general" in STORES:
        return retrieve_general(state)

    return {
        "context": "",
        "sources": [],
    }


# --------------------------------------------------
# 4. Create the LangGraph workflow
# --------------------------------------------------

graph = StateGraph(RAGState)

graph.add_node("router", router_node)

graph.add_node("retrieve_ml", retrieve_ml)
graph.add_node("retrieve_dl", retrieve_dl)
graph.add_node("retrieve_dsa", retrieve_dsa)
graph.add_node("retrieve_c_programming", retrieve_c_programming)
graph.add_node("retrieve_general", retrieve_general_node)

graph.add_node("answer", answer_node)
graph.add_node("summary", summary_node)
graph.add_node("key_points", key_points_node)

# Start -> Router
graph.add_edge(START, "router")

# Router labels -> retrieval nodes
routing_map = {
    "retrieve_ml": "retrieve_ml",
    "retrieve_dl": "retrieve_dl",
    "retrieve_dsa": "retrieve_dsa",
    "retrieve_c_programming": "retrieve_c_programming",
    "retrieve_general": "retrieve_general",
}

graph.add_conditional_edges(
    "router",
    route_by_topic,
    routing_map,
)

# Retrieval -> Answer -> Summary -> Key points -> End
retrievers = [
    "retrieve_ml",
    "retrieve_dl",
    "retrieve_dsa",
    "retrieve_c_programming",
    "retrieve_general",
]

for retriever in retrievers:
    graph.add_edge(retriever, "answer")

graph.add_edge("answer", "summary")
graph.add_edge("summary", "key_points")
graph.add_edge("key_points", END)

# Compile the graph
app = graph.compile()



# --------------------------------------------------
# 5. Ask questions
# --------------------------------------------------

def ask(question: str):
    result = app.invoke({"question": question})

    return result

