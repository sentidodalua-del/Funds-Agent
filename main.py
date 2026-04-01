try:
    from config import ANTHROPIC_API_KEY as _ANT_KEY, PERPLEXITY_API_KEY as _PPLX_KEY
except ImportError:
    _ANT_KEY = ""
    _PPLX_KEY = ""

import os
os.environ.setdefault("ANTHROPIC_API_KEY", _ANT_KEY)
os.environ.setdefault("PERPLEXITY_API_KEY", _PPLX_KEY)

from fastapi import FastAPI, BackgroundTasks, Request
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

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Funds Agent · Glamping Skies</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #f8f6f1;
  --surface: #ffffff;
  --surface2: #f4f2ed;
  --border: rgba(0,0,0,0.08);
  --border2: rgba(0,0,0,0.14);
  --gold: #9a7b3a;
  --gold-light: #c9a55a;
  --gold-bg: #fdf8ef;
  --gold-border: rgba(154,123,58,0.25);
  --green: #2d7a5f;
  --green-bg: #eef7f3;
  --amber: #b5620a;
  --amber-bg: #fef5eb;
  --blue: #1e5a9c;
  --blue-bg: #eef3fb;
  --red: #c0392b;
  --text: #1a1a18;
  --text2: #5a5750;
  --text3: #9a9590;
  --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
  --shadow-lg: 0 8px 32px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.06);
}

* { margin:0; padding:0; box-sizing:border-box; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  min-height: 100vh;
}

/* HEADER */
header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0 28px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 1px 0 var(--border), 0 2px 8px rgba(0,0,0,0.03);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-mark {
  width: 32px;
  height: 32px;
  background: var(--gold);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
}

.brand-name {
  font-family: 'Cormorant Garamond', serif;
  font-size: 19px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: 0.01em;
}

.brand-sub {
  font-size: 11px;
  color: var(--text3);
  font-weight: 400;
  margin-top: 1px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-tabs {
  display: flex;
  background: var(--surface2);
  border-radius: 8px;
  padding: 3px;
  gap: 2px;
}

.htab {
  padding: 5px 14px;
  border-radius: 6px;
  border: none;
  background: none;
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  font-weight: 500;
  color: var(--text2);
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  gap: 5px;
}
.htab:hover { color: var(--text); }
.htab.active { background: var(--surface); color: var(--text); box-shadow: 0 1px 3px rgba(0,0,0,0.08); }

.saved-badge {
  background: var(--gold);
  color: #fff;
  border-radius: 10px;
  padding: 1px 6px;
  font-size: 10px;
  font-weight: 600;
  display: none;
}

.last-search-info {
  font-size: 11px;
  color: var(--text3);
  font-family: 'JetBrains Mono', monospace;
}

.btn-primary {
  background: var(--text);
  color: #fff;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 7px;
  transition: all 0.15s;
  letter-spacing: 0.01em;
}
.btn-primary:hover { background: #2d2d2a; transform: translateY(-1px); box-shadow: var(--shadow); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; }

.spinner {
  width: 11px; height: 11px;
  border: 1.5px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: none;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* LAYOUT */
.layout {
  display: grid;
  grid-template-columns: 268px 1fr;
  min-height: calc(100vh - 60px);
}

/* SIDEBAR */
.sidebar {
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  position: sticky;
  top: 60px;
  height: calc(100vh - 60px);
  overflow-y: auto;
}

.sidebar-section-title {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text3);
  margin-bottom: 8px;
}

/* STAT CARDS */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.stat-card {
  background: var(--surface2);
  border-radius: 10px;
  padding: 12px;
  border: 1px solid var(--border);
}

.stat-num {
  font-family: 'Cormorant Garamond', serif;
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
  line-height: 1;
  margin-bottom: 3px;
}

.stat-num.green { color: var(--green); }
.stat-num.amber { color: var(--amber); }
.stat-num.gold { color: var(--gold); }

.stat-label {
  font-size: 10px;
  color: var(--text3);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* FILTERS */
.filter-group { margin-bottom: 14px; }

.filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.chip {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid var(--border2);
  background: transparent;
  color: var(--text2);
  transition: all 0.12s;
  font-family: 'Inter', sans-serif;
}
.chip:hover { border-color: var(--gold-border); color: var(--gold); }
.chip.active { background: var(--gold-bg); border-color: var(--gold-border); color: var(--gold); }

/* PROFILE CARD */
.profile-card {
  background: var(--gold-bg);
  border: 1px solid var(--gold-border);
  border-radius: 10px;
  padding: 14px;
}

.profile-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 4px;
}

.profile-meta {
  font-size: 11px;
  color: var(--text2);
  line-height: 1.7;
  margin-bottom: 10px;
}

.profile-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.ptag {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(154,123,58,0.12);
  color: var(--gold);
  font-weight: 500;
  border: 1px solid var(--gold-border);
  letter-spacing: 0.03em;
}

/* MAIN */
.main {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* SEARCH */
.search-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: var(--shadow);
}

.search-wrap svg { flex-shrink: 0; opacity: 0.35; }

.search-wrap input {
  flex: 1;
  border: none;
  outline: none;
  background: none;
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  color: var(--text);
}
.search-wrap input::placeholder { color: var(--text3); }

/* SECTION HEADER */
.section-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.section-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 22px;
  font-weight: 600;
  color: var(--text);
}

.count-label {
  font-size: 11px;
  color: var(--text3);
  font-family: 'JetBrains Mono', monospace;
}

/* OPP CARDS */
.opp-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.18s;
  position: relative;
  box-shadow: var(--shadow);
  margin-bottom: 10px;
  overflow: hidden;
}

