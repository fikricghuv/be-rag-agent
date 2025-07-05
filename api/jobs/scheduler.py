from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from core.config_db import config_db
from api.jobs.chat_analysis import process_user_chats
import logging

logger = logging.getLogger(__name__)

def run_analysis_job():
    """
    Fungsi yang dipanggil scheduler untuk menganalisis chat user.
    """
    logger.info("Running scheduled user chat analysis job...")

    with next(config_db()) as db:
        process_user_chats(db)

def start_scheduler():
    """
    Inisialisasi dan jalankan scheduler dengan interval tertentu.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_analysis_job,
        trigger=IntervalTrigger(minutes=3600), 
        id="chat_analysis_job",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler started.")
