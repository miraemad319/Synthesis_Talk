# backend/routes/insights.py

from fastapi import APIRouter, Cookie, HTTPException, Query
from fastapi.responses import JSONResponse
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from backend.utils.session_store import document_store, conversation_histories, persist
from backend.llm import react_with_llm

router = APIRouter()

class InsightAnalyzer:
    """Advanced insight generation with reasoning techniques"""
    
    @staticmethod
    def extract_key_themes(text: str) -> List[str]:
        """Extract key themes using Chain of Thought reasoning"""
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
            response = react_with_llm([{"role": "user", "content": prompt}])
            # Try to extract JSON from response
            if '[' in response and ']' in response:
                start = response.find('[')
                end = response.rfind(']') + 1
                json_str = response[start:end]
                return json.loads(json_str)
            return []
        except Exception as e:
            print(f"Theme extraction failed: {e}")
            return []
    
    @staticmethod
    def generate_research_questions(text: str, themes: List[str]) -> List[str]:
        """Generate research questions using ReAct reasoning"""
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
            response = react_with_llm([{"role": "user", "content": prompt}])
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                data = json.loads(json_str)
                return data.get("questions", [])
            return []
        except Exception as e:
            print(f"Research question generation failed: {e}")
            return []
    
    @staticmethod
    def identify_connections(text: str) -> Dict[str, Any]:
        """Identify connections between concepts"""
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
            response = react_with_llm([{"role": "user", "content": prompt}])
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                return json.loads(json_str)
            return {"causal": [], "correlations": [], "contradictions": [], "supporting": []}
        except Exception as e:
            print(f"Connection analysis failed: {e}")
            return {"causal": [], "correlations": [], "contradictions": [], "supporting": []}

@router.get("/insights/")
async def generate_insights(
    session_id: str = Cookie(default=None),
    insight_type: str = Query(default="comprehensive", description="Type of insights: comprehensive, themes, questions, connections")
):
    """Generate various types of insights from uploaded documents"""
    print(f"[DEBUG /insights/] session_id: {session_id}, type: {insight_type}")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")

    docs = document_store.get(session_id, [])
    if not docs:
        raise HTTPException(status_code=404, detail="No documents found for session")

    all_text = "\n".join(chunk for chunk, _ in docs)
    if not all_text.strip():
        raise HTTPException(status_code=400, detail="No content available for generating insights")

    analyzer = InsightAnalyzer()
    
    try:
        if insight_type == "themes":
            themes = analyzer.extract_key_themes(all_text)
            result = {
                "type": "themes",
                "themes": themes,
                "generated_at": datetime.now().isoformat()
            }
            
        elif insight_type == "questions":
            themes = analyzer.extract_key_themes(all_text)
            questions = analyzer.generate_research_questions(all_text, themes)
            result = {
                "type": "research_questions",
                "questions": questions,
                "related_themes": themes,
                "generated_at": datetime.now().isoformat()
            }
            
        elif insight_type == "connections":
            connections = analyzer.identify_connections(all_text)
            result = {
                "type": "connections",
                "connections": connections,
                "generated_at": datetime.now().isoformat()
            }
            
        else:  # comprehensive
            # Generate comprehensive insights with Chain of Thought
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
            
            llm_response = react_with_llm([{"role": "user", "content": prompt}])
            
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
            
            result = {
                "type": "comprehensive",
                "insights": parsed,
                "generated_at": datetime.now().isoformat(),
                "document_count": len([doc for doc in docs if doc[0].strip()]),
                "total_length": len(all_text)
            }
        
        # Store insights in conversation history
        if session_id not in conversation_histories:
            conversation_histories[session_id] = []
        
        conversation_histories[session_id].append({
            "role": "assistant",
            "content": f"Generated {insight_type} insights",
            "metadata": {
                "type": "insight_generation",
                "insight_type": insight_type,
                "timestamp": datetime.now().isoformat()
            }
        })
        
        persist()
        return JSONResponse(content=result)
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse insights from LLM response")
    except Exception as e:
        print(f"Insight generation error: {e}")
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
                "content_preview": msg["content"][:100]
            })
    
    return JSONResponse(content={
        "insights_count": len(insights),
        "insights": insights,
        "session_id": session_id
    })

