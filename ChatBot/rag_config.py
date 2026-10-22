
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    streaming=True,
)

# Embeddings used to search the Chroma vector database
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMA_ROOT = PROJECT_ROOT / "chroma_topics"

STORES = {}
