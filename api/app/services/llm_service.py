"""
LLM service for Qwen3 integration
"""
import httpx
import logging
import re
from typing import List, Dict

from app.config import settings

logger = logging.getLogger(__name__)


async def generate_response(
    query: str,
    context: str,
    has_data: bool = True,
    chat_history: List[Dict] = None
) -> str:
    """
    Generate response using Qwen3
    
    Args:
        query: User query
        context: Retrieved data context
        has_data: Whether relevant data was found
        chat_history: Previous chat messages
        
    Returns:
        Generated response text
    """
    messages = []
    
    # System message - more strict
    system_msg = f"""Kamu adalah asisten virtual untuk sistem Satu Data Pertahanan {settings.ASSISTANT_SCOPE}. 

ATURAN KETAT:
1. HANYA jawab pertanyaan tentang data pertahanan yang tersedia di sistem
2. TOLAK dengan sopan pertanyaan di luar konteks (politik, agama, gosip, nama orang terkenal, dll)
3. Jawaban RINGKAS dan TO THE POINT (maksimal 3-4 kalimat kecuali diminta detail)
4. Untuk sapaan: jawab 1 kalimat saja

CARA MENJAWAB:
- Ada data relevan → Jelaskan singkat dan jelas
- Tidak ada data → Sarankan kata kunci lain atau konfirmasi maksud pertanyaan
- Pertanyaan di luar topik → "Maaf, saya hanya dapat membantu pertanyaan seputar data pertahanan Kemhan RI. Ada yang bisa saya bantu terkait data pertahanan?"
- Sapaan → "Halo! Ada yang bisa saya bantu terkait data pertahanan?"

CONTOH PERTANYAAN YANG DITOLAK:
- "Siapa presiden Indonesia?" → TOLAK
- "Apa itu cinta?" → TOLAK  
- "Ceritakan tentang [nama orang]" → TOLAK
- "Bagaimana cara masak nasi?" → TOLAK

PRIORITAS: Efisien, ringkas, fokus pada data pertahanan.
"""
    messages.append({"role": "system", "content": system_msg})
    
    # Add chat history
    if chat_history:
        for msg in chat_history:  # Gunakan semua history yang diambil
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Build user message
    if has_data:
        user_content = f"""Data yang ditemukan:

{context}

Pertanyaan: {query}

Chat history tersedia untuk konteks.

INSTRUKSI:
1. Jika pertanyaan tentang data yang ditemukan → Jawab RINGKAS (3-4 kalimat)
2. Jika follow-up dari chat sebelumnya → Gunakan konteks, jawab singkat
3. Jika pertanyaan JELAS di luar topik data pertahanan → Tolak dengan template: "Maaf, saya hanya dapat membantu pertanyaan seputar data pertahanan Kemhan RI. Ada yang bisa saya bantu terkait data pertahanan?"
4. Fokus pada informasi penting: kategori, tipe, kegunaan data
5. TIDAK PERLU sebutkan URL atau sumber

Jawab SINGKAT dan JELAS."""
    else:
        user_content = f"""Pertanyaan: {query}

SITUASI: Tidak ada data yang match dengan keyword pencarian.

Chat history tersedia untuk konteks.

INSTRUKSI:
1. Jika sapaan → Jawab 1 kalimat: "Halo! Ada yang bisa saya bantu terkait data pertahanan?"
2. Jika pertanyaan di luar topik data pertahanan → Tolak: "Maaf, saya hanya dapat membantu pertanyaan seputar data pertahanan Kemhan RI. Ada yang bisa saya bantu terkait data pertahanan?"
3. Jika pertanyaan mungkin relevan tapi tidak ada data → Sarankan kata kunci lain dengan SINGKAT
4. Gunakan bahasa natural tapi RINGKAS

Jawab MAKSIMAL 2 kalimat."""
    
    messages.append({"role": "user", "content": user_content})
    
    # Call Qwen3 API
    async with httpx.AsyncClient(timeout=settings.QWEN_TIMEOUT) as client:
        try:
            response = await client.post(
                settings.QWEN_API_URL,
                json={
                    "model": settings.QWEN_MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 3000
                }
            )
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"]
            
            # Remove <think> tags
            answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL)
            answer = answer.strip()
            
            return answer
        
        except httpx.ConnectError:
            logger.error("Cannot connect to Qwen3 service")
            return "Maaf, saat ini sistem AI sedang tidak tersedia. Silakan coba beberapa saat lagi atau hubungi administrator."
        
        except httpx.TimeoutException:
            logger.error("Qwen3 request timeout")
            return "Maaf, permintaan memakan waktu terlalu lama. Silakan coba lagi dengan pertanyaan yang lebih spesifik."
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Qwen3 HTTP error: {e.response.status_code}")
            return "Maaf, terjadi kesalahan pada sistem AI. Silakan coba beberapa saat lagi."
        
        except Exception as e:
            logger.error(f"Unexpected error calling Qwen3: {str(e)}", exc_info=True)
            return "Maaf, terjadi kesalahan yang tidak terduga. Silakan coba lagi atau hubungi administrator jika masalah berlanjut."
