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

@app.get("/api/debug")
async def debug():
    """Debug endpoint to test API connections."""
    import os
    import httpx
    results = {}

    # Show ALL environment variables (names only for security)
    all_env_keys = list(os.environ.keys())
    results["all_env_keys"] = all_env_keys
    results["env_count"] = len(all_env_keys)
    
    # Check env vars
    pplx_key = os.environ.get("PERPLEXITY_API_KEY", "")
    ant_key = os.environ.get("ANTHROPIC_API_KEY", "")
    results["perplexity_key_set"] = bool(pplx_key) and len(pplx_key) > 10
    results["anthropic_key_set"] = bool(ant_key) and len(ant_key) > 10
    results["perplexity_key_prefix"] = pplx_key[:8] + "..." if pplx_key else "NOT SET"
    results["anthropic_key_prefix"] = ant_key[:8] + "..." if ant_key else "NOT SET"
    
    # Test Perplexity
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {pplx_key}", "Content-Type": "application/json"},
                json={"model": "sonar", "messages": [{"role": "user", "content": "test"}]}
            )
            results["perplexity_status"] = r.status_code
            results["perplexity_ok"] = r.status_code == 200
            if r.status_code != 200:
                results["perplexity_error"] = r.text[:300]
    except Exception as e:
        results["perplexity_ok"] = False
        results["perplexity_error"] = str(e)
    
    # Test Anthropic
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": ant_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]}
            )
            results["anthropic_status"] = r.status_code
            results["anthropic_ok"] = r.status_code == 200
            if r.status_code != 200:
                results["anthropic_error"] = r.text[:300]
    except Exception as e:
        results["anthropic_ok"] = False
        results["anthropic_error"] = str(e)
    
    return JSONResponse(content=results)
