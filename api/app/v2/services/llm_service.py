"""
LLM service — call Qwen via OpenAI-compatible API
"""
import httpx
import logging
from typing import List, Dict
from app.config import settings
from app.v2.config import v2_settings

logger = logging.getLogger(__name__)


async def call_llm(messages: List[Dict[str, str]], temperature: float = 0.3) -> str:
    """
    Kirim messages ke Qwen API dan kembalikan teks jawaban.
    Format OpenAI-compatible.
    """
    payload = {
        "model": settings.QWEN_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 1024,
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.QWEN_TIMEOUT) as client:
            response = await client.post(settings.QWEN_API_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        logger.error(f"LLM HTTP error: {e.response.status_code} — {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"LLM error: {str(e)}")
        raise
