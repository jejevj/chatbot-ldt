"""
Device management endpoints
"""
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import logging
import uuid

from app.database import get_db, Device
from app.schemas import DeviceRegisterRequest, DeviceRegisterResponse

router = APIRouter(prefix="/device", tags=["device"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=DeviceRegisterResponse)
async def register_device(
    request: DeviceRegisterRequest,
    user_agent: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Register or get device ID based on fingerprint"""
    try:
        # Check if device already registered
        device = db.query(Device).filter(
            Device.device_fingerprint == request.device_fingerprint
        ).first()
        
        if device:
            # Update last_seen
            device.last_seen_at = datetime.utcnow()
            device.user_agent = user_agent
            db.commit()
            return DeviceRegisterResponse(
                device_id=device.device_id,
                message="Device already registered"
            )
        
        # Create new device
        device_id = str(uuid.uuid4())
        now = datetime.utcnow()
        new_device = Device(
            device_id=device_id,
            device_fingerprint=request.device_fingerprint,
            user_agent=user_agent,
            created_at=now,
            last_seen_at=now
        )
        db.add(new_device)
        db.commit()
        db.refresh(new_device)
        
        return DeviceRegisterResponse(
            device_id=device_id,
            message="Device registered successfully"
        )
    
    except Exception as e:
        logger.error(f"Error in register_device: {str(e)}", exc_info=True)
        db.rollback()
        raise
