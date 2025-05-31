# backend/llm.py

import os
import time
import json
import logging
from openai import OpenAI, OpenAIError
from fastapi import HTTPException

# Load your environment variables
API_KEY   = os.getenv("NGU_API_KEY")
BASE_URL  = os.getenv("NGU_BASE_URL")
LLM_MODEL = os.getenv("NGU_MODEL")

# A comprehensive system prompt for all replies (paragraphs, bullets, MCQs, docs, no typos, etc.)
SYSTEM_PROMPT = """
You are a highly accurate and careful research assistant. Follow these guidelines in every reply:

1. GENERAL STYLE:
   • Write complete sentences with correct spelling—avoid all typos.
   • Organize responses into paragraphs separated by a single blank line.
   • For bullet lists, format as:
         - First bullet
         - Second bullet
         - Third bullet
     with a blank line before and after the list.

2. MULTIPLE-CHOICE QUESTIONS (MCQs):
   Only if the user explicitly asks for “multiple‐choice questions,” format them exactly as:
      1. Question text
         (A) Option A
         (B) Option B
         (C) Option C
         (D) Option D

      2. Next question text
         (A) Option A
         (B) Option B
         (C) Option C
         (D) Option D

   Leave a blank line between each numbered question. Use plain text—no extra Markdown.

3. REFERENCING DOCUMENTS:
   Always read any “system” message labeled “Relevant documents:” and use that context verbatim. 
   If you cannot answer using those chunks, respond: “I’m sorry, I don’t have that information.”

4. LENGTH & CLARITY:
   If a paragraph is too long, break it into multiple paragraphs. Use line breaks.
   For code snippets (if requested), enclose them in triple backticks (```).

5. SELF‐CRITIQUE:
   After generating your initial answer, review it for any mistakes or typos. If you find any, correct them. 
   If it is already accurate, simply restate it.

Always follow these rules exactly.
"""

def trim_history(history: list[dict], max_chars: int = 20000) -> list[dict]:
    """
    Naively trim conversation history (by character count) so that 
    the total content length stays under max_chars, preserving the latest messages.
    """
    total_chars = sum(len(m["content"]) for m in history)
    while total_chars > max_chars and len(history) > 1:
        removed = history.pop(0)
        total_chars -= len(removed["content"])
    return history

def react_with_llm(conversation_history: list[dict]) -> str:
    """
    1) Prepend SYSTEM_PROMPT
    2) Trim history to avoid token overflow
    3) Send initial request with explicit parameters
    4) Self‐critique step to correct typos or mistakes
    5) Return the final, cleaned answer
    """
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    # 1) Build full message list: SYSTEM_PROMPT + user/system/assistant messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    # 2) Trim by character count (approximate tokens) to stay under context window
    messages = trim_history(messages, max_chars=20000)

    # 3) Make initial LLM call with retry logic
    max_retries = 3
    backoff = 1

    for attempt in range(max_retries):
        try:
            # Estimate tokens roughly for logging (approx. 4 characters = 1 token)
            token_estimate = sum(len(m["content"]) for m in messages) // 4
            logging.info(f"[LLM] Sending {len(messages)} messages (~{token_estimate} tokens) to model.")

            start_time = time.time()
            init_resp = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.2,       # Low to reduce hallucinations
                max_tokens=1024,       # Cap response length
                top_p=0.9,             # Nucleus sampling
                frequency_penalty=0.0, # No repetition penalty
                presence_penalty=0.0,  # No new topic penalty
            )
            latency = time.time() - start_time

            initial_answer = init_resp.choices[0].message["content"]
            finish_reason = init_resp.choices[0].finish_reason
            logging.info(f"[LLM] Received initial response (reason={finish_reason}) in {latency:.2f}s.")
            break

        except OpenAIError as e:
            logging.error(f"[LLM] Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(backoff * (2 ** attempt))  # 1s, 2s, 4s backoff
                continue
            else:
                raise HTTPException(status_code=500, detail=f"LLM API error: {e}")
    else:
        # If we somehow exit the loop without breaking, abort
        raise HTTPException(status_code=500, detail="LLM call failed after retries.")

    # 4) SELF‐CRITIQUE: Ask the model to check and correct its own output
    critique_prompt = (
        "Please review your previous answer carefully. Correct any mistakes or typos. "
        "If it is already accurate, restate it exactly."
    )
    critique_history = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + conversation_history
        + [{"role": "assistant", "content": initial_answer},
           {"role": "user", "content": critique_prompt}]
    )

    critique_history = trim_history(critique_history, max_chars=20000)

    try:
        start_time = time.time()
        crit_resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=critique_history,
            temperature=0.2,
            max_tokens=512,
            top_p=0.9,
        )
        critique_latency = time.time() - start_time
        final_answer = crit_resp.choices[0].message["content"]
        logging.info(f"[LLM] Received critique response in {critique_latency:.2f}s.")
    except OpenAIError as e:
        logging.error(f"[LLM] Critique call failed: {e} - returning initial answer.")
        final_answer = initial_answer

    return final_answer








