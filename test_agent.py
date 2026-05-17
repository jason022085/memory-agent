import asyncio
import os
import shutil
from agent import run_agent
from worker import sleep_update_consolidator
from memory import FabMemory

async def test_shared_memory_lifecycle():
    print("=== 正在開始黃光設備課 [共享記憶] 整合測試 ===")
    
    # 0. 清理測試資料庫
    db_path = "./chroma_db_test"
    os.environ["CHROMA_DB_PATH"] = db_path
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
    
    # 1. 工程師 A (Jason) 建立日誌
    print("\n步驟 1: 工程師 A (Jason) 處理異常...")
    section_id = "SHARED_ZONE_001"
    await run_agent("jason", section_id, {"tool": "ASML_01"}, "發現 ASML_01 雷射強度不穩，調整冷卻系統後恢復。", "thread_1")
    
    # 2. 工程師 B (Kevin) 查詢
    print("\n步驟 2: 工程師 B (Kevin) 應能存取 Jason 的經驗 (共享測試)...")
    memory_db = FabMemory(persist_directory=db_path)
    # 直接在 VDB 層級檢查
    history = await memory_db.get_relevant_memory(section_id, "雷射強度")
    print(f"Kevin 檢索到的歷史:\n{history}")
    
    assert "jason" in history, "Kevin 應該要在檢索結果中看到 jason 的操作紀錄"
    assert "調整冷卻系統" in history, "Kevin 應該要看到具體的解決方案"

    # 3. 睡眠更新 (跨使用者整合)
    print("\n步驟 3: 執行跨使用者睡眠整合...")
    await sleep_update_consolidator(section_id)
    
    # 4. 驗證長期記憶
    consolidated_history = await memory_db.get_relevant_memory(section_id, "雷射")
    print(f"整合後的長期記憶:\n{consolidated_history}")
    assert "[consolidated" in consolidated_history, "應存在整合後的長期記憶條目"
    
    print("\n=== 黃光設備課 [共享記憶] 測試成功完成 ===")

if __name__ == "__main__":
    try:
        asyncio.run(test_shared_memory_lifecycle())
    except Exception as e:
        print(f"\n測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
