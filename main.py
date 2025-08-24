from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Import the MCP server tools
from crewai_enterprise_server import kickoff_crew, get_crew_status

app = FastAPI(title="CrewAI FastAPI Wrapper", version="1.1.0")

# Jinja2 setup
templates = Jinja2Templates(directory="templates")

# Request model for API
class KickoffRequest(BaseModel):
    query: str
    paid_tool: str

# Combined workflow endpoint
@app.post("/run_workflow")
async def run_workflow(req: KickoffRequest):
    kickoff_result = await kickoff_crew({"query": req.query, "paid_tool": req.paid_tool})
    kickoff_id = kickoff_result.get("kickoff_id")

    if not kickoff_id:
        return {"error": "Kickoff failed", "details": kickoff_result}

    # Poll status
    for _ in range(20):
        status_result = await get_crew_status(kickoff_id)
        state = status_result.get("state")
        if state == "SUCCESS":
            try:
                return {"final_result": status_result["result"]}
            except Exception:
                return {"raw_result": status_result}
        await asyncio.sleep(2)

    return {"error": "Timeout: workflow did not complete in time"}

# Serve HTML frontend
@app.get("/frontend", response_class=HTMLResponse)
def serve_frontend(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
