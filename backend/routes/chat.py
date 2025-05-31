# backend/routes/chat.py

from fastapi import APIRouter, Request, HTTPException, Body, Cookie
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import logging
import json
import re

from backend.utils.session_store import conversation_histories, document_store, persist
from backend.utils.helpers import extract_search_query
from backend.utils.concept_linker import find_relevant_chunks
from backend.llm import react_with_llm
from backend.duckduckgo_search import duckduckgo_search

logging.basicConfig(level=logging.INFO)
router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    use_reasoning: Optional[bool] = True

class ReActStep(BaseModel):
    thought: str
    action: str
    action_input: str
    observation: str

def extract_react_steps(llm_response: str) -> List[ReActStep]:
    """
    Parse ReAct-style reasoning steps from LLM response.
    Expected format:
    Thought: <reasoning>
    Action: <action_name>
    Action Input: <input>
    Observation: <result>
    """
    steps = []
    lines = llm_response.split('\n')
    current_step = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('Thought:'):
            current_step['thought'] = line[8:].strip()
        elif line.startswith('Action:'):
            current_step['action'] = line[7:].strip()
        elif line.startswith('Action Input:'):
            current_step['action_input'] = line[13:].strip()
        elif line.startswith('Observation:'):
            current_step['observation'] = line[12:].strip()
            # Complete step
            if all(k in current_step for k in ['thought', 'action', 'action_input', 'observation']):
                steps.append(ReActStep(**current_step))
                current_step = {}
    
    return steps

def execute_action(action: str, action_input: str, session_id: str) -> str:
    """
    Execute a specific action and return the observation.
    """
    try:
        if action.lower() == "search":
            return duckduckgo_search(action_input)
        elif action.lower() == "document_search":
            docs = document_store.get(session_id, [])
            relevant = find_relevant_chunks(action_input, docs, top_k=3)
            if relevant:
                return "\n".join(f"[{fname}] {chunk[:200]}..." for chunk, fname in relevant)
            return "No relevant documents found."
        elif action.lower() == "summarize":
            docs = document_store.get(session_id, [])
            if docs:
                all_text = "\n".join(chunk for chunk, _, _ in docs)
                return f"Document summary: {all_text[:500]}..."
            return "No documents to summarize."
        elif action.lower() == "clarify":
            return f"Let me clarify: {action_input}"
        else:
            return f"Unknown action: {action}"
    except Exception as e:
        return f"Action execution failed: {str(e)}"

def chain_of_thought_reasoning(message: str, context: List[Dict]) -> str:
    """
    Implement Chain of Thought reasoning for complex queries.
    """
    cot_prompt = f"""
    Let's think step by step about this question: "{message}"

    Please break down your reasoning process:
    1. What is the user really asking?
    2. What information do I have available?
    3. What steps should I take to answer thoroughly?
    4. What is my conclusion?

    Based on the conversation context, provide a thoughtful response.
    """
    
    cot_messages = context + [{"role": "user", "content": cot_prompt}]
    return react_with_llm(cot_messages)

def react_reasoning(message: str, session_id: str, context: List[Dict]) -> tuple[str, List[ReActStep]]:
    """
    Implement ReAct (Reasoning + Acting) pattern for tool-enhanced responses.
    """
    react_prompt = f"""
    You are a research assistant with access to tools. Use the ReAct pattern to answer this query: "{message}"

    Available actions:
    - search: Search the web for information
    - document_search: Search uploaded documents for relevant content
    - summarize: Summarize available documents
    - clarify: Ask for clarification or provide explanations

    Use this format for each step:
    Thought: [your reasoning about what to do next]
    Action: [action name]
    Action Input: [input for the action]
    Observation: [result of the action]

    Continue until you have enough information to provide a complete answer.
    Then provide your Final Answer.
    """
    
    react_messages = context + [{"role": "user", "content": react_prompt}]
    llm_response = react_with_llm(react_messages)
    
    # Execute actions and update observations
    steps = []
    lines = llm_response.split('\n')
    current_step = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('Thought:'):
            current_step['thought'] = line[8:].strip()
        elif line.startswith('Action:') and 'thought' in current_step:
            current_step['action'] = line[7:].strip()
        elif line.startswith('Action Input:') and 'action' in current_step:
            current_step['action_input'] = line[13:].strip()
            # Execute the action
            observation = execute_action(
                current_step['action'], 
                current_step['action_input'], 
                session_id
            )
            current_step['observation'] = observation
            steps.append(ReActStep(**current_step))
            current_step = {}
    
    # Generate final response with all observations
    final_context = "\n".join([
        f"Thought: {step.thought}\nAction: {step.action}\nObservation: {step.observation}"
        for step in steps
    ])
    
    final_prompt = f"""
    Based on this reasoning process:
    {final_context}
    
    Original question: {message}
    
    Provide a comprehensive final answer that synthesizes all the information gathered.
    """
    
    final_response = react_with_llm([{"role": "user", "content": final_prompt}])
    
    return final_response, steps