.opp-card::after {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  border-radius: 3px 0 0 3px;
}

.opp-card.r-Alta::after { background: var(--green); }
.opp-card.r-Média::after { background: var(--amber); }
.opp-card.r-Baixa::after { background: var(--text3); }

.opp-card:hover {
  border-color: var(--border2);
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

.opp-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.opp-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 17px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.35;
  flex: 1;
}

.badges {
  display: flex;
  gap: 5px;
  flex-shrink: 0;
  align-items: center;
}

.badge {
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 5px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border: 1px solid transparent;
}

.b-Alta { background: var(--green-bg); color: var(--green); border-color: rgba(45,122,95,0.2); }
.b-Média { background: var(--amber-bg); color: var(--amber); border-color: rgba(181,98,10,0.2); }
.b-Baixa { background: var(--surface2); color: var(--text3); border-color: var(--border); }
.b-urgA { background: #fef0ee; color: var(--red); border-color: rgba(192,57,43,0.2); }
.b-urgM { background: var(--amber-bg); color: var(--amber); border-color: rgba(181,98,10,0.2); }
.b-urgB { background: var(--blue-bg); color: var(--blue); border-color: rgba(30,90,156,0.2); }
.b-A { background: var(--blue-bg); color: var(--blue); border-color: rgba(30,90,156,0.2); }
.b-B { background: var(--green-bg); color: var(--green); border-color: rgba(45,122,95,0.2); }
.b-AB { background: var(--amber-bg); color: var(--amber); border-color: rgba(181,98,10,0.2); }

.opp-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-bottom: 10px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--text2);
}
.meta-item strong { color: var(--text); font-weight: 500; }

.opp-summary {
  font-size: 12px;
  color: var(--text2);
  line-height: 1.65;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 12px;
}

.opp-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.opp-program {
  font-size: 11px;
  color: var(--text3);
  font-family: 'JetBrains Mono', monospace;
}

.opp-amount {
  font-family: 'Cormorant Garamond', serif;
  font-size: 18px;
  font-weight: 700;
  color: var(--gold);
}

.opp-amount-label {
  font-size: 10px;
  color: var(--text3);
  font-family: 'Inter', sans-serif;
  font-weight: 400;
  margin-left: 3px;
}

.save-btn {
  position: absolute;
  top: 14px;
  right: 14px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 4px;
  border-radius: 5px;
  transition: all 0.15s;
  color: var(--text3);
  line-height: 1;
  z-index: 2;
}
.save-btn:hover { color: var(--gold); transform: scale(1.15); }
.save-btn.saved { color: var(--gold); }

.score-bar {
  height: 2px;
  background: var(--border);
  border-radius: 2px;
  margin-top: 10px;
  overflow: hidden;
}
.score-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--gold-border), var(--gold));
  border-radius: 2px;
  transition: width 0.6s ease;
}

/* EMPTY / LOADING */
.empty-state {
  text-align: center;
  padding: 80px 32px;
  color: var(--text3);
}
.empty-icon { font-size: 40px; margin-bottom: 14px; }
.empty-state h3 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 20px;
  color: var(--text2);
  margin-bottom: 8px;
  font-weight: 600;
}
.empty-state p { font-size: 13px; line-height: 1.65; }

.loading-state { text-align: center; padding: 60px; color: var(--text3); }
.dots { display: inline-flex; gap: 5px; margin-bottom: 14px; }
.dots span {
  width: 7px; height: 7px;
  background: var(--gold-light);
  border-radius: 50%;
  animation: bounce 1.2s ease infinite;
}
.dots span:nth-child(2) { animation-delay: 0.2s; }
.dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%,80%,100%{transform:scale(0.6);opacity:0.4} 40%{transform:scale(1);opacity:1} }

/* MODAL */
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(26,26,24,0.5);
  backdrop-filter: blur(6px);
  z-index: 200;
  display: none;
  align-items: flex-start;
  justify-content: center;
  padding: 32px 16px;
  overflow-y: auto;
}
.overlay.open { display: flex; }

.modal {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  width: 100%;
  max-width: 820px;
  margin: auto;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
  animation: mIn 0.22s ease;
}
@keyframes mIn { from{opacity:0;transform:translateY(16px) scale(0.98)} to{opacity:1;transform:none} }

.modal-head {
  padding: 24px 28px 18px;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.modal-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 22px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.3;
}

.modal-x {
  background: none;
  border: none;
  color: var(--text3);
  font-size: 20px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 5px;
  transition: all 0.12s;
  flex-shrink: 0;
  line-height: 1;
}
.modal-x:hover { background: var(--surface2); color: var(--text); }

