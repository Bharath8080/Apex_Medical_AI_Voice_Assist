import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from loguru import logger
from pydantic import BaseModel

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "rag_docs"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 200


DEFAULT_PDF_PATH = os.path.join(BASE_DIR, "data", "guide.pdf")


class IngestResult(BaseModel):
    status: str
    filename: str
    chunks: int


# FastEmbed Embeddings, Text Splitter & Chroma Store
_embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-base-en-v1.5")
_vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=CHROMA_PATH,
    embedding_function=_embeddings,
)
_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ".", " "],
)


def ingest_pdf(file_path: str = DEFAULT_PDF_PATH, filename: str = "guide.pdf") -> IngestResult:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found at: {file_path}")

    logger.info(f"Loading PDF: {filename} from {file_path}...")
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    logger.info(f"  {len(pages)} pages loaded.")

    logger.info(f"Chunking (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
    chunks = _text_splitter.split_documents(pages)

    # Tag each chunk
    for i, chunk in enumerate(chunks):
        chunk.metadata["source"] = "guide"
        chunk.metadata["chunk_index"] = i
        chunk.metadata["filename"] = filename

    logger.info(f"  {len(chunks)} chunks produced.")
    logger.info(f"Storing in Chroma collection '{COLLECTION_NAME}'...")
    _vectorstore.add_documents(chunks)

    return IngestResult(
        status="success",
        filename=filename,
        chunks=len(chunks),
    )


def retrieve_context(query: str, top_k: int = 3) -> str:
    try:
        docs = _vectorstore.similarity_search(query, k=top_k)
        return "\n\n".join(d.page_content.strip() for d in docs) if docs else "No relevant information found."
    except Exception as e:
        logger.error(f"ChromaDB retrieval error: {e}")
        return "No relevant information found."


if __name__ == "__main__":
    res = ingest_pdf()
    print(f"Successfully ingested {res.chunks} chunks from {res.filename} into ChromaDB!")
    sample = retrieve_context("What are the visiting hours for ICU and General Wards?")
    print(f"\n[Verification Query - Visiting Hours]:\n{sample}")
