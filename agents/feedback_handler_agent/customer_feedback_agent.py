from agno.agent import Agent
from agents.models.openai_model import openai_model
from core.settings import DB_NAME, USER_DB, PASSWORD_DB, HOST, PORT, SCHEMA_TABLE, OPEN_ROUTER_API_KEY
from textwrap import dedent
from agno.models.openrouter import OpenRouter

from agno.tools.postgres import PostgresTools

# Initialize PostgresTools with connection details
postgres_tools = PostgresTools(
    host=HOST,
    port=PORT,
    db_name=DB_NAME,
    user=USER_DB,
    password=PASSWORD_DB,
    table_schema=SCHEMA_TABLE,
)

query_sql = """
INSERT INTO ai.dt_customer_feedback(
        id, feedback_from_customer, sentiment, potential_actions, keyword_issue, created_at, category, product_name, email_user)
        VALUES (id, feedback_from_customer, sentiment, potential_actions, keyword_issue, created_at, category, product_name, email_user);
"""

customer_feedback_agent = Agent(
    name='Customer Feedback Agent',
    agent_id="customer_feedback_agent",
    # description="Handles customer feedback, analyzes sentiment, and provides actionable insights.",
    role="Record and analyze customer feedback/complaints.​",
    instructions=dedent("""
    ### Tujuan Agent:
    Menerima feedback, keluhan, atau saran dari pelanggan untuk di eskalasikan ke tim teknis.

    ### Alur Tugas:
    1. Terima input berupa komplain, feedback, atau saran dari pelanggan.
    2. Periksa apakah data berikut tersedia: 
        - Nama pelanggan (harus ada)
        - Alamat email (harus ada)
        - Nomor polis (optinal)
        - Nomor klaim (optinal)
        - Penjelasan masalah (harus ada)
    3. Jika ada data yang belum lengkap, ajukan pertanyaan lanjutan ke customer untuk melengkapinya.
    4. Setelah semua data terkumpul, simpan informasi tersebut ke database menggunakan tools postgres_tools.
    5. Tabel tujuan: `ai.dt_customer_feedback`

    ### Format query yang digunakan:
    Gunakan query berikut untuk menyimpan data:

    INSERT INTO ai.dt_customer_feedback(
        id, 
        feedback_from_customer, 
        sentiment, 
        potential_actions, 
        keyword_issue, 
        created_at, 
        category, 
        product_name, 
        email_user
    )
    VALUES (
        id, 
        feedback_from_customer, 
        sentiment, 
        potential_actions, 
        keyword_issue, 
        created_at, 
        category, 
        product_name, 
        email_user
    );

    - Lakukan analisis sentimen untuk mengisi kolom `sentiment`.
    - Klasifikasikan jenis masukan (misalnya: komplain, saran, masalah, feedback positif) untuk `category`.

    6. Setelah data berhasil disimpan, berikan balasan kepada customer bahwa masukan atau keluhan mereka sudah diterima dan telah diteruskan untuk penanganan lebih lanjut
        dan akan memberikan konfirmasi melalui email yang diberikan.

    ### Catatan:
    - Lakukan sesuai dengan tugas yang diberikan.
    - Simpan semua jenis masukan pelanggan, tidak hanya yang terkait klaim atau polis.
    - tidak perlu menjelaskan proses penyimpanan data kepada pelanggan seperti "Saya akan melakukan analisis dan menyimpan informasi ini ke dalam sistem kami. Mohon tunggu sebentar.".
    - Berikan jawaban yang singkat dan jelas.
    - Gunakan tools `postgres_tools.run_query` untuk mengeksekusi query.

    """),

    # role=role_agent,
    model=openai_model(),
    # model=OpenRouter(id="anthropic/claude-3.7-sonnet", api_key=OPEN_ROUTER_API_KEY),
    # tools=[insert_postgres_toolkit], #postgres_tools
    tools=[postgres_tools.run_query],
    tool_call_limit=3,
    show_tool_calls=True,
    add_context=True,
    debug_mode=True,
    markdown=True,
    add_history_to_messages=True,
    # goal="Record data, analyze customer feedback, complaints, or suggestions.",
)