.modal-body {
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.msect-title {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--gold);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.msect-title::after { content:''; flex:1; height:1px; background:var(--border); }

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.info-cell {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
}
.info-cell-label {
  font-size: 10px;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 3px;
  font-weight: 500;
}
.info-cell-val {
  font-size: 13px;
  color: var(--text);
  font-weight: 500;
}
.info-cell-val.gold {
  font-family: 'Cormorant Garamond', serif;
  font-size: 18px;
  color: var(--gold);
}

.text-block {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px;
  font-size: 12px;
  color: var(--text2);
  line-height: 1.75;
  white-space: pre-wrap;
}

.budget-table { width: 100%; border-collapse: collapse; }
.budget-table th {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text3);
  text-align: left;
  padding: 6px 10px;
  border-bottom: 1px solid var(--border);
  font-weight: 600;
}
.budget-table td {
  padding: 10px;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  color: var(--text2);
  vertical-align: top;
}
.budget-table tr:last-child td { border-bottom: none; }
.budget-table td:last-child {
  text-align: right;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--text);
  white-space: nowrap;
}

.budget-total {
  background: var(--gold-bg);
  border: 1px solid var(--gold-border);
  border-radius: 8px;
  padding: 14px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}
.bt-label { font-size: 12px; color: var(--text2); }
.bt-sub { font-size: 11px; color: var(--text3); margin-top: 2px; }
.bt-amount {
  font-family: 'Cormorant Garamond', serif;
  font-size: 26px;
  font-weight: 700;
  color: var(--gold);
}
.bt-rate { font-size: 11px; color: var(--text3); margin-top: 2px; text-align: right; }

.steps-list { list-style: none; display: flex; flex-direction: column; gap: 7px; }
.steps-list li {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: var(--text2);
  line-height: 1.5;
  align-items: flex-start;
}
.step-n {
  width: 20px; height: 20px;
  background: var(--gold-bg);
  border: 1px solid var(--gold-border);
  border-radius: 50%;
  font-size: 10px;
  font-weight: 700;
  color: var(--gold);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 1px;
}

.link-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--blue);
  font-size: 12px;
  text-decoration: none;
  padding: 7px 13px;
  border: 1px solid rgba(30,90,156,0.25);
  border-radius: 7px;
  transition: all 0.12s;
  background: var(--blue-bg);
}
.link-btn:hover { background: #dce9f8; }

.action-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-action {
  background: var(--surface2);
  border: 1px solid var(--border2);
  color: var(--text2);
  padding: 7px 13px;
  border-radius: 7px;
  font-size: 12px;
  font-family: 'Inter', sans-serif;
  cursor: pointer;
  transition: all 0.12s;
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}
.btn-action:hover { border-color: var(--gold-border); color: var(--gold); background: var(--gold-bg); }

.notes-area {
  width: 100%;
  background: var(--surface2);
  border: 1px solid var(--border2);
  border-radius: 8px;
  padding: 10px 12px;
  color: var(--text);
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  resize: vertical;
  outline: none;
  min-height: 70px;
  line-height: 1.6;
  transition: border-color 0.12s;
}
.notes-area:focus { border-color: var(--gold-border); }
.notes-area::placeholder { color: var(--text3); }

/* CHAT */
.chat-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 50px; height: 50px;
  border-radius: 50%;
  background: var(--text);
  border: none;
  cursor: pointer;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2);
  z-index: 150;
  transition: all 0.18s;
}
.chat-fab:hover { transform: scale(1.08); box-shadow: 0 6px 24px rgba(0,0,0,0.25); }

.chat-panel {
  position: fixed;
  bottom: 84px; right: 24px;
  width: 360px; height: 500px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  z-index: 150;
  transform: scale(0.92) translateY(16px);
  opacity: 0;
  pointer-events: none;
  transition: all 0.22s cubic-bezier(0.34,1.56,0.64,1);
}
.chat-panel.open { transform: none; opacity: 1; pointer-events: all; }

.chat-head {
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}
.chat-head-left { display: flex; align-items: center; gap: 9px; }
.chat-av {
  width: 32px; height: 32px;
  background: var(--gold-bg);
  border: 1px solid var(--gold-border);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px;
}
.chat-hname { font-size: 13px; font-weight: 600; color: var(--text); }
.chat-hsub { font-size: 10px; color: var(--text3); }
.chat-hx { background:none; border:none; color:var(--text3); cursor:pointer; font-size:16px; padding:3px; border-radius:4px; }
.chat-hx:hover { color: var(--text); }

.chat-msgs {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  scrollbar-width: thin;
}

.cmsg { display: flex; }
.cmsg.user { justify-content: flex-end; }

.cbubble {
  max-width: 84%;
  padding: 9px 13px;
  border-radius: 12px;
  font-size: 12px;
  line-height: 1.65;
  white-space: pre-wrap;
}
.cmsg.user .cbubble {
  background: var(--text);
  color: #fff;
  border-radius: 12px 12px 3px 12px;
}
.cmsg.assistant .cbubble {
  background: var(--surface2);
  border: 1px solid var(--border);
  color: var(--text2);
  border-radius: 12px 12px 12px 3px;
}

.chat-typing {
  display: flex; gap: 4px;
  padding: 9px 13px;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 12px 12px 12px 3px;
  width: fit-content;
}
.chat-typing span {
  width: 5px; height: 5px;
  background: var(--text3);
  border-radius: 50%;
  animation: bounce 1.2s ease infinite;
}
.chat-typing span:nth-child(2) { animation-delay: 0.2s; }
.chat-typing span:nth-child(3) { animation-delay: 0.4s; }

