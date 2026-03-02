from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.responses.create(
model="gpt-4.1-mini",
input="Hello! Confirm my OpenAI setup works."
)

print(response.output_text)