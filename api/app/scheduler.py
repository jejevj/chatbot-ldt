"""
Background scheduler for periodic tasks
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from app.config import settings
from app.database import SessionLocal

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def update_embeddings():
    """Update embeddings for all data"""
    try:
        logger.info("Starting scheduled embedding update...")
        
        from app.services.embedding_service import EmbeddingService
        from app.database import DataTerbuka, DataEmbedding
        
        db = SessionLocal()
        try:
            embedding_service = EmbeddingService()
            
            # Get all data
            all_data = db.execute("SELECT * FROM v_detail_data_terbuka").fetchall()
            
            # Check for new/updated data
            existing_codes = {e.kode_data for e in db.query(DataEmbedding.kode_data).all()}
            
            new_count = 0
            for row in all_data:
                kode_data = row[1]  # kode_data column
                
                if kode_data not in existing_codes:
                    # Generate embedding for new data
                    text = f"{row[6] or ''} {row[5] or ''}"  # judul + deskripsi
                    embedding = embedding_service.encode(text)
                    
                    # Save to database
                    db_embedding = DataEmbedding(
                        kode_data=kode_data,
                        embedding=embedding
                    )
                    db.add(db_embedding)
                    new_count += 1
            
            db.commit()
            logger.info(f"Embedding update completed. Added {new_count} new embeddings.")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error updating embeddings: {str(e)}", exc_info=True)


def start_scheduler():
    """Start the background scheduler"""
    if not settings.AUTO_UPDATE_EMBEDDINGS:
        logger.info("Auto-update embeddings is disabled")
        return
    
    if not scheduler.running:
        # Update embeddings based on configured interval
        scheduler.add_job(
            update_embeddings,
            trigger=IntervalTrigger(hours=settings.EMBEDDING_UPDATE_INTERVAL_HOURS),
            id='update_embeddings',
            name=f'Update embeddings every {settings.EMBEDDING_UPDATE_INTERVAL_HOURS} hours',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info(f"Background scheduler started - embeddings will update every {settings.EMBEDDING_UPDATE_INTERVAL_HOURS} hours")


def stop_scheduler():
    """Stop the background scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")
