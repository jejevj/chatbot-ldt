"""
Chat endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import logging
import json
import uuid

from app.database import get_db, ChatSession, ChatMessage, Device
from app.schemas import (
    ChatRequest, ChatResponse,
    ChatHistoryRequest, ChatHistoryResponse
)
from app.services import search_data, generate_response
from app.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Simple chat endpoint without history"""
    try:
        logger.info(f"Received question: {request.pertanyaan}")
        
        # Search for relevant data
        data_list = search_data(db, request.pertanyaan)
        
        if not data_list:
            logger.info("No relevant data found")
            answer = await generate_response(request.pertanyaan, "", has_data=False)
            return ChatResponse(jawaban=answer, sumber=[])
        
        # Build context
        context = "\n\n".join([
            f"Judul: {data.judul_data}\nKategori: {data.kategori_data}\nTipe: {data.tipe_data}\nURL: {data.url}\nDeskripsi: {data.deskripsi_data or 'Tidak ada deskripsi'}"
            for data in data_list
        ])
        
        # Generate response
        answer = await generate_response(request.pertanyaan, context, has_data=True)
        
        # Prepare sources
        sources = [
            {
                "judul": data.judul_data,
                "url": data.url,
                "kategori": data.kategori_data,
                "tipe": data.tipe_data,
                "kode_data": data.kode_data
            }
            for data in data_list
        ]
        
        return ChatResponse(jawaban=answer, sumber=sources)
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return ChatResponse(
            jawaban="Maaf, terjadi kesalahan saat memproses pertanyaan Anda. Silakan coba lagi dalam beberapa saat.",
            sumber=[]
        )


@router.post("/history", response_model=ChatHistoryResponse)
async def chat_with_history(
    request: ChatHistoryRequest,
    device_id: str = Header(..., alias="X-Device-ID"),
    db: Session = Depends(get_db)
):
    """Chat endpoint with session history support"""
    session_id = None
    user_message_id = None
    
    try:
        # Validate device
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            raise HTTPException(status_code=401, detail="Device not registered")
        
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        
        if not session:
            title = request.pertanyaan[:100] + "..." if len(request.pertanyaan) > 100 else request.pertanyaan
            now = datetime.utcnow()
            session = ChatSession(
                session_id=session_id,
                device_id=device_id,
                title=title,
                created_at=now,
                updated_at=now
            )
            db.add(session)
            db.commit()
            db.refresh(session)
        else:
            if session.device_id != device_id:
                raise HTTPException(status_code=403, detail="Session does not belong to this device")
        
        # Get chat history
        previous_messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).limit(settings.CHAT_HISTORY_LIMIT).all()
        
        chat_history = [
            {"role": msg.role, "content": msg.content}
            for msg in previous_messages
        ]
        
        # Save user message
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.pertanyaan,
            created_at=datetime.utcnow()
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        user_message_id = user_message.id
        
        # Search for relevant data
        data_list = search_data(db, request.pertanyaan)
        
        if not data_list:
            answer = await generate_response(
                request.pertanyaan, "", 
                has_data=False, 
                chat_history=chat_history
            )
            sources = []
        else:
            context = "\n\n".join([
                f"Judul: {data.judul_data}\nKategori: {data.kategori_data}\nTipe: {data.tipe_data}\nURL: {data.url}\nDeskripsi: {data.deskripsi_data or 'Tidak ada deskripsi'}"
                for data in data_list
            ])
            
            answer = await generate_response(
                request.pertanyaan, context,
                has_data=True,
                chat_history=chat_history
            )
            
            sources = [
                {
                    "judul": data.judul_data,
                    "url": data.url,
                    "kategori": data.kategori_data,
                    "tipe": data.tipe_data,
                    "kode_data": data.kode_data
                }
                for data in data_list
            ]
        
        # Save assistant message
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=answer,
            sources=json.dumps(sources) if sources else None,
            created_at=datetime.utcnow()
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        return ChatHistoryResponse(
            session_id=session_id,
            jawaban=answer,
            sumber=sources
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat_with_history: {str(e)}", exc_info=True)
        
        # Cleanup
        if user_message_id:
            try:
                db.query(ChatMessage).filter(ChatMessage.id == user_message_id).delete()
                db.commit()
            except:
                db.rollback()
        else:
            db.rollback()
        
        return ChatHistoryResponse(
            session_id=session_id or str(uuid.uuid4()),
            jawaban="Maaf, terjadi kesalahan saat memproses pertanyaan Anda. Silakan coba lagi dalam beberapa saat.",
            sumber=[]
        )


@router.get("/quick-questions")
async def get_quick_questions(db: Session = Depends(get_db)):
    """Generate dynamic quick questions"""
    try:
        from sqlalchemy import text
        
        # Get random categories
        result = db.execute(text("SELECT DISTINCT kategori_data FROM v_detail_data_terbuka LIMIT 10"))
        categories = [r[0] for r in result if r[0]]
        
        # Get random types
        result = db.execute(text("SELECT DISTINCT tipe_data FROM v_detail_data_terbuka LIMIT 5"))
        types = [r[0] for r in result if r[0]]
        
        questions = []
        
        if len(categories) >= 2:
            questions.append(f"Apa saja data {categories[0]} yang tersedia?")
            questions.append(f"Bagaimana cara mengakses data {categories[1]}?")
        
        questions.append("Data apa saja yang bisa saya akses?")
        questions.append("Bagaimana cara mencari data tertentu?")
        
        if types:
            questions.append(f"Apakah ada data tipe {types[0]}?")
        
        import random
        random.shuffle(questions)
        
        return questions[:random.randint(4, 6)]
    
    except Exception as e:
        logger.error(f"Error generating quick questions: {str(e)}")
        return [
            "Data apa saja yang tersedia?",
            "Bagaimana cara mencari data?",
            "Kategori data apa yang ada?",
            "Apakah ada data terbaru?"
        ]


@router.delete("/messages/after-last-user/{session_id}")
async def delete_messages_after_last_user(
    session_id: str,
    device_id: str = Header(..., alias="X-Device-ID"),
    db: Session = Depends(get_db)
):
    """Delete all messages after the last user message in a session"""
    try:
        # Validate session belongs to device
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.device_id != device_id:
            raise HTTPException(status_code=403, detail="Session does not belong to this device")
        
        # Find last user message
        last_user_message = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.role == "user"
        ).order_by(ChatMessage.created_at.desc()).first()
        
        if not last_user_message:
            return {"message": "No user messages found", "deleted_count": 0}
        
        # Delete all messages after (including) the last user message
        deleted = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.created_at >= last_user_message.created_at
        ).delete()
        
        db.commit()
        
        return {"message": "Messages deleted successfully", "deleted_count": deleted}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting messages: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete messages")
