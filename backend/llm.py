import os
import time
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from openai import OpenAI, OpenAIError
from fastapi import HTTPException
from dotenv import load_dotenv
import re
from enum import Enum

# Load environment variables from .env file
load_dotenv()

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ReasoningType(Enum):
    STANDARD = "standard"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    REACT = "react"
    SYNTHESIS = "synthesis"

# Configuration for both services
SERVICES = {
    "NGU": {
        "api_key": os.getenv('NGU_API_KEY'),
        "base_url": os.getenv('NGU_BASE_URL'),
        "model": os.getenv('NGU_MODEL', 'gpt-3.5-turbo')
    },
    "GROQ": {
        "api_key": os.getenv('GROQ_API_KEY'),
        "base_url": os.getenv('GROQ_BASE_URL'),
        "model": os.getenv('GROQ_MODEL', 'llama2-70b-4096')
    }
}

# Primary service preference
PRIMARY_SERVICE = os.getenv('MODEL_SERVER', 'NGU').upper()
FALLBACK_SERVICE = 'GROQ' if PRIMARY_SERVICE == 'NGU' else 'NGU'

# Enhanced system prompt with ReAct reasoning capabilities
SYSTEM_PROMPT = """
You are SynthesisTalk, a highly capable research assistant that uses advanced reasoning methodologies including ReAct (Reasoning + Acting) and Chain of Thought.

CORE CAPABILITIES:
1. **ReAct Reasoning**: For complex queries, use this pattern:
   - Thought: Analyze what information you need
   - Action: Determine what tool or approach to use  
   - Observation: Process the results
   - Repeat until you can provide a complete answer

2. **Chain of Thought**: Break down complex problems step-by-step:
   - Identify key components
   - Analyze relationships
   - Draw logical conclusions
   - Synthesize final answer

3. **Synthesis Engine**: 
   - Connect ideas across multiple sources
   - Identify patterns and relationships
   - Generate insights from accumulated knowledge
   - Provide multi-format outputs

4. **Self-Correction**: Review and improve responses for accuracy and completeness

TOOL INTEGRATION:
- Document Analysis: Extract and analyze content from uploaded files
- Web Search: Find current information to supplement knowledge
- Note Management: Organize and structure research findings
- Visualization: Create data representations and concept maps
- Context Linking: Connect related concepts across sources

RESPONSE GUIDELINES:
- Always cite sources when using document content
- Use clear, organized formatting with proper structure
- For complex research questions, show your reasoning process
- Adapt response format to user needs (paragraph, bullets, structured)
- If information is missing, suggest specific additional sources

QUALITY STANDARDS:
- Accuracy: Verify information against multiple sources
- Completeness: Address all aspects of the query
- Clarity: Use accessible language while maintaining precision
- Relevance: Focus on information that directly addresses the question

Remember: You are helping users conduct serious research. Be thorough, accurate, and insightful while showing your reasoning process.
"""

