import chromadb
from chromadb.utils import embedding_functions
import time
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def format_json_to_markdown(json_str: str) -> str:
    """將結構化的 TroubleshootingSOP JSON 字串轉換為乾淨的 Markdown 區塊，以供 LLM 檢索讀取。"""
    try:
        data = json.loads(json_str)
        if isinstance(data, dict) and "alarm_id" in data and "root_cause" in data:
            last_updated_str = "未知"
            if "last_updated" in data:
                try:
                    last_updated_str = datetime.fromtimestamp(data["last_updated"] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    pass
            
            res_steps = "\n".join(f"  {i+1}. {step}" for i, step in enumerate(data.get("resolution_steps", [])))
            prev_actions = "\n".join(f"  - {act}" for act in data.get("preventive_actions", []))
            engineers = ", ".join(data.get("engineers_involved", []))
            sessions = ", ".join(data.get("session_references", []))
            
            md = (
                f"【系統固化標準作業程序 (SOP)】：[{data.get('alarm_id')}] (課別/區域: {data.get('process_area')})\n"
                f"--------------------------------------------------\n"
                f"- 可信度評級: {data.get('confidence_level', '未知')}\n"
                f"- 最後整合/更新時間: {last_updated_str}\n"
                f"\n"
                f"* 故障異常徵兆 (Symptom):\n  {data.get('symptom_description', '無資料')}\n\n"
                f"* 根本原因分析 (Physical Root Cause):\n  {data.get('root_cause', '無資料')}\n\n"
                f"* 標準作業處置步驟 (Verified SOP):\n{res_steps}\n\n"
                f"* 預防性維護對策 (Preventive Actions):\n{prev_actions}\n\n"
                f"* 貢獻工程師: {engineers}\n"
                f"* 關聯事件軌跡 (Reference Sessions): {sessions}\n"
                f"--------------------------------------------------"
            )
            return md
    except Exception:
        pass
    return json_str


class FabMemory:
    def __init__(self, persist_directory=None):
        if persist_directory is None:
            persist_directory = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.ef = embedding_functions.DefaultEmbeddingFunction()

    def _get_collection(self, section_id: str):
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
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        
        if not results['documents'] or not results['documents'][0]:
            return ""
        
        formatted_memories = []
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            mem_type = meta.get("type", "unknown")
            user = meta.get("user_id", "system")
            
            # If the memory is consolidated, format it from JSON to clean Markdown
            display_doc = doc
            if mem_type == "consolidated":
                display_doc = format_json_to_markdown(doc)
                
            formatted_memories.append(f"[{mem_type} | User: {user}] {display_doc}")
            
        return "\n".join(formatted_memories)

    async def search_similar_consolidated(self, section_id: str, query: str, n_results: int = 3):
        collection = self._get_collection(section_id)
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"type": "consolidated"}
        )
        
        memories = []
        if results['documents'] and results['documents'][0]:
            for doc, meta, doc_id in zip(results['documents'][0], results['metadatas'][0], results['ids'][0]):
                memories.append({
                    "id": doc_id,
                    "content": doc,
                    "metadata": meta
                })
        return memories

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

    async def update_consolidated_memory(self, section_id: str, memory_id: str, content: str):
        collection = self._get_collection(section_id)
        timestamp = int(time.time() * 1000)
        
        collection.update(
            ids=[memory_id],
            documents=[content],
            metadatas=[{"timestamp": timestamp, "type": "consolidated"}]
        )

    async def delete_logs(self, section_id: str, ids: list):
        if not ids:
            return
        collection = self._get_collection(section_id)
        collection.delete(ids=ids)

