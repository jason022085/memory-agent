import chromadb
from chromadb.utils import embedding_functions
import time
import os
from dotenv import load_dotenv

load_dotenv()

class FabMemory:
    def __init__(self, persist_directory=None):
        if persist_directory is None:
            persist_directory = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.client = chromadb.PersistentClient(path=persist_directory)
        # Using a default embedding function (can be replaced with Google/OpenAI embeddings)
        self.ef = embedding_functions.DefaultEmbeddingFunction()

    def _get_collection(self, section_id: str):
        # Shared memory within section: namespace = f"area_{section_id}"
        collection_name = f"area_{section_id}".replace("-", "_")
        return self.client.get_or_create_collection(
            name=collection_name, 
            embedding_function=self.ef
        )

    async def soft_update_log(self, user_id: str, section_id: str, content: str, metadata: dict):
        collection = self._get_collection(section_id)
        timestamp = int(time.time() * 1000)
        
        collection.add(
            documents=[content],
            metadatas=[{
                **metadata,
                "timestamp": timestamp,
                "type": "raw_log"
            }],
            ids=[f"log_{timestamp}"]
        )

    async def get_relevant_memory(self, section_id: str, query: str, n_results: int = 5):
        collection = self._get_collection(section_id)
        
        # Search for both consolidated and raw logs
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        
        if not results['documents']:
            return ""
        
        formatted_memories = []
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            mem_type = meta.get("type", "unknown")
            user = meta.get("user_id", "system")
            formatted_memories.append(f"[{mem_type} | User: {user}] {doc}")
            
        return "\n".join(formatted_memories)

    async def fetch_raw_logs(self, section_id: str):
        collection = self._get_collection(section_id)
        results = collection.get(where={"type": "raw_log"})
        return results

    async def fetch_consolidated_memory(self, section_id: str):
        collection = self._get_collection(section_id)
        results = collection.get(where={"type": "consolidated"})
        return results

    async def fetch_all_memories(self, section_id: str):
        collection = self._get_collection(section_id)
        # Fetching everything in the section
        results = collection.get()
        return results

    async def add_consolidated_memory(self, section_id: str, content: str):
        collection = self._get_collection(section_id)
        timestamp = int(time.time() * 1000)
        
        collection.add(
            documents=[content],
            metadatas=[{"timestamp": timestamp, "type": "consolidated"}],
            ids=[f"cons_{timestamp}"]
        )

    async def delete_logs(self, section_id: str, ids: list):
        if not ids:
            return
        collection = self._get_collection(section_id)
        collection.delete(ids=ids)
