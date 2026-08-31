import os
import uuid
import atexit
from pydantic import BaseModel
from langchain_cohere import CohereEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient, models
from src import config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QDRANT_PATH = os.path.join(BASE_DIR, "qdrant_db")
COLLECTION_NAME = "rag_docs"

COHERE_MODEL = "embed-v4.0"
VECTOR_SIZE = 1536
DENSE_FIELD = "dense"
SPARSE_FIELD = "sparse"
SPARSE_MODEL = "Qdrant/bm25"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 200
DEFAULT_PDF_PATH = os.path.join(BASE_DIR, "data", "guide.pdf")


class IngestResult(BaseModel):
    status: str
    filename: str
    chunks: int


_embeddings = CohereEmbeddings(
    model=COHERE_MODEL,
    cohere_api_key=config.COHERE_API_KEY,
)

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

    texts = [c.page_content.strip() for c in chunks]
    dense_vectors = _embeddings.embed_documents(texts)

    points = []
    for i, (text, dense_vec, chunk) in enumerate(zip(texts, dense_vectors, chunks)):
        points.append(
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector={
                    DENSE_FIELD: dense_vec,
                    SPARSE_FIELD: models.Document(text=text, model=SPARSE_MODEL),
                },
                payload={
                    "text": text,
                    "filename": filename,
                    "chunk_index": i,
                    "page": chunk.metadata.get("page", 0),
                },
            )
        )

    _client.upload_points(
        collection_name=COLLECTION_NAME,
        points=points,
        batch_size=32,
    )

    return IngestResult(status="success", filename=filename, chunks=len(chunks))


if not _client.collection_exists(COLLECTION_NAME):
    _client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            DENSE_FIELD: models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE)
        },
        sparse_vectors_config={
            SPARSE_FIELD: models.SparseVectorParams()
        },
    )
    if os.path.exists(DEFAULT_PDF_PATH):
        ingest_pdf(DEFAULT_PDF_PATH)
elif _client.get_collection(COLLECTION_NAME).points_count == 0:
    if os.path.exists(DEFAULT_PDF_PATH):
        ingest_pdf(DEFAULT_PDF_PATH)


def retrieve_context(query: str, top_k: int = 3) -> str:
    query_dense = _embeddings.embed_query(query)

    results = _client.query_points(
        collection_name=COLLECTION_NAME,
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        prefetch=[
            models.Prefetch(query=query_dense, using=DENSE_FIELD, limit=top_k * 3),
            models.Prefetch(query=models.Document(text=query, model=SPARSE_MODEL), using=SPARSE_FIELD, limit=top_k * 3),
        ],
        limit=top_k,
        with_payload=True,
    ).points

    if not results:
        return "No relevant information found."

    return "\n\n".join(p.payload["text"] for p in results)
