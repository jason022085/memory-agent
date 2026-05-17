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

    # 2. 構建整合 Prompt (採用半導體專家人格並使用繁體中文)
    prompt = f"""你是一位資深的半導體設備專家，專長於黃光、蝕刻與薄膜製程。
請分析以下來自多位工程師的原始設備事件日誌與互動紀錄。
執行以下任務：
1. RCA 模式提取：識別重複發生的故障徵兆、感測器異常或警報模式。
2. 操作精煉：總結不同使用者所採取的行動中，哪些 Tool Call 序列或維修步驟最為有效。
3. 知識固化：將這些碎片化的日誌轉化為一條具備長期指導價值、結構化的設備維護記憶條目。

[原始日誌內容]
{raw_content}

請輸出專業且簡潔的「固化知識記憶」：
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
