import operator
import time
import os
from typing import Annotated, TypedDict, List, Dict, Any
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from memory import FabMemory

load_dotenv()

# 1. Define State
class FabAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: str
    section_id: str
    equipment_data: Dict[str, Any]
    retrieved_history: str

# 2. Initialize Components
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))

# 3. Nodes
async def retrieval_node(state: FabAgentState):
    """Retrieves relevant history from VectorDB based on current context"""
    memory_db = FabMemory()
    last_message = state["messages"][-1].content if state["messages"] else ""
    query = f"{state['equipment_data']} {last_message}"
    
    history = await memory_db.get_relevant_memory(
        state["section_id"], 
        query
    )
    return {"retrieved_history": history}

async def diagnostic_agent_node(state: FabAgentState):
    """Performs diagnosis based on equipment data and retrieved history"""
    prompt = f"""你是一個半導體設備分析專家.
Current Area/Section: {state['section_id']}
User ID: {state['user_id']}

Past Knowledge & Logs:
{state['retrieved_history']}

Latest Equipment Data:
{state['equipment_data']}

分析以上資訊，提供專業的診斷建議和可能的解決方案。
請根據設備數據和過去的相關記錄，提出可能的問題原因。
"""
    # Create the message list for the LLM
    inputs = [HumanMessage(content=prompt)] + state["messages"]
    response = await llm.ainvoke(inputs)
    return {"messages": [response]}

async def soft_update_node(state: FabAgentState):
    """Intercepts and logs raw interaction logs (Soft Update)"""
    memory_db = FabMemory()
    recent_messages = state["messages"][-2:] # Capture this round's interaction
    
    for msg in recent_messages:
        log_entry = ""
        metadata = {
            "role": "unknown",
            "user_id": state["user_id"],
            "section_id": state["section_id"]
        }
        
        if isinstance(msg, AIMessage):
            log_entry = f"Agent Response: {msg.content}"
            metadata["role"] = "assistant"
            if msg.tool_calls:
                log_entry += f" | Tool Calls: {msg.tool_calls}"
        elif isinstance(msg, HumanMessage):
            log_entry = f"Engineer Input: {msg.content}"
            metadata["role"] = "user"
        elif isinstance(msg, ToolMessage):
            log_entry = f"Equipment Tool Output: {msg.content}"
            metadata["role"] = "tool"
            
        if log_entry:
            await memory_db.soft_update_log(
                state["user_id"], 
                state["section_id"], 
                log_entry, 
                metadata
            )
    return {}

# 4. Build Graph
workflow = StateGraph(FabAgentState)

workflow.add_node("retrieve", retrieval_node)
workflow.add_node("agent", diagnostic_agent_node)
workflow.add_node("soft_update", soft_update_node)

workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "agent")
workflow.add_edge("agent", "soft_update")
workflow.add_edge("soft_update", END)

# Compile with local memory checkpointer for session state
app = workflow.compile(checkpointer=MemorySaver())

async def run_agent(user_id: str, section_id: str, equipment_data: dict, user_message: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "user_id": user_id,
        "section_id": section_id,
        "equipment_data": equipment_data,
        "retrieved_history": ""
    }
    
    final_state = await app.ainvoke(initial_state, config=config)
    
    # Return the last AI response
    for msg in reversed(final_state["messages"]):
        if isinstance(msg, AIMessage):
            return msg.content
    
    return "No response generated."
