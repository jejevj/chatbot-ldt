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

PRINSIP UTAMA:
1. Fokus membantu pengguna menemukan dan memahami data pertahanan yang tersedia
2. Gunakan konteks percakapan untuk memahami pertanyaan follow-up
3. Jika data relevan ditemukan, jelaskan dengan detail dan informatif
4. Jika pertanyaan jelas di luar topik data pertahanan (nama orang, tempat umum, dll), arahkan kembali dengan sopan
5. Untuk sapaan, jawab singkat dan ramah

CARA MENILAI RELEVANSI:
- Pertanyaan tentang data yang baru disebutkan = RELEVAN
- Pertanyaan follow-up tentang detail/deskripsi = RELEVAN  
- Pertanyaan dengan keyword yang match dengan data = RELEVAN
- Pertanyaan tentang orang/tempat yang tidak ada di data = TIDAK RELEVAN
- Sapaan umum = NETRAL (jawab singkat)

Gunakan penilaian kontekstual, bukan aturan kaku. Prioritaskan membantu pengguna.
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
1. Baca pertanyaan dan pahami maksudnya dalam konteks percakapan
2. Jika pertanyaan adalah follow-up dari percakapan sebelumnya (misalnya "berikan deskripsi lengkapnya", "jelaskan lebih detail"), gunakan konteks untuk memahami data mana yang dimaksud
3. Jika pertanyaan jelas relevan dengan data yang diberikan, jawab dengan detail dan informatif
4. Jika pertanyaan JELAS tidak ada hubungannya dengan data (misalnya tanya nama orang yang tidak ada di data), katakan dengan sopan bahwa itu di luar konteks
5. Jelaskan kategori, tipe, deskripsi, dan kegunaan data dengan bahasa yang mudah dipahami
6. URL sudah tersedia di sumber data, tidak perlu disebutkan dalam jawaban

Prioritaskan membantu pengguna memahami data yang tersedia."""
    else:
        user_content = f"""Pertanyaan: {query}

SITUASI: Tidak ada data yang match dengan keyword pencarian.

Chat history tersedia untuk konteks.

INSTRUKSI:
1. Pahami maksud pertanyaan dalam konteks percakapan
2. Jika ini sapaan atau small talk:
   - Balas dengan ramah dan singkat
   - Tanyakan apa yang bisa dibantu terkait data pertahanan
3. Jika pertanyaan tentang hal di luar data pertahanan (nama orang, tempat umum, topik lain):
   - Jelaskan dengan sopan bahwa sistem ini untuk data pertahanan Kemhan
   - Arahkan untuk bertanya tentang data yang tersedia
4. Jika pertanyaan mungkin relevan tapi tidak ada data yang cocok:
   - Sarankan menggunakan kata kunci yang lebih spesifik
   - Atau tanyakan apakah maksudnya tentang topik tertentu

Gunakan bahasa yang natural dan membantu."""
    
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
                    "max_tokens": 2000
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
