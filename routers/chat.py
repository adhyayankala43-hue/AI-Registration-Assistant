"""
Exposes the AI chat interaction logic to the frontend.
"""
from datetime import datetime, timezone
from fastapi import APIRouter
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from schemas import ChatRequest
from database import load_database, save_database
from state import CHAT_HISTORY
from agent import llm_with_tools, llm, tools_by_name

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("/")
async def chat_endpoint(request: ChatRequest):
    if not llm_with_tools: return {"reply": "Service unavailable."}
    
    sid = request.student_id
    if sid not in CHAT_HISTORY:
        CHAT_HISTORY[sid] = [SystemMessage(content="You are a strict, helpful AI Registration Assistant.")]
    
    CHAT_HISTORY[sid].append(HumanMessage(content=request.message))
    
    try:
        ai_msg = await llm_with_tools.ainvoke(CHAT_HISTORY[sid])
        if ai_msg.tool_calls:
            tool_outputs = []
            for call in ai_msg.tool_calls:
                t_name = call.get("name")
                if t_name in tools_by_name:
                    res = tools_by_name[t_name].invoke(call.get("args"))
                    tool_outputs.append(f"Result: {res}")
            
            final_res = await llm.ainvoke(CHAT_HISTORY[sid] + [HumanMessage(content="\n".join(tool_outputs))])
            reply = final_res.content
        else:
            reply = ai_msg.content
            
        CHAT_HISTORY[sid].append(AIMessage(content=reply))
    except Exception as e:
        return {"reply": f"Error: {e}"}

    db = load_database()
    db["chat_logs"].append({"student_id": sid, "message": request.message, "reply": reply})
    save_database(db)
    return {"reply": reply}
