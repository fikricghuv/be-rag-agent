from agents.models.openai_model import openai_model
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.memory.db.postgres import PgMemoryDb, MemoryDb
from utils.get_instruction_from_db import get_instructions_from_db
from core.settings import URL_DB_POSTGRES, OPEN_ROUTER_API_KEY
from utils.get_knowledge_base_param import get_knowledge_base_config
from agents.product_information_agent.product_information_agent import product_information_agent
from agents.feedback_handler_agent.customer_feedback_agent import customer_feedback_agent
from agents.general_information_insurance_agent.general_insurance_information_agent import general_insurance_information_agent
from agno.team.team import Team, TeamMemory
from textwrap import dedent
from agno.models.openrouter import OpenRouter

instructions_from_db = get_instructions_from_db('Customer Service Agent')
kb_config = get_knowledge_base_config()

storage = PostgresAgentStorage(
    # store sessions in the ai.sessions table
    table_name="agent_sessions",
    # db_url: Postgres database URL
    db_url=URL_DB_POSTGRES,
)

# Inisialisasi agen
def call_agent(session_id, user_id) :

    customer_service_agent = Team(
        members=[product_information_agent, customer_feedback_agent], #, general_insurance_information_agent
        # mode="coordinate",
        mode="route",
        model=openai_model(),
        # model=OpenRouter(id="anthropic/claude-3.7-sonnet", api_key=OPEN_ROUTER_API_KEY),
        name='Customer Service Team',
        team_id="customer_service_team",
        user_id=user_id,
        session_id=session_id,
        description="You are a Customer Service Team to delegate question and information about BRI INSURANCE products to appropriate agent.",
        instructions=dedent("""
        ### Peran Anda:
        Anda adalah pemimpin dari Customer Service Team untuk menangani berbagai jenis pertanyaan dari pelanggan seputar produk BRI INSURANCE dan mengarahkan setiap pertanyaan atau masukan ke agent yang paling tepat.

        ### Tugas Utama:
        - Menganalisis isi pertanyaan atau masukan dari customer.
        - Mengklasifikasikan topik atau jenis pertanyaan.
        - Mengarahkan pertanyaan tersebut ke agent spesifik sesuai dengan klasifikasinya.
        - Menjaga percakapan tetap sopan, profesional, dan ramah seperti layaknya customer service manusia.

        ### Alur Routing:
        1. **Informasi Produk BRI INSURANCE**
            → Rute ke: **Product Information Agent**
            → Contoh: "Apa saja manfaat dari produk X?", "Bagaimana cara membeli produk Y?"

        2. **Masalah / Komplain / Feedback / Saran**
            → Rute ke: **Customer Feedback Agent**
            → Contoh: "Saya mengalami masalah klaim.", "Aplikasi tidak bisa dibuka.", "Saya punya saran untuk layanan customer care."

        3. **Pertanyaan Umum tentang Asuransi**
            → Rute ke: **Product Information Agent**
            → Contoh: "Apa itu asuransi all risk?", "Bagaimana cara kerja asuransi kendaraan?"

        ### Panduan Interaksi:
        - Jika ada pertanyaan yang mengandung beberapa topik, rute satu per satu ke agent yang sesuai.
        - Jelaskan secara singkat kepada customer bahwa permintaan mereka sedang dialihkan ke bagian yang relevan.
        - Jika pertanyaannya tidak relevan dengan BRI INSURANCE, jawab dengan sopan bahwa Anda hanya dapat membantu terkait layanan BRI INSURANCE.
        
        ### Penting:
        - Jangan menjawab pertanyaan yang bukan terkait BRI INSURANCE.
        - Delegasikan pertanyaan ke agent yang sesuai.
        - Tidak perlu memberikan jawaban kepada user jika ada agent yang didelegasikan yang menjawab.
        - Fokus pada memberikan respon yang alami, tidak seperti robot.
        - Jaga akurasi routing demi kepuasan pelanggan.

        """),

        debug_mode=True,
        show_tool_calls=True,
        memory=TeamMemory(
            user_id=user_id,
            db=PgMemoryDb(
                table_name="agent_memory", 
                db_url=URL_DB_POSTGRES), 
            create_user_memories=True,
            updating_memory=True,
        ),
        storage=storage,
        markdown=True,
        enable_agentic_context=True,  # Allow the agent to maintain a shared context and send that to members.
        # share_member_interactions=True,  # Share all member responses with subsequent member requests.
        # show_members_responses=True,
        read_team_history=True,
        # enable_team_history=True,
        # telemetry=False,
        # expected_output="Delegate task to appropriate agent.",
        
    )

    return customer_service_agent