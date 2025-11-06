import config
from google import genai
import os
import google

api_key = config.GOOGLE_VERTEX_API_KEY
print(config.GOOGLE_VERTEX_API_KEY)

creds, _ = google.auth.load_credentials_from_file("white-academy-476808-f4-ecc4626c3715.json")

client = genai.Client(credentials=creds)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="explain nextflow in 2 paragraphs, what's the current version?"
)

print(response.text)