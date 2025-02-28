import os
from langchain_google_genai import GoogleGenerativeAI, ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings, HarmBlockThreshold, HarmCategory



from config.config import GEMINI_FLASH_LITE_001_MODEL, GEMINI_PRO_002_MODEL, GEMINI_EMBEDDINGS_MODEL


api_key = "AIzaSyDGnj-q426jslevxhFKfYW2es2udxyWOEU"

safety_settings = {
    HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

gemini_flash_llm = GoogleGenerativeAI(
    model=GEMINI_FLASH_LITE_001_MODEL,
    google_api_key = api_key,
    temperature=0.1,
    max_tokens=8192,
    verbose=True,
    timeout=None,
    max_retries=2,
    safety_settings = safety_settings
)

gemini_pro_llm = GoogleGenerativeAI(
    model=GEMINI_PRO_002_MODEL,
    google_api_key = api_key,
    temperature=0.1,
    max_tokens=8192,
    verbose=True,
    timeout=None,
    max_retries=2,
    safety_settings = safety_settings
)

gemini_embeddings = GoogleGenerativeAIEmbeddings(model=GEMINI_EMBEDDINGS_MODEL, google_api_key = api_key)