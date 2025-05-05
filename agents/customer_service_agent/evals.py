from agents.customer_service_agent.customer_service_agent import call_customer_service_agent
import asyncio

async def evaluate_relevance(agent, question, expected_keywords=[], not_expected_keywords=[]):
    """Evaluasi relevansi jawaban agent berdasarkan kata kunci yang diharapkan dan tidak diharapkan."""
    response = await agent.run(question)
    response_content = response.content.lower()
    relevance_score = 0

    for keyword in expected_keywords:
        if keyword.lower() in response_content:
            relevance_score += 1

    for keyword in not_expected_keywords:
        if keyword.lower() in response_content:
            relevance_score -= 1

    print(f"Pertanyaan: {question}")
    print(f"Jawaban: {response.content}")
    print(f"Skor Relevansi: {relevance_score}")
    return relevance_score

async def evaluate_completeness(agent, question, expected_answers_to=[]):
    """Evaluasi apakah agent menjawab semua bagian pertanyaan."""
    response = await agent.run(question)
    response_content = response.content.lower()
    completeness_score = 0
    num_expected = len(expected_answers_to)

    for expected_part in expected_answers_to:
        if expected_part.lower() in response_content:
            completeness_score += 1

    completeness_percentage = (completeness_score / num_expected) * 100 if num_expected > 0 else 100
    print(f"Pertanyaan: {question}")
    print(f"Jawaban: {response.content}")
    print(f"Skor Kelengkapan: {completeness_percentage:.2f}%")
    return completeness_percentage

async def evaluate_tool_usage(agent, question, expected_tool_names=[]):
    """Evaluasi apakah agent menggunakan alat yang diharapkan."""
    response = await agent.run(question)
    tool_names_used = [call.tool_call.name for call in response.tool_calls] if response.tool_calls else []
    tool_usage_score = all(expected_tool in tool_names_used for expected_tool in expected_tool_names)
    print(f"Pertanyaan: {question}")
    print(f"Jawaban: {response.content}")
    print(f"Alat yang Digunakan: {tool_names_used}")
    print(f"Penggunaan Alat yang Diharapkan: {tool_usage_score}")
    return tool_usage_score

# Contoh Penggunaan Evaluasi
async def main_evaluation():
    session_id = "test_session"
    user_id = "test_user"
    agent = call_customer_service_agent(session_id, user_id)

    # Evaluasi Relevansi
    await evaluate_relevance(
        agent,
        "Apa saja produk yang ada?",
        expected_keywords=["produk", "asuransi"]
    )

    await evaluate_relevance(
        agent,
        "Bagaimana cara klaim polis?",
        expected_keywords=["claim", "klaim", "polis"],
        not_expected_keywords=["pembelian", "harga"]
    )

    # Evaluasi Kelengkapan
    await evaluate_completeness(
        agent,
        "Saya ingin tahu tentang asuransi mobil",
        expected_answers_to=["mobil", "kendaraan", "asuransi"]
    )

    # Evaluasi Penggunaan Alat (asumsi Anda tahu alat mana yang seharusnya dipanggil)
    await evaluate_tool_usage(
        agent,
        "saya punya keluhan tentang klaim polis saya, email saya fikcg@gmail.com",
        expected_tool_names=["TelegramTools"] # Ganti dengan nama alat yang sesuai
    )

if __name__ == "__main__":
    asyncio.run(main_evaluation())