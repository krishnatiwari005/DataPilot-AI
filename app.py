from agno.agent import Agent
from agno.models.groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

api_key=os.getenv("GROQ_API_KEY","").strip()

llm=Groq(id="",api_key=api_key)

