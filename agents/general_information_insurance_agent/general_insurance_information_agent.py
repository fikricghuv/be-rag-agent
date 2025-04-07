from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from models.openai_model import openai_model

general_insurance_information_agent = Agent(
    name='General Inusrance Information Agent',
    agent_id="general_insurance_information_agent",
    description="Anda adalah Agen General Inusrance Informasi Produk yang memberikan detail tentang definisi umum asuransi",
    model=openai_model(temperature=0.7),
    tools=[DuckDuckGoTools()],
    instructions=
    [
        "hanya menjawab pertanyaan terkait informasi umum asuransi.",
        "Berikan informasi tentang definisi umum asuransi.",
        "Jika diperlukan, lakukan pencarian web untuk mendapatkan informasi terbaru."
    ],
    debug_mode=True,
    show_tool_calls=True,
)