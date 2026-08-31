import os
import uuid
import atexit
import warnings

os.environ["TRANSFORMERS_VERBOSITY"] = "error"
warnings.filterwarnings("ignore", category=DeprecationWarning)

from pydantic import BaseModel
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient, models

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QDRANT_PATH = os.path.join(BASE_DIR, "qdrant_db")
COLLECTION_NAME = "rag_docs"

DENSE_MODEL  = "BAAI/bge-base-en-v1.5"
SPARSE_MODEL = "Qdrant/bm25"
DENSE_FIELD  = "dense"
SPARSE_FIELD = "sparse"

CHUNK_SIZE    = 800
CHUNK_OVERLAP = 200
DEFAULT_PDF_PATH = os.path.join(BASE_DIR, "data", "guide.pdf")


class IngestResult(BaseModel):
    status: str
    filename: str
    chunks: int


_client = QdrantClient(path=QDRANT_PATH)
atexit.register(_client.close)

_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ".", " "],
)


def ingest_pdf(file_path: str = DEFAULT_PDF_PATH, filename: str = "guide.pdf") -> IngestResult:
    pages = PyPDFLoader(file_path).load()
    chunks = _text_splitter.split_documents(pages)

    vectors = []
    payloads = []
    ids = []

    for i, chunk in enumerate(chunks):
        text = chunk.page_content.strip()
        vectors.append({
            DENSE_FIELD:  models.Document(text=text, model=DENSE_MODEL),
            SPARSE_FIELD: models.Document(text=text, model=SPARSE_MODEL),
        })
        payloads.append({
            "text": text,
            "filename": filename,
            "chunk_index": i,
            "page": chunk.metadata.get("page", 0),
        })
        ids.append(str(uuid.uuid4()))

    _client.upload_collection(
        collection_name=COLLECTION_NAME,
        vectors=vectors,
        payload=payloads,
        ids=ids,
        batch_size=32,
    )

    return IngestResult(status="success", filename=filename, chunks=len(chunks))


if not _client.collection_exists(COLLECTION_NAME):
    _client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            DENSE_FIELD: models.VectorParams(
                size=_client.get_embedding_size(DENSE_MODEL),
                distance=models.Distance.COSINE,
            )
        },
        sparse_vectors_config={
            SPARSE_FIELD: models.SparseVectorParams(
                index=models.SparseIndexParams(on_disk=False)
            )
        },
    )
    if os.path.exists(DEFAULT_PDF_PATH):
        ingest_pdf(DEFAULT_PDF_PATH)
elif _client.get_collection(COLLECTION_NAME).points_count == 0:
    if os.path.exists(DEFAULT_PDF_PATH):
        ingest_pdf(DEFAULT_PDF_PATH)


def retrieve_context(query: str, top_k: int = 3) -> str:
    results = _client.query_points(
        collection_name=COLLECTION_NAME,
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        prefetch=[
            models.Prefetch(
                query=models.Document(text=query, model=DENSE_MODEL),
                using=DENSE_FIELD,
                limit=top_k * 3,
            ),
            models.Prefetch(
                query=models.Document(text=query, model=SPARSE_MODEL),
                using=SPARSE_FIELD,
                limit=top_k * 3,
            ),
        ],
        limit=top_k,
        with_payload=True,
    ).points

    if not results:
        return "No relevant information found."

    return "\n\n".join(p.payload["text"] for p in results)
