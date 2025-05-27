import os
import re
import traceback
from dotenv import load_dotenv
from openai import OpenAI
from duckduckgo_search import duckduckgo_search

# Load environment variables from .env file
load_dotenv()

# Environment configuration
API_KEY = os.getenv("NGU_API_KEY")
BASE_URL = os.getenv("NGU_BASE_URL")
LLM_MODEL = os.getenv("NGU_MODEL")
MODEL_SERVER = os.getenv("MODEL_SERVER")

# Initialize OpenAI-compatible client
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

def react_with_llm(messages, max_steps=3):
    """
    Chain-of-Thought + ReAct tool loop with fallback retry if LLM shows uncertainty.
    Allows the LLM to reason through a conversation, trigger tools like web search,
    then update the context and continue the conversation.

    Parameters:
    - messages (list): Conversation history in OpenAI format [{"role": "...", "content": "..."}]
    - max_steps (int): Maximum number of reasoning + tool steps allowed

    Returns:
    - str: Final assistant message after reasoning/tool usage
    """
    uncertain_phrases = [
        "i'm not sure", "i don't know", "i don't have enough information",
        "i cannot answer", "as an ai", "i cannot determine"
    ]

    for step in range(max_steps):
        try:
            # Ask the LLM
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.7
            )

            reply = response.choices[0].message.content
            messages.append({"role": "assistant", "content": reply})

            # If reply includes a tool trigger (e.g. Search[]), extract and call it
            if "Search[" in reply:
                match = re.search(r"Search\[(.*?)\]", reply)
                if match:
                    query = match.group(1)
                    search_result = duckduckgo_search(query)
                    tool_msg = (
                        f"Search Result for '{query}': {search_result.get('abstract') or 'No results found.'}"
                    )
                    messages.append({"role": "user", "content": tool_msg})
                    continue  # Retry with tool result in context

            # Retry if the LLM gives an uncertain or generic response
            if any(p in reply.lower() for p in uncertain_phrases):
                messages.append({"role": "user", "content": "Please try again with more detail."})
                continue

            break  # Break if no search or retry is needed

        except Exception as e:
            traceback.print_exc()
            return f"LLM error: {e}"

    return messages[-1]["content"]







