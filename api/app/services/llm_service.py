"""
LLM service for Qwen3 integration
"""
import httpx
import json
import logging
import re
from typing import List, Dict, Optional

from app.config import settings

logger = logging.getLogger(__name__)


async def generate_response(
    query: str,
    context: str,
    has_data: bool = True,
    chat_history: List[Dict] = None,
    available_categories: Optional[Dict] = None
) -> str:
    """
    Generate response using Qwen3

    Args:
        query: User query
        context: Retrieved data context
        has_data: Whether relevant data was found
        chat_history: Previous chat messages
        available_categories: Dict dengan key 'tipe_data' dan 'kategori_data'
                              berisi list nilai unik dari database.
                              Diisi saat has_data=False agar AI tetap bisa
                              menjelaskan data apa saja yang tersedia.

    Returns:
        Generated response text
    """
    messages = []

    # --- Bangun info kategori untuk sistem prompt ---
    category_info = ""
    if available_categories:
        tipe_list = available_categories.get("tipe_data", [])
        kategori_list = available_categories.get("kategori_data", [])
        if tipe_list or kategori_list:
            parts = []
            if tipe_list:
                parts.append("Tipe data: " + ", ".join(tipe_list))
            if kategori_list:
                parts.append("Kategori data: " + ", ".join(kategori_list))
            category_info = "\n\nINFO SISTEM - Data yang tersedia di Satu Data Pertahanan:\n" + "\n".join(parts)

    # --- System message ---
    system_msg = f"""Kamu adalah asisten virtual untuk sistem Satu Data Pertahanan {settings.ASSISTANT_SCOPE}.{category_info}

ATURAN:
1. JAWAB pertanyaan tentang data pertahanan dengan informatif dan membantu
2. TOLAK dengan sopan pertanyaan yang JELAS di luar konteks sistem (politik tidak terkait pertahanan, gosip artis, resep masakan, dll)
3. Jawaban RINGKAS tapi INFORMATIF (3-5 kalimat untuk pertanyaan umum, lebih detail jika diminta)
4. Untuk sapaan: jawab 1 kalimat saja
5. Jika ada daftar INFO SISTEM di atas, GUNAKAN informasi tersebut untuk menjawab pertanyaan umum tentang data yang tersedia

CARA MENJAWAB BERDASARKAN SITUASI:
- Ada data relevan diberikan → Jelaskan data tersebut secara informatif
- Tidak ada data, tapi pertanyaan umum ("data apa saja?", "kategori apa?") → Jelaskan dari INFO SISTEM
- Tidak ada data, pertanyaan spesifik → Sarankan kata kunci lain, sebutkan kategori yang ada
- Pertanyaan JELAS di luar topik data pertahanan → "Maaf, saya hanya dapat membantu pertanyaan seputar data pertahanan Kemhan RI. Ada yang bisa saya bantu terkait data pertahanan?"
- Sapaan → "Halo! Ada yang bisa saya bantu terkait data pertahanan?"

CONTOH PERTANYAAN YANG DIJAWAB:
- "Data apa saja yang tersedia?" → Sebutkan tipe dan kategori dari INFO SISTEM
- "Kirimkan data dengan kategori Statistik" → Jelaskan bahwa kategori tersebut tersedia / tidak tersedia berdasarkan INFO SISTEM
- "Ada data tentang alutsista?" → Jawab berdasarkan konteks data yang diberikan
- "Bagaimana cara akses data?" → Jelaskan dengan panduan singkat

PRIORITAS: Membantu pengguna memahami dan mengakses data pertahanan dengan efisien.
"""
    messages.append({"role": "system", "content": system_msg})

    # --- Tambahkan chat history ---
    if chat_history:
        for msg in chat_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

    # --- Bangun user message ---
    if has_data:
        user_content = f"""Data yang ditemukan dari sistem:

{context}

Pertanyaan: {query}

INSTRUKSI:
1. Jelaskan data di atas secara informatif dan relevan dengan pertanyaan
2. Jika ada beberapa data, ringkas dan highlight yang paling relevan
3. Jika data mungkin tidak exact match → Klarifikasi: "Saya menemukan data yang mungkin terkait:"
4. Selalu tampilkan informasi berguna: judul, kategori, tipe, deskripsi singkat
5. Jika pertanyaan JELAS di luar topik data pertahanan → Tolak dengan sopan

PENTING: Selalu tampilkan data yang ditemukan, biarkan user menilai relevansinya."""
    else:
        user_content = f"""Pertanyaan: {query}

SITUASI: Tidak ditemukan data yang cocok untuk keyword tersebut.

INSTRUKSI:
1. Jika HANYA sapaan ("Halo", "Hi", "Selamat pagi") → Jawab 1 kalimat singkat
2. Jika pertanyaan tentang DATA APA SAJA yang tersedia, atau KATEGORI/TIPE data → 
   Gunakan INFO SISTEM di system prompt untuk menjelaskan jenis-jenis data yang ada
3. Jika pertanyaan tentang kategori/tipe spesifik (contoh: "data kategori Statistik") → 
   Cek apakah ada di INFO SISTEM, lalu informasikan apakah tersedia dan sarankan mencari lebih spesifik
4. Jika pertanyaan tentang cara akses/cara mencari → Jelaskan dengan informatif
5. Jika pertanyaan spesifik tapi tidak ada data → Sarankan kata kunci alternatif berdasarkan INFO SISTEM
6. Jika pertanyaan JELAS di luar topik → "Maaf, saya hanya dapat membantu pertanyaan seputar data pertahanan Kemhan RI."

PENTING:
- Untuk pertanyaan umum tentang "data apa saja", LANGSUNG jelaskan dari INFO SISTEM. JANGAN minta kata kunci lebih spesifik.
- JANGAN awali jawaban dengan sapaan jika user sedang mengajukan pertanyaan.
- JANGAN bilang "saya tidak memiliki data" jika INFO SISTEM berisi kategori/tipe yang relevan."""

    messages.append({"role": "user", "content": user_content})

    # --- Panggil Qwen3 API ---
    async with httpx.AsyncClient(timeout=settings.QWEN_TIMEOUT) as client:
        try:
            payload = {
                "model": settings.QWEN_MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 800
            }

            payload_size = len(json.dumps(payload))
            logger.info(f"Qwen request size: {payload_size} bytes, messages: {len(messages)}")

            response = await client.post(
                settings.QWEN_API_URL,
                json=payload
            )
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"]

            # Hapus tag <think> (chain-of-thought Qwen3)
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
            logger.error(f"Response body: {e.response.text}")
            return "Maaf, terjadi kesalahan pada sistem AI. Silakan coba beberapa saat lagi."

        except Exception as e:
            logger.error(f"Unexpected error calling Qwen3: {str(e)}", exc_info=True)
            return "Maaf, terjadi kesalahan yang tidak terduga. Silakan coba lagi atau hubungi administrator jika masalah berlanjut."