def self_correction_check(response: str, original_query: str) -> str:
    """
    Implement self-correction mechanism to verify and improve responses.
    """
    correction_prompt = f"""
    Please review this response for accuracy and completeness:
    
    Original Query: {original_query}
    Response: {response}
    
    Check for:
    1. Does the response actually answer the question?
    2. Is the information accurate and consistent?
    3. Are there any logical gaps or contradictions?
    4. Could the response be clearer or more helpful?
    
    If improvements are needed, provide a corrected version. Otherwise, confirm the response is good.
    Start with either "CORRECTION NEEDED:" or "RESPONSE CONFIRMED:"
    """
    
    try:
        correction_result = react_with_llm([{"role": "user", "content": correction_prompt}])
        
        if correction_result.startswith("CORRECTION NEEDED:"):
            return correction_result[18:].strip()  # Return corrected version
        else:
            return response  # Original response was fine
    except Exception as e:
        logging.error(f"Self-correction failed: {e}")
        return response  # Fall back to original response

@router.post("/chat/")
async def chat(
    request: Request,
    chat_request: ChatRequest = Body(...),
    session_id: Optional[str] = Cookie(default=None)
):
    """
    Enhanced chat endpoint with advanced reasoning capabilities.
    """
    user_message = chat_request.message
    use_reasoning = chat_request.use_reasoning

    # Create new session if needed
    is_new_session = False
    if session_id is None:
        session_id = str(uuid.uuid4())
        is_new_session = True
        logging.info(f"[CHAT] New session started: {session_id}")

    logging.info(f"[CHAT] Session {session_id} | User: {user_message}")

    # Initialize conversation history
    if session_id not in conversation_histories:
        conversation_histories[session_id] = []

    # Add user message to history
    conversation_histories[session_id].append({"role": "user", "content": user_message})

    try:
        # Handle web search if requested
        search_query = extract_search_query(user_message)
        if search_query:
            search_results = duckduckgo_search(search_query)
            conversation_histories[session_id].append({
                "role": "system", 
                "content": f"Search results for '{search_query}':\n{search_results}"
            })
            logging.info(f"[CHAT] Web search context added for: {search_query}")

        # Add relevant document context
        docs = document_store.get(session_id, [])
        if docs:
            # Handle new document format with metadata
            doc_chunks = [(chunk, fname) for chunk, fname, _ in docs] if docs and len(docs[0]) == 3 else docs
            relevant = find_relevant_chunks(user_message, doc_chunks)
            
            if relevant:
                doc_context = "\n".join(f"[From {fname}]\n{chunk}" for chunk, fname in relevant)
                doc_context = doc_context[:2000]  # Truncate if too long
                conversation_histories[session_id].append({
                    "role": "system",
                    "content": f"Relevant documents:\n{doc_context.strip()}"
                })
                logging.info(f"[CHAT] Document context added ({len(relevant)} chunks)")

        # Determine reasoning approach
        reasoning_steps = []
        
        if use_reasoning and any(keyword in user_message.lower() for keyword in 
                               ['analyze', 'compare', 'explain', 'research', 'find', 'search']):
            # Use ReAct for complex queries that might need tools
            assistant_reply, reasoning_steps = react_reasoning(
                user_message, session_id, conversation_histories[session_id]
            )
            logging.info(f"[CHAT] Used ReAct reasoning with {len(reasoning_steps)} steps")
        elif use_reasoning and any(keyword in user_message.lower() for keyword in 
                                 ['why', 'how', 'what if', 'because']):
            # Use Chain of Thought for reasoning-heavy questions
            assistant_reply = chain_of_thought_reasoning(user_message, conversation_histories[session_id])
            logging.info("[CHAT] Used Chain of Thought reasoning")
        else:
            # Standard LLM response
            assistant_reply = react_with_llm(conversation_histories[session_id])

        # Apply self-correction if reasoning was used
        if use_reasoning:
            assistant_reply = self_correction_check(assistant_reply, user_message)

        # Save assistant's reply
        conversation_histories[session_id].append({"role": "assistant", "content": assistant_reply})
        persist()

        # Build response
        response_data = {
            "reply": assistant_reply,
            "reasoning_steps": [step.dict() for step in reasoning_steps] if reasoning_steps else [],
            "used_reasoning": use_reasoning,
            "session_id": session_id
        }

        json_response = JSONResponse(content=response_data)
        if is_new_session:
            json_response.set_cookie(key="session_id", value=session_id, httponly=True)
        
        return json_response

    except Exception as e:
        logging.error(f"[CHAT] Error processing message: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.post("/chat/clear")
async def clear_history(session_id: Optional[str] = Cookie(default=None)):
    """Clear conversation history for the current session."""
    if session_id and session_id in conversation_histories:
        conversation_histories[session_id] = []
        persist()
        return {"message": "Conversation history cleared.", "session_id": session_id}
    return {"message": "No session found to clear."}

@router.get("/chat/history")
async def get_chat_history(session_id: Optional[str] = Cookie(default=None)):
    """Get conversation history for the current session."""
    if not session_id:
        raise HTTPException(status_code=400, detail="No session found")
    
    history = conversation_histories.get(session_id, [])
    return {"history": history, "session_id": session_id}

@router.post("/chat/feedback")
async def provide_feedback(
    feedback: dict = Body(...),
    session_id: Optional[str] = Cookie(default=None)
):
    """
    Accept user feedback on responses for future improvement.
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="No session found")
    
    # In a real implementation, you'd store this feedback for model improvement
    logging.info(f"[FEEDBACK] Session {session_id}: {feedback}")
    
    return {"message": "Thank you for your feedback!", "session_id": session_id}