.chat-input-row {
  padding: 10px;
  border-top: 1px solid var(--border);
  display: flex;
  gap: 7px;
  align-items: flex-end;
  flex-shrink: 0;
}
.chat-in {
  flex: 1;
  background: var(--surface2);
  border: 1px solid var(--border2);
  border-radius: 8px;
  padding: 7px 11px;
  color: var(--text);
  font-family: 'Inter', sans-serif;
  font-size: 12px;
  resize: none;
  outline: none;
  max-height: 100px;
  overflow-y: auto;
  line-height: 1.5;
  transition: border-color 0.12s;
}
.chat-in:focus { border-color: var(--gold-border); }
.chat-in::placeholder { color: var(--text3); }

.chat-send-btn {
  width: 32px; height: 32px;
  background: var(--text);
  border: none;
  border-radius: 7px;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  transition: all 0.12s;
}
.chat-send-btn:hover { background: #2d2d2a; }
.chat-send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* CONSULTANCIES */
.consult-card {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 10px;
}
.consult-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}
.consult-name {
  font-family: 'Cormorant Garamond', serif;
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}
.consult-loc { font-size: 11px; color: var(--text3); margin-top: 1px; }
.consult-score {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 500;
  color: var(--gold);
  background: var(--gold-bg);
  border: 1px solid var(--gold-border);
  padding: 3px 9px;
  border-radius: 20px;
}
.consult-field { margin-bottom: 7px; }
.cfield-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text3);
  font-weight: 500;
  margin-bottom: 2px;
}
.cfield-val { font-size: 12px; color: var(--text2); line-height: 1.55; }
.ctags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }
.ctag {
  font-size: 10px;
  padding: 2px 7px;
  background: var(--gold-bg);
  border: 1px solid var(--gold-border);
  color: var(--gold);
  border-radius: 4px;
  font-weight: 500;
}
.consult-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}
.clink {
  font-size: 11px;
  color: var(--blue);
  text-decoration: none;
  padding: 5px 10px;
  border: 1px solid rgba(30,90,156,0.2);
  border-radius: 5px;
  background: var(--blue-bg);
  transition: all 0.12s;
}
.clink:hover { background: #dce9f8; }

@media (max-width: 860px) {
  .layout { grid-template-columns: 1fr; }
  .sidebar { position: static; height: auto; }
  .info-grid { grid-template-columns: 1fr 1fr; }
  .chat-panel { width: calc(100vw - 32px); right: 16px; }
}
</style>
</head>
<body>

<header>
  <div class="brand">
    <div class="brand-mark">🏕</div>
    <div>
      <div class="brand-name">Funds Agent</div>
      <div class="brand-sub">Glamping Skies · Alentejo</div>
    </div>
  </div>
  <div class="header-right">
    <div class="header-tabs">
      <button class="htab active" id="tabAll" onclick="switchTab('all')">Todos</button>
      <button class="htab" id="tabSaved" onclick="switchTab('saved')">
        ⭐ Guardados
        <span class="saved-badge" id="savedBadge">0</span>
      </button>
    </div>
    <span class="last-search-info" id="lastSearch"></span>
    <button class="btn-primary" id="btnSearch" onclick="triggerSearch()">
      <span class="spinner" id="spinner"></span>
      <span id="btnLabel">Pesquisar</span>
    </button>
  </div>
</header>

<div class="layout">
  <aside class="sidebar">
    <div>
      <div class="sidebar-section-title">Resumo</div>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-num" id="sTotal">—</div>
          <div class="stat-label">Total</div>
        </div>
        <div class="stat-card">
          <div class="stat-num green" id="sHigh">—</div>
          <div class="stat-label">Alta relevância</div>
        </div>
        <div class="stat-card">
          <div class="stat-num amber" id="sMed">—</div>
          <div class="stat-label">Média</div>
        </div>
        <div class="stat-card">
          <div class="stat-num gold" id="sToday">—</div>
          <div class="stat-label">Hoje</div>
        </div>
      </div>
    </div>

    <div>
      <div class="sidebar-section-title">Filtros</div>
      <div class="filter-group">
        <div style="font-size:11px;color:var(--text2);margin-bottom:5px;font-weight:500">Relevância</div>
        <div class="filter-chips">
          <button class="chip active" onclick="setFilter('relevance',null,this)">Todos</button>
          <button class="chip" onclick="setFilter('relevance','Alta',this)">Alta</button>
          <button class="chip" onclick="setFilter('relevance','Média',this)">Média</button>
          <button class="chip" onclick="setFilter('relevance','Baixa',this)">Baixa</button>
        </div>
      </div>
      <div class="filter-group">
        <div style="font-size:11px;color:var(--text2);margin-bottom:5px;font-weight:500">Tipo</div>
        <div class="filter-chips">
          <button class="chip active" onclick="setFilter('profile',null,this)">Todos</button>
          <button class="chip" onclick="setFilter('profile','A',this)">🔵 Intangíveis</button>
          <button class="chip" onclick="setFilter('profile','B',this)">🟢 Físico</button>
        </div>
      </div>
      <div class="filter-group">
        <div style="font-size:11px;color:var(--text2);margin-bottom:5px;font-weight:500">Área</div>
        <div class="filter-chips">
          <button class="chip active" onclick="setFilter('area',null,this)">Todas</button>
          <button class="chip" onclick="setFilter('area','Digitalização',this)">Digital</button>
          <button class="chip" onclick="setFilter('area','Marketing',this)">Marketing</button>
          <button class="chip" onclick="setFilter('area','Internacionalização',this)">Internac.</button>
          <button class="chip" onclick="setFilter('area','IA',this)">IA</button>
          <button class="chip" onclick="setFilter('area','Energia',this)">Energia</button>
        </div>
      </div>
    </div>

    <div class="profile-card">
      <div class="sidebar-section-title">Perfil</div>
      <div class="profile-title">Glamping Skies</div>
      <div class="profile-meta">
        Turismo Rural · Estremoz, Alentejo<br>
        Microempresa · CAE 55202<br>
        Território Baixa Densidade
      </div>
      <div class="profile-tags">
        <span class="ptag">Digitalização</span>
        <span class="ptag">Marketing</span>
        <span class="ptag">IA & Automação</span>
        <span class="ptag">Internacionalização</span>
        <span class="ptag">Energia Solar</span>
        <span class="ptag">Fundo Perdido</span>
      </div>
    </div>
  </aside>

  <main class="main">
    <div class="search-wrap">
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.5"/><path d="m11 11 3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
      <input type="text" placeholder="Pesquisar concursos..." id="searchInput" oninput="filterLocal()">
    </div>

    <div class="section-header">
      <div class="section-title">Oportunidades de Financiamento</div>
      <div class="count-label" id="countLabel">0 concursos</div>
    </div>

    <div id="oppList"></div>
  </main>
</div>

<!-- MAIN MODAL -->
<div class="overlay" id="mainOverlay" onclick="closeMainOnOverlay(event)">
  <div class="modal">
    <div class="modal-head">
      <div class="modal-title" id="mTitle"></div>
      <button class="modal-x" onclick="closeMain()">✕</button>
    </div>
    <div class="modal-body" id="mBody"></div>
  </div>
</div>

<!-- CONSULTANCIES MODAL -->
<div class="overlay" id="consultOverlay" onclick="closeConsultOnOverlay(event)">
  <div class="modal">
    <div class="modal-head">
      <div class="modal-title">Consultoras Recomendadas</div>
      <button class="modal-x" onclick="closeConsult()">✕</button>
    </div>
    <div class="modal-body" id="consultBody">
      <div class="loading-state">
        <div class="dots"><span></span><span></span><span></span></div>
        <div>A pesquisar e avaliar consultoras especializadas...</div>
        <div style="font-size:11px;color:var(--text3);margin-top:6px">Pode demorar 20-30 segundos</div>
      </div>
    </div>
  </div>
</div>

<!-- CHAT -->
<button class="chat-fab" onclick="toggleChat()" title="Consultor IA">💬</button>

<div class="chat-panel" id="chatPanel">
  <div class="chat-head">
    <div class="chat-head-left">
      <div class="chat-av">🤖</div>
      <div>
        <div class="chat-hname">Consultor IA</div>
        <div class="chat-hsub">Especialista em fundos europeus</div>
      </div>
    </div>
    <button class="chat-hx" onclick="toggleChat()">✕</button>
  </div>
  <div class="chat-msgs" id="chatMsgs">
    <div class="cmsg assistant">
      <div class="cbubble">Olá! Conheço o perfil completo do Glamping Skies e da Sentido da Lua Lda. Posso ajudar com elegibilidade, formulários, estratégia de candidatura ou avaliar se precisas de consultora externa. Em que posso ajudar?</div>
    </div>
  </div>
  <div class="chat-input-row">
    <textarea class="chat-in" id="chatIn" placeholder="Escreve a tua dúvida..." rows="1" onkeydown="chatKey(event)" oninput="autoH(this)"></textarea>
    <button class="chat-send-btn" onclick="sendChat()">➤</button>
  </div>
</div>

<script>
let allOpps = [];
let filters = { relevance: null, area: null, profile: null };
let chatHistory = [];
let chatOpen = false;
let currentTab = 'all';

// ---- STATS ----
async function loadStats() {
  try {
    const r = await fetch('/api/stats');
    const s = await r.json();
    document.getElementById('sTotal').textContent = s.total || 0;
    document.getElementById('sHigh').textContent = s.high_relevance || 0;
    document.getElementById('sMed').textContent = s.medium_relevance || 0;
    document.getElementById('sToday').textContent = s.found_today || 0;
    if (s.last_search) {
      const d = new Date(s.last_search);
      document.getElementById('lastSearch').textContent =
        'Última: ' + d.toLocaleDateString('pt-PT') + ' ' + d.toLocaleTimeString('pt-PT',{hour:'2-digit',minute:'2-digit'});
    }
  } catch(e) {}
}

// ---- OPPORTUNITIES ----
async function loadOpportunities() {
  showLoading();
  try {
    let url = '/api/opportunities?';
    if (filters.relevance) url += 'relevance=' + filters.relevance + '&';
    if (filters.area) url += 'area=' + filters.area + '&';
    const r = await fetch(url);
    allOpps = await r.json();
    renderOpps(allOpps);
  } catch(e) { showError(); }
}

function showLoading() {
  document.getElementById('oppList').innerHTML = `<div class="loading-state"><div class="dots"><span></span><span></span><span></span></div><div>A carregar...</div></div>`;
}

function showError() {
  document.getElementById('oppList').innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><h3>Erro de ligação</h3><p>Não foi possível ligar ao servidor.</p></div>`;
}

function renderOpps(opps) {
  const list = document.getElementById('oppList');
  document.getElementById('countLabel').textContent = opps.length + ' concurso' + (opps.length !== 1 ? 's' : '');

  // Apply profile filter client-side
  let filtered = opps;
  if (filters.profile) filtered = opps.filter(o => o.investment_profile === filters.profile || (filters.profile === 'A' && !o.investment_profile));

  if (!filtered.length) {
    list.innerHTML = `<div class="empty-state"><div class="empty-icon">🔍</div><h3>Sem resultados</h3><p>Clica em "Pesquisar" para o agente procurar concursos adequados ao teu perfil.</p></div>`;
    return;
  }

  list.innerHTML = filtered.map(o => {
    const budget = parseBudget(o.proposed_budget);
    const amount = budget ? '€' + Number(budget.support_amount).toLocaleString('pt-PT') : '—';
    const profBadge = o.investment_profile === 'A' ? `<span class="badge b-A">🔵 Intangíveis</span>` :
                      o.investment_profile === 'B' ? `<span class="badge b-B">🟢 Físico</span>` :
                      o.investment_profile === 'AB' ? `<span class="badge b-AB">🟡 Misto</span>` : '';
    return `
    <div class="opp-card r-${o.relevance_label || 'Baixa'}" onclick="openMain(${o.id})">
      <button class="save-btn ${o.is_saved ? 'saved' : ''}" onclick="event.stopPropagation();toggleSave(${o.id},this)" title="${o.is_saved ? 'Remover' : 'Guardar'}">${o.is_saved ? '⭐' : '☆'}</button>
      <div class="opp-card-top" style="padding-right:28px">
        <div class="opp-title">${o.title || 'Sem título'}</div>
        <div class="badges">
          <span class="badge b-${o.relevance_label || 'Baixa'}">${o.relevance_label || '—'}</span>
          ${o.urgency ? `<span class="badge b-urg${o.urgency[0]}">${o.urgency}</span>` : ''}
          ${profBadge}
        </div>
      </div>
      <div class="opp-meta">
        ${o.deadline ? `<div class="meta-item">📅 <strong>${o.deadline}</strong></div>` : ''}
        ${o.support_rate ? `<div class="meta-item">💶 <strong>${o.support_rate}</strong></div>` : ''}
        ${o.area ? `<div class="meta-item">🏷 <strong>${o.area}</strong></div>` : ''}
      </div>
      ${o.eligibility_analysis ? `<div class="opp-summary">${o.eligibility_analysis}</div>` : ''}
      <div class="opp-footer">
        <div class="opp-program">${o.program || ''} · ${o.managing_entity || ''}</div>
        <div><span class="opp-amount">${amount}</span><span class="opp-amount-label">apoio estimado</span></div>
      </div>
      <div class="score-bar"><div class="score-fill" style="width:${o.relevance_score||0}%"></div></div>
    </div>`;
  }).join('');
}

function parseBudget(raw) {
  if (!raw) return null;
  try { return typeof raw === 'string' ? JSON.parse(raw) : raw; } catch(e) { return null; }
}

// ---- MODAL ----
async function openMain(id) {
  const o = allOpps.find(x => x.id === id);
  if (!o) return;
  document.getElementById('mTitle').textContent = o.title;
  const budget = parseBudget(o.proposed_budget);
  const steps = o.next_steps ? o.next_steps.split('\\n').filter(s => s.trim()) : [];

  let budgetHtml = '';
  if (budget && budget.components) {
    budgetHtml = `
      <table class="budget-table">
        <thead><tr><th>Componente</th><th>Descrição</th><th>Valor</th></tr></thead>
        <tbody>
          ${budget.components.map(c => `
            <tr>
              <td style="color:var(--text);font-weight:500;white-space:nowrap">${c.name}</td>
              <td>${c.description||''}</td>
              <td>€${Number(c.value).toLocaleString('pt-PT')}</td>
            </tr>`).join('')}
        </tbody>
      </table>
      <div class="budget-total">
        <div>
          <div class="bt-label">Investimento elegível total</div>
          <div class="bt-sub">Comparticipação própria: €${Number(budget.own_contribution||0).toLocaleString('pt-PT')}</div>
        </div>
        <div style="text-align:right">
          <div class="bt-amount">€${Number(budget.support_amount||0).toLocaleString('pt-PT')}</div>
          <div class="bt-rate">fundo perdido · ${budget.support_rate_applied||o.support_rate||'—'} · Total €${Number(budget.total_investment||0).toLocaleString('pt-PT')}</div>
        </div>
      </div>`;
  }

  document.getElementById('mBody').innerHTML = `
    <div>
      <div class="msect-title">Informação do Concurso</div>
      <div class="info-grid">
        <div class="info-cell"><div class="info-cell-label">Programa</div><div class="info-cell-val">${o.program||'—'}</div></div>
        <div class="info-cell"><div class="info-cell-label">Entidade</div><div class="info-cell-val">${o.managing_entity||'—'}</div></div>
        <div class="info-cell"><div class="info-cell-label">Prazo</div><div class="info-cell-val">${o.deadline||'—'}</div></div>
        <div class="info-cell"><div class="info-cell-label">Dotação Total</div><div class="info-cell-val">${o.total_budget||'—'}</div></div>
        <div class="info-cell"><div class="info-cell-label">Máx. por Candidatura</div><div class="info-cell-val">${o.max_per_project||'—'}</div></div>
        <div class="info-cell"><div class="info-cell-label">Taxa de Apoio</div><div class="info-cell-val gold">${o.support_rate||'—'}</div></div>
      </div>
    </div>
    <div>
      <div class="msect-title">Análise de Elegibilidade</div>
      <div class="text-block">${o.eligibility_analysis||'—'}</div>
    </div>
    ${budget ? `<div><div class="msect-title">Proposta Orçamental</div>${budgetHtml}</div>` : ''}
    ${o.proposal_text ? `<div><div class="msect-title">Texto da Proposta</div><div class="text-block">${o.proposal_text}</div></div>` : ''}
    ${steps.length ? `<div><div class="msect-title">Próximos Passos</div><ul class="steps-list">${steps.map((s,i)=>`<li><div class="step-n">${i+1}</div><span>${s.replace(/^[-•*\\d.]+\\s*/,'')}</span></li>`).join('')}</ul></div>` : ''}
    <div>
      <div class="msect-title">Notas Pessoais</div>
      <textarea class="notes-area" id="notesArea_${o.id}" placeholder="Adiciona notas, dúvidas ou próximos passos..." onblur="saveNotes(${o.id})">${o.saved_notes||''}</textarea>
      <div style="font-size:11px;color:var(--text3);margin-top:4px">Guardado automaticamente</div>
    </div>
    <div class="action-row">
      ${o.official_link ? `<a href="${o.official_link}" target="_blank" class="link-btn">🔗 Página oficial do concurso</a>` : ''}
      <button class="btn-action" onclick="openConsult(${o.id})">🏢 Consultoras Especializadas</button>
      <button class="btn-action" onclick="askChat(${o.id})">💬 Perguntar ao Consultor IA</button>
    </div>
  `;

  document.getElementById('mainOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeMain() {
  document.getElementById('mainOverlay').classList.remove('open');
  document.body.style.overflow = '';
}
function closeMainOnOverlay(e) { if (e.target === document.getElementById('mainOverlay')) closeMain(); }

// ---- CONSULTANCIES ----
async function openConsult(id) {
  const body = document.getElementById('consultBody');
  body.innerHTML = `<div class="loading-state"><div class="dots"><span></span><span></span><span></span></div><div>A pesquisar consultoras...</div><div style="font-size:11px;color:var(--text3);margin-top:6px">20-30 segundos</div></div>`;
  document.getElementById('consultOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
  try {
    const r = await fetch('/api/opportunities/' + id + '/consultancies');
    const list = await r.json();
    if (!list.length) {
      body.innerHTML = `<div class="empty-state"><div class="empty-icon">🔍</div><h3>Sem resultados</h3><p>Não foram encontradas consultoras verificadas para este concurso. Consulta o Chat IA para alternativas.</p></div>`;
      return;
    }
    body.innerHTML = list.map((c,i) => `
      <div class="consult-card">
        <div class="consult-top">
          <div><div class="consult-name">${i+1}. ${c.name||'—'}</div><div class="consult-loc">📍 ${c.location||'Portugal'}</div></div>
          <div class="consult-score">⭐ ${c.screening_score||'—'}/100</div>
        </div>
        <div class="consult-field"><div class="cfield-label">Especialização</div><div class="cfield-val">${c.specialization||'—'}</div></div>
        <div class="consult-field"><div class="cfield-label">Track Record</div><div class="cfield-val">${c.track_record||'—'}</div></div>
        <div class="consult-field"><div class="cfield-label">Adequação a este concurso</div><div class="cfield-val">${c.suitability_for_this_call||'—'}</div></div>
        ${c.screening_notes ? `<div class="consult-field"><div class="cfield-label">Notas</div><div class="cfield-val">${c.screening_notes}</div></div>` : ''}
        <div class="ctags">${(c.programs_expertise||[]).map(p=>`<span class="ctag">${p}</span>`).join('')}</div>
        <div class="consult-foot">
          <div style="font-size:11px;color:var(--text3)">${c.estimated_fee ? '💶 ' + c.estimated_fee : ''}</div>
          ${c.website ? `<a href="${c.website}" target="_blank" class="clink">🔗 Website</a>` : ''}
        </div>
      </div>`).join('');
  } catch(e) {
    body.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><h3>Erro</h3><p>Não foi possível obter recomendações.</p></div>`;
  }
}

