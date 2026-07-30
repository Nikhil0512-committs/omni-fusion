import os
import google.generativeai as genai
from PIL import Image

api_key = os.popen("grep GEMINI_API_KEY backend/.env | cut -d '=' -f2").read().strip()
genai.configure(api_key=api_key)

for m in genai.list_models():
    print(m.name)




