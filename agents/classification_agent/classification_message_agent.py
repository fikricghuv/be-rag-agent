from openai import OpenAI

client = OpenAI()

CLASSIFICATION_CATEGORIES = [
    "Sapa", "Informasi Umum", "Produk Asuransi Oto", "Produk Asuransi Asri",
    "Produk Asuransi Sepeda", "Produk Asuransi Apartemen", "Produk Asuransi Ruko",
    "Produk Asuransi Diri", "Claim", "Payment", "Policy", "Complaint", "Others"
]

def classify_chat_agent(response_text: str) -> str:
    
    prompt = f"""
    Kategorikan pesan ini ke salah satu kategori berikut:
    {', '.join(CLASSIFICATION_CATEGORIES)}

    Pesan: "{response_text}"

    Jawab hanya dengan 1 nama kategorinya saja. Pilih yang paling sesuai dengan konteks pesan di atas.
    """
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content.strip().lower()