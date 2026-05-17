import asyncio
from agent import run_agent
from worker import sleep_update_consolidator

async def main():
    # 情境：黃光設備課，兩位工程師 Jason 與 Kevin 在同一區工作
    section_id = "PHOTO_LITHO_01"
    
    # 1. 工程師 Jason 處理 ASML_08 的 Overlay 偏移
    user_a = "eng_jason"
    equipment_data_a = {
        "tool_id": "SCANNER_ASML_08",
        "alarm_id": "ALID_204",
        "error_msg": "Overlay Offset Out of Range (X-axis)",
        "reading": "+15nm"
    }
    
    print(f"--- [User: {user_a}] 處理 ASML_08 異常 ---")
    response_a = await run_agent(
        user_a, 
        section_id, 
        equipment_data_a, 
        "ASML 08 發生 Overlay 偏移，我檢查了冷卻水溫發現異常偏高 (23.5C)，這可能是主因嗎？",
        "session_a_001"
    )
    print(f"Agent: {response_a}\n")
    
    # 2. 幾小時後，工程師 Kevin 接班，處理另一台機台 ASML_05
    user_b = "eng_kevin"
    equipment_data_b = {
        "tool_id": "SCANNER_ASML_05",
        "alarm_id": "ALID_204",
        "error_msg": "Overlay Offset Out of Range"
    }
    
    print(f"--- [User: {user_b}] 接班處理 ASML_05 異常 ---")
    response_b = await run_agent(
        user_b, 
        section_id, 
        equipment_data_b, 
        "我是 Kevin，ASML 05 也出現 Overlay 偏移，同課成員之前有處理過類似情況嗎？",
        "session_b_001"
    )
    print(f"Agent: {response_b}\n")

    print(">>> 暫停點：請開啟 Dashboard (http://127.0.0.1:8000) 觀察「原始日誌 (Raw Log)」")
    print(">>> 你會看到 Jason 與 Kevin 的對話已被記錄。")
    input("請按 Enter 鍵繼續，執行睡眠更新 (整合知識)...")

    # 3. 觸發睡眠更新 (將兩人的經驗整合為課室長期知識)
    print("\n--- 觸發睡眠更新 (整合 Jason 與 Kevin 的課室經驗) ---")
    await sleep_update_consolidator(section_id)

    print(">>> 觀察點：再次重新整理 Dashboard")
    print(">>> 你會發現原始日誌已消失，取而代之的是綠色的「已固化知識 (Consolidated)」卡片。")
    input("請按 Enter 鍵繼續，測試第三位工程師的檢索...")
    
    # 4. 第三位工程師 Mike 隔日上班
    user_c = "eng_mike"
    print(f"--- [User: {user_c}] 隔日上班查詢 ---")
    response_c = await run_agent(
        user_c, 
        section_id, 
        {}, 
        "總結一下昨天黃光 01 線關於 Overlay 偏移的處理經驗。",
        "session_c_001"
    )
    print(f"Agent: {response_c}\n")

if __name__ == "__main__":
    asyncio.run(main())