class AdvancedLLMProcessor:
    """Enhanced LLM processor with advanced reasoning capabilities."""
    
    def __init__(self):
        self.reasoning_patterns = {
            ReasoningType.REACT: self._apply_react_reasoning,
            ReasoningType.CHAIN_OF_THOUGHT: self._apply_chain_of_thought,
            ReasoningType.SYNTHESIS: self._apply_synthesis_reasoning,
            ReasoningType.STANDARD: self._apply_standard_reasoning
        }
        
    def determine_reasoning_type(self, query: str, context: str = "") -> ReasoningType:
        """Intelligently determine the best reasoning approach for a query."""
        query_lower = query.lower()
        
        # ReAct indicators: complex multi-step analysis
        react_indicators = [
            "analyze", "compare", "evaluate", "synthesize", "relationship",
            "how does", "why might", "what are the implications", "explore the connection"
        ]
        
        # Synthesis indicators: connecting multiple sources
        synthesis_indicators = [
            "connect", "integrate", "combine", "relate", "pattern", "trend",
            "across sources", "between documents", "common themes"
        ]
        
        # Chain of thought indicators: step-by-step reasoning
        cot_indicators = [
            "explain how", "walk through", "step by step", "process of",
            "sequence", "methodology", "procedure"
        ]
        
        # Check for multiple sources in context
        has_multiple_sources = context and len(re.findall(r'\[From [^\]]+\]', context)) > 1
        
        # Complex query indicators
        is_complex = (
            len(query.split()) > 15 or
            any(indicator in query_lower for indicator in react_indicators) or
            has_multiple_sources
        )
        
        # Determine reasoning type
        if any(indicator in query_lower for indicator in synthesis_indicators) or has_multiple_sources:
            return ReasoningType.SYNTHESIS
        elif is_complex and any(indicator in query_lower for indicator in react_indicators):
            return ReasoningType.REACT  
        elif any(indicator in query_lower for indicator in cot_indicators):
            return ReasoningType.CHAIN_OF_THOUGHT
        else:
            return ReasoningType.STANDARD
    
    def _apply_react_reasoning(self, query: str, context: str, client: OpenAI, model: str) -> str:
        """Apply ReAct reasoning methodology."""
        react_prompt = f"""
Use ReAct (Reasoning + Acting) methodology to answer this research question systematically.

Format your response as follows:
Thought: [What do I need to understand about this question?]
Action: [What approach will I take to gather/analyze information?]
Observation: [What do I learn from the available information?]
Thought: [What additional analysis is needed?]
Action: [Next step in my analysis]
Observation: [Additional insights gained]
... (continue as needed)
Final Answer: [Comprehensive response based on reasoning process]

Research Question: {query}

Available Information:
{context[:3000] if context else "No additional context provided"}

Begin your ReAct analysis:
"""
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": react_prompt}
        ]
        
        return self._make_llm_call(client, model, messages, temperature=0.3, max_tokens=1500)
    
    def _apply_chain_of_thought(self, query: str, context: str, client: OpenAI, model: str) -> str:
        """Apply Chain of Thought reasoning."""
        cot_prompt = f"""
Let me work through this systematically using chain of thought reasoning:

Question: {query}

Step 1: Identify the key components
[What are the main elements I need to address?]

Step 2: Analyze available information  
[What relevant information do I have?]
{context[:2000] if context else "No additional context"}

Step 3: Connect the dots
[How do these pieces of information relate to each other?]

Step 4: Consider implications
[What can I conclude from this analysis?]

Step 5: Formulate comprehensive answer
[Based on my step-by-step analysis, what is the complete answer?]

Let me think through this carefully:
"""
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": cot_prompt}
        ]
        
        return self._make_llm_call(client, model, messages, temperature=0.2, max_tokens=1200)
    
    def _apply_synthesis_reasoning(self, query: str, context: str, client: OpenAI, model: str) -> str:
        """Apply synthesis reasoning for connecting multiple sources."""
        synthesis_prompt = f"""
Perform advanced synthesis to connect information across multiple sources:

Research Question: {query}

Available Sources and Information:
{context[:4000] if context else "No source material provided"}

Synthesis Framework:
1. **Source Analysis**: What unique insights does each source provide?
2. **Pattern Recognition**: What common themes or patterns emerge?
3. **Gap Identification**: What information is missing or contradictory?
4. **Connection Mapping**: How do concepts from different sources relate?
5. **Insight Generation**: What new understanding emerges from synthesis?
6. **Comprehensive Response**: Integrated answer drawing from all sources

Proceed with systematic synthesis:
"""
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": synthesis_prompt}
        ]
        
        return self._make_llm_call(client, model, messages, temperature=0.4, max_tokens=1800)
    
    def _apply_standard_reasoning(self, query: str, context: str, client: OpenAI, model: str) -> str:
        """Apply standard reasoning for straightforward queries."""
        # Use the existing conversation format for simpler queries
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{query}\n\nContext: {context[:2000] if context else 'No additional context'}"}
        ]
        
        return self._make_llm_call(client, model, messages, temperature=0.2, max_tokens=1000)
    
    def _make_llm_call(self, client: OpenAI, model: str, messages: List[Dict], **kwargs) -> str:
        """Make an LLM API call with error handling and logging."""
        token_estimate = sum(len(m["content"]) for m in messages) // 4
        logger.info(f"Making LLM call with {len(messages)} messages (~{token_estimate} tokens)")
        
        try:
            start_time = time.time()
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            latency = time.time() - start_time
            
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            logger.info(f"LLM response received (reason={finish_reason}) in {latency:.2f}s")
            
            return content
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise

