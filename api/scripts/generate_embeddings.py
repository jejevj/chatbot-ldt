"""
Script untuk generate embeddings untuk semua data di database
Run: python generate_embeddings.py
"""
import sys
from sqlalchemy.orm import Session
from database import SessionLocal, DataTerbuka, DataEmbedding
from embedding_service import get_embedding_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_embeddings_for_all_data():
    """Generate embeddings untuk semua data di v_detail_data_terbuka"""
    db = SessionLocal()
    
    try:
        # Get embedding service
        embedding_service = get_embedding_service()
        
        # Get all data
        all_data = db.query(DataTerbuka).all()
        logger.info(f"Found {len(all_data)} data records")
        
        if not all_data:
            logger.warning("No data found in v_detail_data_terbuka")
            return
        
        # Prepare texts untuk embedding
        texts = []
        kode_data_list = []
        
        for data in all_data:
            # Gabungkan judul, kategori, tipe, dan deskripsi
            text_content = f"{data.judul_data or ''} {data.kategori_data or ''} {data.tipe_data or ''} {data.deskripsi_data or ''}"
            text_content = text_content.strip()
            
            texts.append(text_content)
            kode_data_list.append(data.kode_data)
        
        # Generate embeddings in batch
        logger.info("Generating embeddings...")
        embeddings = embedding_service.encode_batch(texts)
        
        # Save to database
        logger.info("Saving embeddings to database...")
        for i, (kode_data, text, embedding) in enumerate(zip(kode_data_list, texts, embeddings)):
            # Check if embedding already exists
            existing = db.query(DataEmbedding).filter(
                DataEmbedding.kode_data == kode_data
            ).first()
            
            if existing:
                # Update existing
                existing.embedding = embedding
                existing.text_content = text
                logger.info(f"Updated embedding for {kode_data}")
            else:
                # Create new
                new_embedding = DataEmbedding(
                    kode_data=kode_data,
                    embedding=embedding,
                    text_content=text
                )
                db.add(new_embedding)
                logger.info(f"Created embedding for {kode_data}")
            
            # Commit every 10 records
            if (i + 1) % 10 == 0:
                db.commit()
                logger.info(f"Progress: {i + 1}/{len(kode_data_list)}")
        
        # Final commit
        db.commit()
        logger.info(f"Successfully generated embeddings for {len(kode_data_list)} records")
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}", exc_info=True)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    generate_embeddings_for_all_data()
