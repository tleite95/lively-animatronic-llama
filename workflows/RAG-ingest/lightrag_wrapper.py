import os
import yaml

config_yaml = {
    "artifacts": ".../artifacts/workflows/rag-ingest",
    "pdfs": ".../initial-wiki-ingest",
    "llm_binding": "ollama",
    "llm_host": "http://127.0.0.1:11434",
    "llm_model": "olmo-3.1:32b-think",
}

try:
    with open('config.yaml', 'r') as file:
        config_yaml = yaml.safe_load(file)
except:
    pass

# Storage host, not lightrag server host
# TODO: Move this to config.yaml too
HOST = "192.168.64.1"

MONGO_URI = f"mongodb://{HOST}:27017/"
MONGO_DATABASE = "LightRAG"

NEO4J_URI = f"neo4j://{HOST}:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "alpine"

QDRANT_URL = f"http://{HOST}:6333"

OLLAMA_HOST = f"http://{HOST}:11434"
OLLAMA_EMBED_MODEL = "nomic-embed-text"
OLLAMA_EMBED_DIM = 768

WORKING_DIR = "./rag_storage"


os.environ.setdefault("LLM_BINDING", config_yaml["llm_binding"])
os.environ.setdefault("LLM_BINDING_HOST", config_yaml["llm_host"])
os.environ.setdefault("LLM_MODEL", config_yaml["llm_model"])

try:
    api_key = config_yaml["llm_api_key"]
    os.environ.setdefault("LLM_BINDING_API_KEY", api_key)
except KeyError:
    pass

os.environ.setdefault("EMBEDDING_BINDING", "ollama")
os.environ.setdefault("EMBEDDING_BINDING_HOST", OLLAMA_HOST)
os.environ.setdefault("EMBEDDING_MODEL", OLLAMA_EMBED_MODEL)
os.environ.setdefault("EMBEDDING_DIM", OLLAMA_EMBED_DIM)
os.environ.setdefault("EMBEDDING_TOKEN_LIMIT", 8192)
os.environ.setdefault("WORKING_DIR", WORKING_DIR)

# LightRAG reads connection info from env vars
os.environ.setdefault("MONGO_URI", MONGO_URI)
os.environ.setdefault("MONGO_DATABASE", MONGO_DATABASE)
os.environ.setdefault("NEO4J_URI", NEO4J_URI)
os.environ.setdefault("NEO4J_USERNAME", NEO4J_USERNAME)
os.environ.setdefault("NEO4J_PASSWORD", NEO4J_PASSWORD)
os.environ.setdefault("QDRANT_URL", QDRANT_URL)

os.environ.setdefault("LIGHTRAG_KV_STORAGE", "MongoKVStorage")
os.environ.setdefault("LIGHTRAG_DOC_STATUS_STORAGE", "MongoDocStatusStorage")
os.environ.setdefault("LIGHTRAG_GRAPH_STORAGE", "Neo4JStorage")
os.environ.setdefault("LIGHTRAG_VECTOR_STORAGE", "QdrantVectorDBStorage")


# noqa: E402 means don't worry about the import not being at the top of the file (this is required since we need to set env vars before importing)
from lightrag import LightRAG, QueryParam  # noqa: E402
from lightrag.kg.shared_storage import initialize_pipeline_status  # noqa: E402
from lightrag.llm.ollama import ollama_embed  # noqa: E402
from lightrag.utils import EmbeddingFunc  # noqa: E402

from scripts.run import run_prompt

async def llm_model_func(
    prompt,
    system_prompt=None,
    history_messages=None,
    keyword_extraction=False,
**kwargs,
) -> str:
    run_prompt(prompt, "Plan")


async def embedding_func(texts: list[str]):
    return await ollama_embed(
        texts,
        embed_model=OLLAMA_EMBED_MODEL,
        host=OLLAMA_HOST,
    )


async def build_rag() -> LightRAG:
    if not os.path.exists(WORKING_DIR):
        os.makedirs(WORKING_DIR)

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_model_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=OLLAMA_EMBED_DIM,
            max_token_size=8192,
            func=embedding_func,
        ),
        kv_storage="MongoKVStorage",
        doc_status_storage="MongoDocStatusStorage",
        graph_storage="Neo4JStorage",
        vector_storage="QdrantVectorDBStorage",
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()
    return rag

_rag = None
async def get_lightrag():
    global _rag
    if _rag is None:
        _rag = await build_rag()
    return _rag

async def cleanup_lightrag():
    await _rag.finalize_storages()


# Server

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("lightrag.api.lightrag_server:app", host="127.0.0.1", port=9621, reload=False)
