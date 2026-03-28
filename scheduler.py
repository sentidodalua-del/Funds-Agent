import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from agent import run_daily_search
import uvicorn
from main import app

scheduler = AsyncIOScheduler()

async def scheduled_search():
    await run_daily_search()

def start():
    # Schedule daily at 07:00 Portugal time
    scheduler.add_job(
        scheduled_search,
        CronTrigger(hour=7, minute=0, timezone="Europe/Lisbon"),
        id="daily_search",
        replace_existing=True
    )
    scheduler.start()
    print("Scheduler started. Daily search at 07:00 Lisbon time.")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start()
