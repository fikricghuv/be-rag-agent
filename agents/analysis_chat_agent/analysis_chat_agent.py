from openai import OpenAI
import logging

logger = logging.getLogger(__name__)
client = OpenAI()

def analysis_chat(message: str) -> str:
    
    prompt = f"""
    Berikut adalah isi pesan dari pengguna:
    \"\"\"{message}\"\"\"

    Tugas Anda adalah mengekstrak informasi pribadi (PII) dari pesan di atas jika ada.
    Format hasil harus JSON dengan struktur berikut:
    {{
    "full_name": <nama lengkap>,
    "email": <email>,
    "phone": <nomor telepon>,
    "address": <alamat>,
    "other_info": {{
        "dob": <tanggal lahir>,
        "id_number": <nomor identitas>,
        "place_of_birth": <tempat lahir>
    }}
    }}

    Jika tidak ditemukan, kembalikan nilai-nilai tersebut sebagai `null` atau kosong.
    Kembalikan HANYA JSON valid.
    """
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    # logger.info("result analysis_chat :", completion)
    return completion.choices[0].message.content