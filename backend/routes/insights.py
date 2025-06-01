# backend/routes/insights.py

from fastapi import APIRouter, Cookie, HTTPException, Query, BackgroundTasks
from fastpi.responses import JSONResponse
import json
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import time
import uuid

from backend.utils.session_store import document_store, conversation_histories, persist
from backend.llm import react_with_llm

router = APIRouter()

# In-memory storage for background insight generation tasks
insight_tasks = {}

class InsightAnalyzer:
    """Advanced insight generation with reasoning techniques and timeout handling"""
    
    @staticmethod
    async def extract_key_themes_with_timeout(text: str, timeout: int = 60) -> List[str]:
        """Extract key themes using Chain of Thought reasoning with timeout"""
        prompt = (
            "I need to identify key themes in this text using step-by-step reasoning.\n\n"
            "Step 1: Read through the text and identify main topics\n"
            "Step 2: Look for recurring concepts and patterns\n"
            "Step 3: Group related ideas together\n"
            "Step 4: Extract 5-7 key themes\n\n"
            f"Text to analyze:\n{text[:2000]}\n\n"
            "Please think through each step and return only a JSON array of key themes:\n"
            '["theme1", "theme2", "theme3", ...]'
        )
        
        try:
            # Create a task with timeout
            response_task = asyncio.create_task(
                asyncio.to_thread(react_with_llm, [{"role": "user", "content": prompt}])
            )
            response = await asyncio.wait_for(response_task, timeout=timeout)
            
            # Try to extract JSON from response
            if '[' in response and ']' in response:
                start = response.find('[')
                end = response.rfind(']') + 1
                json_str = response[start:end]
                return json.loads(json_str)
            return []
        except asyncio.TimeoutError:
            print(f"Theme extraction timed out after {timeout}s")
            return ["Analysis timed out - using fallback themes"]
        except Exception as e:
            print(f"Theme extraction failed: {e}")
            return []
    
    @staticmethod
    async def generate_research_questions_with_timeout(text: str, themes: List[str], timeout: int = 60) -> List[str]:
        """Generate research questions using ReAct reasoning with timeout"""
        prompt = (
            "I need to generate research questions using ReAct reasoning.\n\n"
            "Thought: I should analyze the content and themes to identify knowledge gaps and interesting research directions.\n"
            "Action: Analyze the following content and themes to generate focused research questions.\n"
            f"Content summary: {text[:1500]}\n"
            f"Key themes: {', '.join(themes)}\n\n"
            "Observation: Based on the content and themes, I can identify several research directions.\n"
            "Thought: I should formulate 3-5 specific, actionable research questions.\n"
            "Action: Generate research questions in JSON format.\n\n"
            'Return only: {"questions": ["question1", "question2", ...]}'
        )
        
        try:
            response_task = asyncio.create_task(
                asyncio.to_thread(react_with_llm, [{"role": "user", "content": prompt}])
            )
            response = await asyncio.wait_for(response_task, timeout=timeout)
            
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                data = json.loads(json_str)
                return data.get("questions", [])
            return []
        except asyncio.TimeoutError:
            print(f"Research question generation timed out after {timeout}s")
            return ["What are the key implications of the main findings?", "What areas need further investigation?"]
        except Exception as e:
            print(f"Research question generation failed: {e}")
            return []
    
    @staticmethod
    async def identify_connections_with_timeout(text: str, timeout: int = 60) -> Dict[str, Any]:
        """Identify connections between concepts with timeout"""
        prompt = (
            "Analyze this text to identify connections between different concepts, ideas, or topics.\n"
            "Look for:\n"
            "1. Causal relationships (A causes B)\n"
            "2. Correlations (A relates to B)\n"
            "3. Contradictions (A conflicts with B)\n"
            "4. Supporting evidence (A supports B)\n\n"
            f"Text: {text[:2000]}\n\n"
            "Return JSON format:\n"
            '{\n'
            '  "causal": [{"from": "concept1", "to": "concept2", "relationship": "description"}],\n'
            '  "correlations": [{"concept1": "A", "concept2": "B", "strength": "strong/medium/weak"}],\n'
            '  "contradictions": [{"concept1": "A", "concept2": "B", "description": "why they conflict"}],\n'
            '  "supporting": [{"evidence": "A", "supports": "B", "description": "how it supports"}]\n'
            '}'
        )
        
        try:
            response_task = asyncio.create_task(
                asyncio.to_thread(react_with_llm, [{"role": "user", "content": prompt}])
            )
            response = await asyncio.wait_for(response_task, timeout=timeout)
            
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                return json.loads(json_str)
            return {"causal": [], "correlations": [], "contradictions": [], "supporting": []}
        except asyncio.TimeoutError:
            print(f"Connection analysis timed out after {timeout}s")
            return {
                "causal": [{"from": "timeout", "to": "analysis", "relationship": "Analysis timed out"}],
                "correlations": [],
                "contradictions": [],
                "supporting": []
            }
        except Exception as e:
            print(f"Connection analysis failed: {e}")
            return {"causal": [], "correlations": [], "contradictions": [], "supporting": []}

