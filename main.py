import asyncio
from agent import run_agent
from worker import sleep_update_consolidator

async def main():
    # 情境：黃光設備課 (PHOTO_LITHO_01)
    section_id = "PHOTO_LITHO_01"
    
    # 定義 5 個詳細測資
    test_cases = [
        {
            "user_id": "eng_jason",
            "user_message": "機台 LITH-SCA-04 發生 Dose Energy OOC (Out of Control) Alarm。PE 抱怨近三天該機台的 Dose baseline 似乎有飄移 (Drifting)，跟一個月前的 Chart 比較，Average 掉了約 2%。",
            "equipment_data": {
                "tool_id": "LITH-SCA-04",
                "alarm_type": "Dose Energy OOC",
                "tool_investigation": "Check FDC chart 發現 Dose energy 確實在三天前的 PM 後出現 step change 下降。調閱機台 log，確認是 Laser gas 交換後，chamber 內的 pressure tuning 沒有達到最佳化。"
            }
        },
        {
            "user_id": "eng_kevin",
            "user_message": "LITH-SCA-09 跑出來的貨 Overlay 異常，且 Y 軸向的誤差特別大。檢查機台參數，發現 Wafer Stage 的 MSD (Moving Standard Deviation) 在 Y 軸方向的 peak 值偏高。",
            "equipment_data": {
                "tool_id": "LITH-SCA-09",
                "symptom": "Overlay Y-axis MSD peak high",
                "diagnostic_result": "Y 軸的 Air bearing (氣浮軸承) 壓力有異常波動。發現其中一條 Air tube 有微小破損導致漏氣，造成浮力不穩。"
            }
        },
        {
            "user_id": "eng_mike",
            "user_message": "黃光 CD (臨界尺寸) 變異度變大。ADC 抓到的 CD variation 高度集中在 LITH-TRK-12 的 PEB (Post Exposure Bake) Chamber 3。懷疑是 PEB 溫度均勻度 (Temp Uniformity) 跑掉。",
            "equipment_data": {
                "tool_id": "LITH-TRK-12",
                "issue": "CD variation in PEB CH3",
                "sensor_wafer_result": "Bake plate 的 Zone 4 (左下角) 溫度比 target 溫度低了 0.5度。檢查該 Zone 的 Heater resistance，發現阻值偏高，判定是 Heater 老化。"
            }
        },
        {
            "user_id": "eng_jason",
            "user_message": "LITH-TRK-05 的 Daily dummy particle count 呈現上升趨勢 (Trending up)。ADC 分類顯示多為水痕 (Watermark) 與圓形微粒，且集中在 Wafer Edge (邊緣)。",
            "equipment_data": {
                "tool_id": "LITH-TRK-05",
                "alarm": "Particle count trending up",
                "visual_inspection": "EBR nozzle 在關閉時，確實有微小液滴殘留並甩到 wafer 邊緣。調整 EBR nozzle 的 Suck-back pressure 參數並清潔 nozzle head。"
            }
        },
        {
            "user_id": "eng_kevin",
            "user_message": "LITH-TRK-02 剛做完季保養 (Quarterly PM)，更換了光阻幫浦 (Dispense Pump) 的 Filter。但 PM 後的 Qual wafer 一直過不了，光阻厚度 (Thickness) chart 出現雜訊，且表面疑似有微小氣泡。",
            "equipment_data": {
                "tool_id": "LITH-TRK-02",
                "status": "Post-PM Qual fail",
                "root_cause": "Purge 不完全導致管路內有空氣。學弟設定的 Purge count 只有 50 次，少於 SOP 規定的 100 次。"
            }
        }
    ]

    print(f"=== 開始 5 組設備異常處理模擬 (Section: {section_id}) ===\n")

    for i, case in enumerate(test_cases, 1):
        print(f"--- [案例 {i}] 使用者: {case['user_id']} ---")
        print(f"問題: {case['user_message']}")
        
        response = await run_agent(
            case['user_id'],
            section_id,
            case['equipment_data'],
            case['user_message'],
            f"session_case_{i}"
        )
        print(f"Agent 回應: {response}\n")

    print(">>> 暫停點：所有原始日誌已寫入。")
    input("請按 Enter 鍵繼續，執行睡眠更新 (整合 5 組案例知識)...")

    # 3. 觸發睡眠更新
    print("\n--- 觸發睡眠更新 (整合跨工程師的經驗) ---")
    await sleep_update_consolidator(section_id)

    print("\n>>> 觀察點：知識已固化。執行最終驗證查詢...")
    input("請按 Enter 鍵繼續，測試 Agent 的知識提取...")
    
    # 4. 驗證查詢
    query_user = "eng_manager"
    query_msg = "請總結近期關於 Scanner (SCA) 與 Track (TRK) 設備的主要異常事件與對策。"
    print(f"--- [驗證查詢] 使用者: {query_user} ---")
    print(f"查詢內容: {query_msg}")
    
    response_final = await run_agent(
        query_user, 
        section_id, 
        {}, 
        query_msg,
        "session_final_001"
    )
    print(f"Agent 總結回應: {response_final}\n")

if __name__ == "__main__":
    asyncio.run(main())
