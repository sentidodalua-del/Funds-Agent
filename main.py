from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from datetime import datetime
from pathlib import Path
from agent import run_daily_search
from database import init_db, get_all_opportunities, get_opportunity_by_id, get_stats
from consultancies import find_consultancies
from chat_advisor import chat

app = FastAPI(title="EU Funds Agent — Glamping Skies")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/opportunities")
async def list_opportunities(relevance: str = None, area: str = None):
    opportunities = get_all_opportunities(relevance_filter=relevance, area_filter=area)
    return JSONResponse(content=opportunities)

@app.get("/api/opportunities/{opp_id}")
async def get_opportunity(opp_id: int):
    opp = get_opportunity_by_id(opp_id)
    if not opp:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return JSONResponse(content=opp)

@app.get("/api/stats")
async def stats():
    return JSONResponse(content=get_stats())

@app.post("/api/run-search")
async def trigger_search(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_daily_search)
    return JSONResponse(content={"status": "Search started", "timestamp": datetime.now().isoformat()})

@app.get("/api/opportunities/{opp_id}/consultancies")
async def get_consultancies(opp_id: int):
    opp = get_opportunity_by_id(opp_id)
    if not opp:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    if isinstance(opp.get("proposed_budget"), str):
        try:
            opp["proposed_budget"] = json.loads(opp["proposed_budget"])
        except Exception:
            pass
    result = await find_consultancies(opp)
    return JSONResponse(content=result)

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    if not messages:
        return JSONResponse(status_code=400, content={"error": "No messages"})
    reply = await chat(messages)
    return JSONResponse(content={"reply": reply})

@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

from database import toggle_save, get_saved_opportunities, update_saved_notes

@app.post("/api/opportunities/{opp_id}/save")
async def save_opportunity(opp_id: int, request: Request):
    body = await request.json()
    notes = body.get("notes", None)
    result = toggle_save(opp_id, notes)
    return JSONResponse(content=result)

@app.get("/api/saved")
async def list_saved():
    return JSONResponse(content=get_saved_opportunities())

@app.post("/api/opportunities/{opp_id}/notes")
async def update_notes(opp_id: int, request: Request):
    body = await request.json()
    notes = body.get("notes", "")
    update_saved_notes(opp_id, notes)
    return JSONResponse(content={"status": "ok"})
