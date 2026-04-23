"""
Data browsing endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import logging

from app.database import get_db

router = APIRouter(tags=["data"])
logger = logging.getLogger(__name__)


@router.get("/data")
async def list_data(
    kategori: Optional[str] = None,
    tipe: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all open data with optional filters"""
    try:
        sql = "SELECT url, kode_data, tipe_data, kategori_data, sifat_data, deskripsi_data, judul_data FROM v_detail_data_terbuka WHERE 1=1"
        params = {}
        
        if kategori:
            sql += " AND LOWER(kategori_data) LIKE LOWER(:kategori)"
            params["kategori"] = f"%{kategori}%"
        
        if tipe:
            sql += " AND LOWER(tipe_data) LIKE LOWER(:tipe)"
            params["tipe"] = f"%{tipe}%"
        
        sql += " LIMIT :limit"
        params["limit"] = limit
        
        result = db.execute(text(sql), params)
        rows = result.fetchall()
        
        return [
            {
                "url": row[0],
                "kode_data": row[1],
                "tipe_data": row[2],
                "kategori_data": row[3],
                "sifat_data": row[4],
                "deskripsi_data": row[5],
                "judul_data": row[6]
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Error listing data: {str(e)}", exc_info=True)
        return []


@router.get("/kategori")
async def list_kategori(db: Session = Depends(get_db)):
    """List all available categories"""
    try:
        result = db.execute(text("SELECT DISTINCT kategori_data FROM v_detail_data_terbuka WHERE kategori_data IS NOT NULL ORDER BY kategori_data"))
        return [r[0] for r in result]
    except Exception as e:
        logger.error(f"Error listing categories: {str(e)}", exc_info=True)
        return []


@router.get("/tipe")
async def list_tipe(db: Session = Depends(get_db)):
    """List all available data types"""
    try:
        result = db.execute(text("SELECT DISTINCT tipe_data FROM v_detail_data_terbuka WHERE tipe_data IS NOT NULL ORDER BY tipe_data"))
        return [r[0] for r in result]
    except Exception as e:
        logger.error(f"Error listing types: {str(e)}", exc_info=True)
        return []
