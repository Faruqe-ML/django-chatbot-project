from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    streaming=True,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMA_ROOT = PROJECT_ROOT / "chroma_topics"

# Shared vector-store dictionary
STORES = {}