function closeConsult() {
  document.getElementById('consultOverlay').classList.remove('open');
  document.body.style.overflow = '';
}
function closeConsultOnOverlay(e) { if (e.target === document.getElementById('consultOverlay')) closeConsult(); }

// ---- SAVE ----
async function toggleSave(id, btn) {
  const r = await fetch('/api/opportunities/' + id + '/save', { method:'POST', headers:{'Content-Type':'application/json'}, body:'{}' });
  const d = await r.json();
  btn.textContent = d.is_saved ? '⭐' : '☆';
  btn.classList.toggle('saved', d.is_saved);
  const o = allOpps.find(x => x.id === id);
  if (o) o.is_saved = d.is_saved ? 1 : 0;
  updateSavedBadge();
  if (currentTab === 'saved' && !d.is_saved) loadSaved();
}

async function saveNotes(id) {
  const ta = document.getElementById('notesArea_' + id);
  if (!ta) return;
  const notes = ta.value;
  await fetch('/api/opportunities/' + id + '/notes', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({notes}) });
  if (notes) {
    const o = allOpps.find(x => x.id === id);
    if (o && !o.is_saved) {
      await fetch('/api/opportunities/' + id + '/save', { method:'POST', headers:{'Content-Type':'application/json'}, body:'{}' });
      if (o) o.is_saved = 1;
      updateSavedBadge();
    }
  }
}

