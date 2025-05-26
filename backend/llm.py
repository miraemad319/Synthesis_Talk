import os
import re
import traceback
from dotenv import load_dotenv
from openai import OpenAI
from duckduckgo_search import duckduckgo_search

# Load environment variables from .env file (API keys, model, etc.)
load_dotenv()

# Read required environment variables
API_KEY = os.getenv("NGU_API_KEY")
BASE_URL = os.getenv("NGU_BASE_URL")
LLM_MODEL = os.getenv("NGU_MODEL")
MODEL_SERVER = os.getenv("MODEL_SERVER")

# Initialize the OpenAI-compatible client
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

def react_with_llm(messages, max_steps=3):
    """
    A Chain-of-Thought + Tool-Use Reasoning loop.
    Allows the LLM to reason through a conversation, trigger tools like web search,
    then update the context and continue the conversation.

    Parameters:
    - messages (list): Conversation history in OpenAI format [{"role": "...", "content": "..."}]
    - max_steps (int): Maximum number of reasoning + tool steps allowed

    Returns:
    - str: Final assistant message after reasoning/tool usage
    """
    for step in range(max_steps):
        try:
            # Call the LLM with the current conversation context
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.7  # Introduces slight variation in responses
            )

            # Get the LLM's reply
            reply = response.choices[0].message.content
            messages.append({"role": "assistant", "content": reply})

            # Tool trigger pattern: Search[Some Query]
            if "Search[" in reply:
                match = re.search(r"Search\[(.*?)\]", reply)
                if match:
                    query = match.group(1)

                    # Use DuckDuckGo to search for the query
                    search_result = duckduckgo_search(query)

                    # Format search result as a user message to feed back to LLM
                    tool_msg = (
                        f"Search Result for '{query}': "
                        f"{search_result.get('abstract') or 'No results found.'}"
                    )
                    messages.append({"role": "user", "content": tool_msg})

                    # Loop again — LLM will now reason with new info
                    continue

            # If no tool was triggered, stop the loop
            break

        except Exception as e:
            traceback.print_exc()
            return f"LLM error: {e}"

    # Return the final assistant reply
    return messages[-1]["content"]



