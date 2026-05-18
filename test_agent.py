import asyncio
import os
import shutil
from agent import run_agent
from worker import sleep_update_consolidator
from memory import FabMemory

async def test_shared_memory_lifecycle():
    print("=== 正在開始黃光設備課 [共享記憶] 整合測試 (新測資) ===")
    
    # 0. 清理測試資料庫
    db_path = "./chroma_db_test"
    os.environ["CHROMA_DB_PATH"] = db_path
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
    
    section_id = "SHARED_ZONE_001"
    
    # 1. 工程師 A (Jason) 處理 LITH-SCA-04
    print("\n步驟 1: 工程師 A (Jason) 處理 Dose Energy 異常...")
    case_1_msg = "機台 LITH-SCA-04 發生 Dose Energy OOC Alarm，Dose baseline 似乎有飄移。"
    case_1_data = {
        "tool_id": "LITH-SCA-04",
        "investigation": "確認是 Laser gas 交換後，chamber 內的 pressure tuning 沒有達到最佳化。重新做 Laser calibration 後恢復。"
    }
    await run_agent("jason", section_id, case_1_data, case_1_msg, "thread_1")
    
    # 2. 工程師 B (Mike) 處理 LITH-TRK-12
    print("\n步驟 2: 工程師 B (Mike) 處理 PEB 溫度異常...")
    case_2_msg = "LITH-TRK-12 的 PEB CH3 溫度均勻度跑掉，導致 CD variation。"
    case_2_data = {
        "tool_id": "LITH-TRK-12",
        "result": "發現 Bake plate 的 Zone 4 溫度偏低，Heater resistance 阻值偏高，更換 Heater block 後恢復。"
    }
    await run_agent("mike", section_id, case_2_data, case_2_msg, "thread_2")

    # 3. 驗證共享檢索 (在整合前)
    print("\n步驟 3: 驗證跨使用者檢索 (Raw Logs)...")
    memory_db = FabMemory(persist_directory=db_path)
    history = await memory_db.get_relevant_memory(section_id, "Dose Energy")
    print(f"檢索到的歷史:\n{history}")
    
    assert "jason" in history, "應該要在檢索結果中看到 jason 的操作紀錄"
    assert "Laser gas" in history, "應該要看到 Laser gas 相關描述"

    # 4. 執行睡眠更新 (跨使用者整合)
    print("\n步驟 4: 執行跨使用者睡眠整合...")
    await sleep_update_consolidator(section_id)
    
    # 5. 驗證長期記憶 (Consolidated)
    print("\n步驟 5: 驗證固化後的長期記憶...")
    consolidated_history = await memory_db.get_relevant_memory(section_id, "Heater block")
    print(f"整合後的長期記憶:\n{consolidated_history}")
    
    assert "[consolidated" in consolidated_history, "應存在整合後的長期記憶條目"
    assert "Heater" in consolidated_history or "阻值" in consolidated_history, "長期記憶應包含 Heater 或阻值等關鍵資訊"
    
    print("\n=== 黃光設備課 [共享記憶] 測試成功完成 (New Data) ===")

if __name__ == "__main__":
    try:
        asyncio.run(test_shared_memory_lifecycle())
    except Exception as e:
        print(f"\n測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