async function updateSavedBadge() {
  try {
    const r = await fetch('/api/saved');
    const s = await r.json();
    const b = document.getElementById('savedBadge');
    b.textContent = s.length;
    b.style.display = s.length ? 'inline' : 'none';
  } catch(e) {}
}

// ---- TABS ----
function switchTab(tab) {
  currentTab = tab;
  document.getElementById('tabAll').classList.toggle('active', tab === 'all');
  document.getElementById('tabSaved').classList.toggle('active', tab === 'saved');
  tab === 'all' ? loadOpportunities() : loadSaved();
}

async function loadSaved() {
  showLoading();
  try {
    const r = await fetch('/api/saved');
    allOpps = await r.json();
    if (!allOpps.length) {
      document.getElementById('oppList').innerHTML = `<div class="empty-state"><div class="empty-icon">⭐</div><h3>Nenhum concurso guardado</h3><p>Clica em ☆ em qualquer concurso para o guardar aqui.</p></div>`;
      document.getElementById('countLabel').textContent = '0 concursos';
    } else {
      renderOpps(allOpps);
    }
  } catch(e) { showError(); }
}

// ---- FILTERS ----
function setFilter(type, val, el) {
  filters[type] = val;
  el.closest('.filter-chips').querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  if (type !== 'profile') loadOpportunities();
  else renderOpps(allOpps);
}

