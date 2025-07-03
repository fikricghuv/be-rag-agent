from openai import OpenAI

client = OpenAI()

# def speech_to_text(path_file):
    
#     with open(path_file, "rb") as audio_file:
#         transcription = client.audio.transcriptions.create(
#             model="whisper-1",  
#             file=audio_file,
#             response_format="text",  
#             language="id"
#         )
#     return transcription

from agno.media import Audio
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def speech_to_text(file_bytes):
    agentTranscriber = Agent(
        model=OpenAIChat(id="gpt-4o-audio-preview", modalities=["text"]),
        markdown=True,
    )
    transcribe = agentTranscriber.run(
        "translate ini kedalam bahasa indonesia, untuk diolah customer service agent.", audio=[Audio(content=file_bytes, format="wav")]
    )
    return transcribe
