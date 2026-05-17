import os
import asyncio
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from memory import FabMemory

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))
async def sleep_update_consolidator(section_id: str):
    """
    Background Worker: Extracts raw_logs and consolidates them into 
    long-term 'consolidated' memory.
    """
    memory_db = FabMemory()
    print(f"Starting Sleep Update for {section_id}...")
    
    # 1. Fetch raw logs
    logs = await memory_db.fetch_raw_logs(section_id)
    if not logs['documents']:
        print("No raw logs to consolidate.")
        return

    raw_content = "\n".join(logs['documents'])
    log_ids = logs['ids']

    # 2. Build Consolidation Prompt (Added multi-user context)
    prompt = f"""You are a Fab Memory Consolidation Engine.
Analyze the following raw equipment event logs and interactions from multiple engineers.
Perform the following:
1. RCA Pattern Extraction: Identify recurring failure symptoms or patterns.
2. Operation Refinement: Summarize which actions from different users were most effective.
3. Knowledge Solidification: Transform these fragmented logs into a high-value, 
   structured long-term maintenance memory entry for the entire section.

[RAW LOGS]
{raw_content}

Consolidated Memory:
"""

    # 3. Call LLM to reflect and consolidate
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    consolidated_mem = response.content

    # 4. Write consolidated memory & Prune old logs
    await memory_db.add_consolidated_memory(section_id, consolidated_mem)
    await memory_db.delete_logs(section_id, log_ids)
    
    print(f"SUCCESS: Consolidated {len(log_ids)} logs into long-term memory for {section_id}.")

if __name__ == "__main__":
    # Example manual trigger
    asyncio.run(sleep_update_consolidator("ETCH_LINE_01"))