function filterLocal() {
  const q = document.getElementById('searchInput').value.toLowerCase();
  if (!q) { renderOpps(allOpps); return; }
  renderOpps(allOpps.filter(o =>
    (o.title||'').toLowerCase().includes(q) ||
    (o.program||'').toLowerCase().includes(q) ||
    (o.area||'').toLowerCase().includes(q) ||
    (o.eligibility_analysis||'').toLowerCase().includes(q)
  ));
}

// ---- SEARCH ----
async function triggerSearch() {
  const btn = document.getElementById('btnSearch');
  const spinner = document.getElementById('spinner');
  const label = document.getElementById('btnLabel');
  btn.disabled = true;
  spinner.style.display = 'block';
  label.textContent = 'A pesquisar...';
  try {
    await fetch('/api/run-search', { method:'POST' });
    let tries = 0;
    const poll = setInterval(async () => {
      tries++;
      await loadStats();
      await loadOpportunities();
      if (tries > 60) { clearInterval(poll); reset(); }
    }, 5000);
    setTimeout(() => { clearInterval(poll); reset(); }, 300000);
  } catch(e) { reset(); }
  function reset() {
    btn.disabled = false;
    spinner.style.display = 'none';
    label.textContent = 'Pesquisar';
  }
}

// ---- CHAT ----
function toggleChat() {
  chatOpen = !chatOpen;
  document.getElementById('chatPanel').classList.toggle('open', chatOpen);
  if (chatOpen) setTimeout(() => document.getElementById('chatIn').focus(), 300);
}

function chatKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); } }
function autoH(el) { el.style.height = 'auto'; el.style.height = Math.min(el.scrollHeight,100) + 'px'; }

async function sendChat() {
  const input = document.getElementById('chatIn');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  input.style.height = 'auto';
  addMsg('user', text);
  chatHistory.push({ role:'user', content:text });
  const typing = addTyping();
  document.querySelector('.chat-send-btn').disabled = true;
  try {
    const r = await fetch('/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({messages: chatHistory}) });
    const d = await r.json();
    typing.remove();
    const reply = d.reply || 'Erro.';
    addMsg('assistant', reply);
    chatHistory.push({ role:'assistant', content:reply });
  } catch(e) { typing.remove(); addMsg('assistant','Erro de ligação.'); }
  document.querySelector('.chat-send-btn').disabled = false;
}

function addMsg(role, text) {
  const msgs = document.getElementById('chatMsgs');
  const d = document.createElement('div');
  d.className = 'cmsg ' + role;
  d.innerHTML = `<div class="cbubble">${text.replace(/\\n/g,'<br>')}</div>`;
  msgs.appendChild(d);
  msgs.scrollTop = msgs.scrollHeight;
  return d;
}

function addTyping() {
  const msgs = document.getElementById('chatMsgs');
  const d = document.createElement('div');
  d.className = 'cmsg assistant';
  d.innerHTML = `<div class="chat-typing"><span></span><span></span><span></span></div>`;
  msgs.appendChild(d);
  msgs.scrollTop = msgs.scrollHeight;
  return d;
}

function askChat(id) {
  const o = allOpps.find(x => x.id === id);
  if (!o) return;
  closeMain();
  if (!chatOpen) toggleChat();
  const input = document.getElementById('chatIn');
  input.value = `Analisa este concurso: "${o.title}" (${o.program}). Devo candidatar por meios próprios ou preciso de consultora?`;
  autoH(input);
  input.focus();
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') { closeMain(); closeConsult(); } });

loadStats();
loadOpportunities();
updateSavedBadge();
</script>
</body>
</html>
"""

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