async def generate_insights_background(session_id: str, insight_type: str, all_text: str, task_id: str):
    """Background task for generating insights"""
    try:
        print(f"[BACKGROUND] Starting insight generation: {task_id}")
        insight_tasks[task_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Starting analysis...",
            "started_at": datetime.now().isoformat()
        }
        
        analyzer = InsightAnalyzer()
        
        if insight_type == "themes":
            insight_tasks[task_id].update({"progress": 50, "message": "Extracting themes..."})
            themes = await analyzer.extract_key_themes_with_timeout(all_text, timeout=90)
            result = {
                "type": "themes",
                "themes": themes,
                "generated_at": datetime.now().isoformat()
            }
            
        elif insight_type == "questions":
            insight_tasks[task_id].update({"progress": 25, "message": "Extracting themes..."})
            themes = await analyzer.extract_key_themes_with_timeout(all_text, timeout=60)
            
            insight_tasks[task_id].update({"progress": 75, "message": "Generating research questions..."})
            questions = await analyzer.generate_research_questions_with_timeout(all_text, themes, timeout=60)
            
            result = {
                "type": "research_questions",
                "questions": questions,
                "related_themes": themes,
                "generated_at": datetime.now().isoformat()
            }
            
        elif insight_type == "connections":
            insight_tasks[task_id].update({"progress": 50, "message": "Analyzing connections..."})
            connections = await analyzer.identify_connections_with_timeout(all_text, timeout=90)
            result = {
                "type": "connections",
                "connections": connections,
                "generated_at": datetime.now().isoformat()
            }
            
        else:  # comprehensive
            insight_tasks[task_id].update({"progress": 30, "message": "Performing comprehensive analysis..."})
            
            # Generate comprehensive insights with timeout
            prompt = (
                "I need to provide comprehensive insights about this research content using systematic analysis.\n\n"
                "Step 1: Identify the main topic and scope\n"
                "Step 2: Extract key findings and important points\n"
                "Step 3: Analyze patterns and relationships\n"
                "Step 4: Generate actionable insights\n"
                "Step 5: Suggest areas for further research\n\n"
                f"Document content (first 3000 chars):\n{all_text[:3000]}\n\n"
                "Please analyze step by step and return insights in this JSON format:\n"
                '{\n'
                '  "summary": "concise overview paragraph",\n'
                '  "key_findings": ["finding1", "finding2", "finding3"],\n'
                '  "patterns": ["pattern1", "pattern2"],\n'
                '  "implications": ["implication1", "implication2"],\n'
                '  "research_gaps": ["gap1", "gap2"],\n'
                '  "confidence_score": 0.8\n'
                '}'
            )
            
            try:
                llm_task = asyncio.create_task(
                    asyncio.to_thread(react_with_llm, [{"role": "user", "content": prompt}])
                )
                llm_response = await asyncio.wait_for(llm_task, timeout=90)
                
                # Extract JSON from response
                if '{' in llm_response and '}' in llm_response:
                    start = llm_response.find('{')
                    end = llm_response.rfind('}') + 1
                    json_str = llm_response[start:end]
                    parsed = json.loads(json_str)
                else:
                    # Fallback structure if JSON parsing fails
                    parsed = {
                        "summary": "Analysis completed but formatting issues occurred",
                        "key_findings": ["Content analysis performed"],
                        "patterns": [],
                        "implications": [],
                        "research_gaps": [],
                        "confidence_score": 0.5
                    }
            except asyncio.TimeoutError:
                parsed = {
                    "summary": "Analysis timed out after 90 seconds. Please try with smaller content or contact support.",
                    "key_findings": ["Analysis was interrupted due to timeout"],
                    "patterns": [],
                    "implications": ["Consider breaking content into smaller segments"],
                    "research_gaps": ["Analysis incomplete due to timeout"],
                    "confidence_score": 0.3
                }
            
            docs = document_store.get(session_id, [])
            result = {
                "type": "comprehensive",
                "insights": parsed,
                "generated_at": datetime.now().isoformat(),
                "document_count": len([doc for doc in docs if doc[0].strip()]),
                "total_length": len(all_text)
            }
        
        # Store results
        insight_tasks[task_id].update({
            "status": "completed",
            "progress": 100,
            "message": "Analysis completed successfully",
            "result": result,
            "completed_at": datetime.now().isoformat()
        })
        
        # Store in conversation history
        if session_id not in conversation_histories:
            conversation_histories[session_id] = []
        
        conversation_histories[session_id].append({
            "role": "assistant",
            "content": f"Generated {insight_type} insights",
            "metadata": {
                "type": "insight_generation",
                "insight_type": insight_type,
                "timestamp": datetime.now().isoformat(),
                "task_id": task_id
            }
        })
        
        persist()
        print(f"[BACKGROUND] Completed insight generation: {task_id}")
        
    except Exception as e:
        print(f"[BACKGROUND] Error in insight generation {task_id}: {e}")
        insight_tasks[task_id] = {
            "status": "failed",
            "progress": 0,
            "message": f"Analysis failed: {str(e)}",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        }