def get_client(service_name: str) -> OpenAI:
    """Create an OpenAI client for the specified service."""
    service_config = SERVICES[service_name]
    if not service_config["api_key"]:
        raise ValueError(f"API key not configured for {service_name}")
    
    return OpenAI(
        api_key=service_config["api_key"],
        base_url=service_config["base_url"]
    )

def test_service_health(service_name: str) -> bool:
    """Test if a service is available."""
    try:
        client = get_client(service_name)
        response = client.chat.completions.create(
            model=SERVICES[service_name]["model"],
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1,
            temperature=0
        )
        return True
    except Exception as e:
        logger.warning(f"Service {service_name} health check failed: {e}")
        return False

def trim_history(history: List[Dict], max_chars: int = 25000) -> List[Dict]:
    """Trim conversation history to stay under character limit."""
    if not history:
        return history
        
    # Always keep system message if present
    system_messages = [m for m in history if m["role"] == "system"]
    other_messages = [m for m in history if m["role"] != "system"]
    
    total_chars = sum(len(m["content"]) for m in history)
    
    while total_chars > max_chars and len(other_messages) > 1:
        removed = other_messages.pop(0)  # Remove oldest non-system message
        total_chars -= len(removed["content"])
    
    return system_messages + other_messages

def apply_self_correction(response: str, original_query: str, client: OpenAI, model: str) -> str:
    """Apply self-correction to improve response quality."""
    correction_prompt = f"""
Please review and improve the following response to ensure it meets high research standards:

Original Question: {original_query}

Current Response: {response}

Evaluation Criteria:
1. **Accuracy**: Are all facts and claims correct?
2. **Completeness**: Does it fully address the question?
3. **Clarity**: Is it well-organized and easy to understand?
4. **Sources**: Are sources properly referenced?
5. **Reasoning**: Is the logic sound and well-explained?

If the response is excellent as-is, return it unchanged. If improvements are needed, provide an enhanced version that addresses any deficiencies.

Improved Response:
"""
    
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": correction_prompt}
        ]
        
        improved = AdvancedLLMProcessor()._make_llm_call(
            client, model, messages, 
            temperature=0.1, max_tokens=1000
        )
        
        # If the response is significantly longer and different, use it
        if len(improved) > len(response) * 0.8 and improved != response:
            logger.info("Applied self-correction to improve response")
            return improved
        else:
            return response
            
    except Exception as e:
        logger.error(f"Self-correction failed: {e}")
        return response

