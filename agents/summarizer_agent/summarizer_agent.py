from openai import OpenAI

client = OpenAI()

def evaluate_answer(response_text: str) -> str:
    
    prompt = f"""
    
    """
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content.strip().lower()