@router.post("/insights/")
async def generate_insights(
    background_tasks: BackgroundTasks,
    session_id: str = Cookie(default=None),
    insight_type: str = Query(default="comprehensive", description="Type of insights: comprehensive, themes, questions, connections")
):
    """Generate various types of insights from uploaded documents using background processing"""
    print(f"[DEBUG /insights/] session_id: {session_id}, type: {insight_type}")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")

    docs = document_store.get(session_id, [])
    if not docs:
        raise HTTPException(status_code=404, detail="No documents found for session")

    all_text = "\n".join(chunk for chunk, _ in docs)
    if not all_text.strip():
        raise HTTPException(status_code=400, detail="No content available for generating insights")

    # Create a unique task ID
    task_id = str(uuid.uuid4())
    
    # Start background task
    background_tasks.add_task(
        generate_insights_background, 
        session_id, 
        insight_type, 
        all_text, 
        task_id
    )
    
    # Return task ID for tracking
    return JSONResponse(content={
        "task_id": task_id,
        "status": "started",
        "message": f"Insight generation started for type: {insight_type}",
        "estimated_time": "1-2 minutes",
        "check_status_url": f"/api/v1/insights/status/{task_id}"
    })

@router.get("/insights/status/{task_id}")
async def get_insight_status(task_id: str):
    """Check the status of an insight generation task"""
    if task_id not in insight_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = insight_tasks[task_id]
    
    # Clean up completed/failed tasks after 1 hour
    if task_info.get("status") in ["completed", "failed"]:
        completed_time = task_info.get("completed_at") or task_info.get("failed_at")
        if completed_time:
            try:
                completed_dt = datetime.fromisoformat(completed_time)
                if (datetime.now() - completed_dt).seconds > 3600:  # 1 hour
                    del insight_tasks[task_id]
                    raise HTTPException(status_code=410, detail="Task results expired")
            except:
                pass
    
    return JSONResponse(content=task_info)

@router.get("/insights/")
async def get_insights_direct(
    session_id: str = Cookie(default=None),
    insight_type: str = Query(default="comprehensive", description="Type of insights: comprehensive, themes, questions, connections"),
    quick: bool = Query(default=False, description="Generate quick insights with shorter timeouts")
):
    """Generate insights directly (synchronous) - use for quick insights only"""
    print(f"[DEBUG /insights/ direct] session_id: {session_id}, type: {insight_type}, quick: {quick}")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")

    docs = document_store.get(session_id, [])
    if not docs:
        raise HTTPException(status_code=404, detail="No documents found for session")

    all_text = "\n".join(chunk for chunk, _ in docs)
    if not all_text.strip():
        raise HTTPException(status_code=400, detail="No content available for generating insights")

    analyzer = InsightAnalyzer()
    timeout = 30 if quick else 60  # Shorter timeout for quick mode
    
    try:
        if insight_type == "themes":
            themes = await analyzer.extract_key_themes_with_timeout(all_text, timeout=timeout)
            result = {
                "type": "themes",
                "themes": themes,
                "generated_at": datetime.now().isoformat()
            }
        else:
            # For non-theme requests, redirect to background processing
            return JSONResponse(
                status_code=202,
                content={
                    "message": "This insight type requires background processing. Use POST /insights/ instead.",
                    "suggestion": "Use POST /insights/ for comprehensive analysis"
                }
            )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        print(f"Direct insight generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Insight generation failed: {str(e)}")

@router.get("/insights/summary")
async def get_session_insights_summary(session_id: str = Cookie(default=None)):
    """Get a summary of all insights generated for this session"""
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")
    
    if session_id not in conversation_histories:
        return JSONResponse(content={"insights_count": 0, "insights": []})
    
    # Filter conversation history for insight-related entries
    insights = []
    for msg in conversation_histories[session_id]:
        if (msg.get("metadata", {}).get("type") == "insight_generation"):
            insights.append({
                "type": msg["metadata"]["insight_type"],
                "timestamp": msg["metadata"]["timestamp"],
                "content_preview": msg["content"][:100],
                "task_id": msg["metadata"].get("task_id")
            })
    
    return JSONResponse(content={
        "insights_count": len(insights),
        "insights": insights,
        "session_id": session_id
    })

@router.delete("/insights/tasks")
async def cleanup_old_tasks():
    """Clean up old completed/failed tasks"""
    cleaned = 0
    current_time = datetime.now()
    
    for task_id in list(insight_tasks.keys()):
        task_info = insight_tasks[task_id]
        if task_info.get("status") in ["completed", "failed"]:
            completed_time = task_info.get("completed_at") or task_info.get("failed_at")
            if completed_time:
                try:
                    completed_dt = datetime.fromisoformat(completed_time)
                    if (current_time - completed_dt).seconds > 3600:  # 1 hour
                        del insight_tasks[task_id]
                        cleaned += 1
                except:
                    pass
    
    return JSONResponse(content={"cleaned_tasks": cleaned})