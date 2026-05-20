import asyncio
import os
import shutil
import json
from agent import run_agent
from worker import sleep_update_consolidator
from memory import FabMemory

async def test_shared_memory_lifecycle():
    print("=== 正在開始黃光設備課 [共享記憶] 整合與增量合併測試 ===")
    
    # 0. 清理測試資料庫
    db_path = "./chroma_db_test"
    os.environ["CHROMA_DB_PATH"] = db_path
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
    
    section_id = "SHARED_ZONE_001"
    memory_db = FabMemory(persist_directory=db_path)
    
    # 1. 工程師 A (Jason) 處理 Dose Energy 異常
    print("\n步驟 1: 工程師 A (Jason) 處理 Dose Energy 異常...")
    case_1_msg = "機台 LITH-SCA-04 發生 Dose Energy OOC Alarm，Dose baseline 似乎有飄移。"
    case_1_data = {
        "tool_id": "LITH-SCA-04",
        "investigation": "確認是 Laser gas 交換後，chamber 內的 pressure tuning 沒有達到最佳化。重新做 Laser calibration 後恢復。"
    }
    await run_agent("jason", section_id, case_1_data, case_1_msg, "thread_1")
    
    # 2. 工程師 B (Mike) 處理 PEB 溫度異常
    print("\n步驟 2: 工程師 B (Mike) 處理 PEB 溫度異常...")
    case_2_msg = "LITH-TRK-12 的 PEB CH3 溫度均勻度跑掉，導致 CD variation。"
    case_2_data = {
        "tool_id": "LITH-TRK-12",
        "result": "發現 Bake plate 的 Zone 4 溫度偏低，Heater resistance 阻值偏高，更換 Heater block 後恢復。"
    }
    await run_agent("mike", section_id, case_2_data, case_2_msg, "thread_2")

    # 3. 驗證共享檢索 (在整合前)
    print("\n步驟 3: 驗證跨使用者檢索 (Raw Logs)...")
    history = await memory_db.get_relevant_memory(section_id, "Dose Energy")
    print(f"檢索到的歷史:\n{history}")
    
    assert "jason" in history, "應該要在檢索結果中看到 jason 的操作紀錄"
    assert "Laser gas" in history, "應該要看到 Laser gas 相關描述"

    # 4. 執行第一次睡眠更新 (建立最初的 2 個獨立 SOP)
    print("\n步驟 4: 執行睡眠整合 (預期建立兩個獨立的 SOP)...")
    await sleep_update_consolidator(section_id)
    
    # 驗證長期記憶 (第一階段)
    consolidated_history = await memory_db.get_relevant_memory(section_id, "Heater block")
    print(f"\n第一階段整合後的長期記憶 (Formatted Markdown):\n{consolidated_history}")
    
    assert "[consolidated" in consolidated_history, "應存在整合後的長期記憶條目"
    assert "Heater" in consolidated_history or "阻值" in consolidated_history, "長期記憶應包含 Heater 或阻值等關鍵資訊"
    
    # 5. 工程師 C (Kevin) 回報同類的 Dose Energy 異常，加入新的調校手法
    print("\n步驟 5: 工程師 C (Kevin) 處理同一機台 Dose Energy 異常，提供額外手法...")
    case_3_msg = "LITH-SCA-04 Dose baseline 再次出現 OOC 飄移。本次追加清潔了 Suction Nozzle 並重新做 Pressure Tuning。"
    case_3_data = {
        "tool_id": "LITH-SCA-04",
        "detail": "Suction nozzle 表面有油污，用 IPA 清潔後，再重新將 chamber 內的 pressure 調整 5% 以最佳化。"
    }
    await run_agent("kevin", section_id, case_3_data, case_3_msg, "thread_3")

    # 6. 執行第二次睡眠更新 (增量合併測試)
    print("\n步驟 6: 執行第二次睡眠整合 (測試增量合併/Merge & Enrich)...")
    await sleep_update_consolidator(section_id)
    
    # 撈出所有的 consolidated 記憶，驗證是否增量合併
    all_cons = await memory_db.fetch_consolidated_memory(section_id)
    print(f"\n所有 Consolidated 資料庫內容:")
    for doc, doc_id in zip(all_cons['documents'], all_cons['ids']):
        print(f"ID: {doc_id} -> {doc}\n")
        
    # 驗證合併後的結構
    merged_history = await memory_db.get_relevant_memory(section_id, "Laser gas")
    print(f"合併/增量更新後的 Dose Energy 長期記憶:\n{merged_history}")
    
    # 應包含雙方的維修關鍵字以及工程師名單
    assert "jason" in merged_history, "合併後的貢獻者中應包含 jason"
    assert "kevin" in merged_history, "合併後的貢獻者中應包含 kevin"
    assert "nozzle" in merged_history.lower() or "suction" in merged_history.lower() or "ipa" in merged_history.lower(), "合併後的內容應包含 Kevin 提到的清潔手法 (nozzle / suction / ipa)"
    
    print("\n=== 黃光設備課 [共享記憶與增量合併] 測試成功完成！ ===")

if __name__ == "__main__":
    try:
        asyncio.run(test_shared_memory_lifecycle())
    except Exception as e:
        print(f"\n測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)