def react_with_llm(conversation_history: List[Dict], use_advanced_reasoning: bool = True) -> str:
    """
    Enhanced LLM interface with advanced reasoning capabilities.
    
    Args:
        conversation_history: List of conversation messages
        use_advanced_reasoning: Whether to apply advanced reasoning techniques
        
    Returns:
        LLM response string
    """
    if not conversation_history:
        raise ValueError("Conversation history cannot be empty")
    
    # Extract latest user message and context
    latest_message = ""
    context_info = ""
    
    for msg in reversed(conversation_history):
        if msg["role"] == "user" and not latest_message:
            latest_message = msg["content"]
        elif msg["role"] == "system" and ("Relevant documents:" in msg["content"] or "Search results" in msg["content"]):
            context_info += msg["content"] + "\n"
    
    # Initialize advanced processor
    processor = AdvancedLLMProcessor()
    
    # Determine reasoning approach
    if use_advanced_reasoning and latest_message:
        reasoning_type = processor.determine_reasoning_type(latest_message, context_info)
        logger.info(f"Using reasoning type: {reasoning_type.value}")
    else:
        reasoning_type = ReasoningType.STANDARD
    
    # Prepare messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history
    messages = trim_history(messages)
    
    # Try services in order
    services_to_try = [PRIMARY_SERVICE, FALLBACK_SERVICE]
    last_error = None
    
    for service_name in services_to_try:
        try:
            logger.info(f"Attempting to use {service_name} service...")
            
            # Validate service configuration
            service_config = SERVICES[service_name]
            if not all([service_config["api_key"], service_config["base_url"], service_config["model"]]):
                logger.warning(f"{service_name} service not properly configured")
                continue
            
            client = get_client(service_name)
            model = service_config["model"]
            
            # Apply appropriate reasoning method
            if reasoning_type != ReasoningType.STANDARD:
                response = processor.reasoning_patterns[reasoning_type](
                    latest_message, context_info, client, model
                )
            else:
                response = processor._make_llm_call(
                    client, model, messages,
                    temperature=0.2, max_tokens=1024, top_p=0.9
                )
            
            # Apply self-correction for important queries
            if use_advanced_reasoning and len(latest_message.split()) > 5:
                response = apply_self_correction(response, latest_message, client, model)
            
            logger.info(f"Successfully generated response using {service_name}")
            return response
            
        except Exception as e:
            last_error = e
            logger.error(f"{service_name} service failed: {e}")
            continue
    
    # If all services failed
    error_msg = f"All LLM services failed. Last error: {last_error}"
    logger.error(error_msg)
    raise HTTPException(status_code=500, detail=error_msg)

def get_available_service() -> Optional[str]:
    """Return the name of the first available service."""
    for service_name in [PRIMARY_SERVICE, FALLBACK_SERVICE]:
        if test_service_health(service_name):
            return service_name
    return None

# Enhanced tool management for research operations
class ResearchToolManager:
    """Manages research tools and their integration with reasoning systems."""
    
    def __init__(self):
        self.tools = {
            "document_analyzer": {
                "name": "Document Analyzer",
                "description": "Extract key information and insights from uploaded documents",
                "capabilities": ["extraction", "summarization", "key_point_identification"]
            },
            "web_searcher": {
                "name": "Web Search Engine", 
                "description": "Search for current information to supplement research",
                "capabilities": ["fact_finding", "verification", "current_events"]
            },
            "concept_linker": {
                "name": "Concept Linker",
                "description": "Connect related concepts across different sources",
                "capabilities": ["relationship_mapping", "pattern_recognition", "synthesis"]
            },
            "insight_generator": {
                "name": "Insight Generator",
                "description": "Generate research insights from accumulated information",
                "capabilities": ["trend_analysis", "gap_identification", "hypothesis_formation"]
            },
            "format_converter": {
                "name": "Format Converter",
                "description": "Convert research findings into different output formats",
                "capabilities": ["summary_generation", "visualization", "export"]
            }
        }
    
    def get_available_tools(self) -> Dict[str, Dict]:
        """Return all available research tools."""
        return self.tools
    
    def get_tool_recommendations(self, query: str, context: str = "") -> List[str]:
        """Recommend appropriate tools based on query analysis."""
        query_lower = query.lower()
        recommendations = []
        
        # Document analysis recommendations
        if any(word in query_lower for word in ["analyze", "extract", "summarize", "document"]):
            recommendations.append("document_analyzer")
        
        # Web search recommendations  
        if any(word in query_lower for word in ["search", "find", "current", "recent", "latest"]):
            recommendations.append("web_searcher")
        
        # Concept linking recommendations
        if any(word in query_lower for word in ["connect", "relate", "compare", "pattern", "relationship"]):
            recommendations.append("concept_linker")
        
        # Insight generation recommendations
        if any(word in query_lower for word in ["insight", "trend", "implication", "significance"]):
            recommendations.append("insight_generator")
        
        # Format conversion recommendations
        if any(word in query_lower for word in ["format", "export", "visualize", "chart", "summary"]):
            recommendations.append("format_converter")
        
        return recommendations

# Global instances
tool_manager = ResearchToolManager()
llm_processor = AdvancedLLMProcessor()