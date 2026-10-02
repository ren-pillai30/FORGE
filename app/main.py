from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Any, Dict
import uvicorn
from app.agent import get_agent

app = FastAPI(title="Forge Telemetry API")
agent_executor = get_agent()

# Define API data models
class ChatRequest(BaseModel):
    message: str

class ThoughtProcess(BaseModel):
    tool: str
    tool_input: Dict[str, Any]
    observation: str

class ChatResponse(BaseModel):
    final_response: str
    thoughts: List[ThoughtProcess]

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    result = agent_executor.invoke({"input": request.message})
    
    # Extract the agent's thought process and database observations
    thoughts = []
    if "intermediate_steps" in result:
        for action, observation in result["intermediate_steps"]:
            thoughts.append(ThoughtProcess(
                tool=action.tool,
                tool_input=action.tool_input,
                observation=str(observation)
            ))
            
    return ChatResponse(
        final_response=result.get("output", ""),
        thoughts=thoughts
    )

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
