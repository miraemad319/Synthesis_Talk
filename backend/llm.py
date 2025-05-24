import os
from openai import OpenAI
from dotenv import load_dotenv
from duckduckgo_search import duckduckgo_search

load_dotenv()

# Initialize the OpenAI client with custom base URL
API_KEY = os.getenv('NGU_API_KEY')
BASE_URL = os.getenv('NGU_BASE_URL')
LLM_MODEL = os.getenv('NGU_MODEL')

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
model_server = os.getenv('MODEL_SERVER')


def react_with_llm(messages, max_steps=3):
    for step in range(max_steps):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.7
            )
            reply = response.choices[0].message.content
            messages.append({"role": "assistant", "content": reply})

            # Check if LLM suggests an action like Search[query]
            if "Search[" in reply:
                import re
                match = re.search(r"Search\[(.*?)\]", reply)
                if match:
                    query = match.group(1)
                    search_result = duckduckgo_search(query)
                    tool_msg = f"Search Result for '{query}': {search_result.get('abstract') or 'No results found.'}"
                    messages.append({"role": "user", "content": tool_msg})
                    continue  # LLM will now see the result and reason again
            break  # If no action needed, stop loop

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"LLM error: {e}"
    return messages[-1]["content"]



