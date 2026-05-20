from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from memory import FabMemory
import os
import json

app = FastAPI(title="Semiconductor Agent Memory Dashboard")
templates = Jinja2Templates(directory="templates")
memory_db = FabMemory()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, section_id: str = "PHOTO_LITHO_01"):
    # 從 VDB 撈出該 section 的所有記憶 (包含 raw_log 與 consolidated)
    results = await memory_db.fetch_all_memories(section_id)
    
    memories = []
    if results['documents']:
        for doc, meta in zip(results['documents'], results['metadatas']):
            mem_type = meta.get("type")
            parsed_content = doc
            
            # If the memory is consolidated, parse the JSON string so the template can bind it
            if mem_type == "consolidated":
                try:
                    parsed_content = json.loads(doc)
                except Exception:
                    pass
                    
            memories.append({
                "content": parsed_content,
                "timestamp": meta.get("timestamp"),
                "type": mem_type,
                "user_id": meta.get("user_id", "system")
            })
    
    # 按照時間排序 (由新到舊)
    memories.sort(key=lambda x: x['timestamp'] if x['timestamp'] else 0, reverse=True)

    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html", 
        context={
            "section_id": section_id,
            "memories": memories
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

