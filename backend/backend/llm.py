import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize the OpenAI client with custom base URL
API_KEY = os.getenv('NGU_API_KEY')
BASE_URL = os.getenv('NGU_BASE_URL')
LLM_MODEL = os.getenv('NGU_MODEL')

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
model_server = os.getenv('MODEL_SERVER')

def chat_with_llm(messages):
    """
    messages: a list of {"role": "user" | "assistant" | "system", "content": str}
    """
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        import traceback
        traceback.print_exc()  # Add this to print the full error stack trace
        print(f"Error from OpenAI: {e}")
        return f"OpenAI API error: {e}"  # Show actual error in the response



