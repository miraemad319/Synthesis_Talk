# Import the LLM interface to call for summaries
from backend.llm import react_with_llm
import nltk
from nltk.tokenize import sent_tokenize
from typing import List, Dict, Any, Optional
import json
import re

def _ensure_nltk_data():
    """Ensure NLTK punkt tokenizer is available"""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        try:
            nltk.download("punkt", quiet=True)
            nltk.download("punkt_tab", quiet=True)  # For newer NLTK versions
        except Exception as e:
            print(f"Warning: Could not download NLTK data: {e}")
            # Fallback to simple sentence splitting
            return False
    return True

def _simple_sentence_split(text):
    """Fallback sentence splitting when NLTK is not available"""
    import re
    # Simple regex-based sentence splitting
    sentences = re.split(r'[.!?]+\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def extract_key_concepts(text: str) -> List[str]:
    """Extract key concepts from text using simple heuristics"""
    # Remove common words and extract potential key terms
    import re
    from collections import Counter
    
    # Clean and tokenize
    words = re.findall(r'\b[A-Za-z]{3,}\b', text.lower())
    
    # Common stop words to exclude
    stop_words = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our',
        'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way',
        'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use', 'that', 'with', 'have',
        'this', 'will', 'your', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time',
        'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take',
        'than', 'them', 'well', 'were', 'what', 'where', 'which', 'while', 'would', 'there', 'could',
        'other', 'after', 'first', 'never', 'these', 'think', 'where', 'being', 'every', 'great',
        'might', 'shall', 'still', 'those', 'under', 'while'
    }
    
    # Filter out stop words and count frequency
    filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
    word_counts = Counter(filtered_words)
    
    # Return top concepts
    return [word for word, count in word_counts.most_common(10)]

def summarize_text(text: str, format: str = "paragraph", reasoning_technique: str = "chain_of_thought") -> Dict[str, Any]:
    """
    Generates a summary of the provided document text using advanced reasoning techniques.

    Parameters:
    - text (str): The full document content as a string.
    - format (str): "paragraph", "bullets", "structured", or "executive"
    - reasoning_technique (str): "chain_of_thought" or "react"

    Returns:
    - Dict[str, Any]: Summary with metadata including reasoning process
    """
    if not text.strip():
        return {
            "summary": "No content to summarize.",
            "reasoning_technique": reasoning_technique,
            "key_concepts": [],
            "confidence": 0.0
        }

    # Ensure NLTK data is available
    if not _ensure_nltk_data():
        print("Warning: Using fallback sentence splitting")

    # Trim large documents but keep more context for better summaries
    snippet = text[:5000] if len(text) > 5000 else text
    
    # Extract key concepts for context
    key_concepts = extract_key_concepts(snippet)
    
    if reasoning_technique == "react":
        return _summarize_with_react(snippet, format, key_concepts)
    else:
        return _summarize_with_chain_of_thought(snippet, format, key_concepts)

def _summarize_with_chain_of_thought(text: str, format: str, key_concepts: List[str]) -> Dict[str, Any]:
    """Summarize using Chain of Thought reasoning"""
    
    # Construct the Chain of Thought prompt
    cot_prompt = f"""I need to summarize this document step by step using chain of thought reasoning.

Let me think through this systematically:

1. First, let me identify the main topic and purpose of this document.
2. Then, I'll identify the key points and supporting details.
3. Next, I'll organize these points logically.
4. Finally, I'll create a {format} summary that captures the essence.

Document to summarize:
{text}

Key concepts I've identified: {', '.join(key_concepts)}

Let me work through this step by step:

Step 1 - Main Topic Analysis:
[Analyze what this document is primarily about]

Step 2 - Key Points Identification:
[List the main arguments, findings, or information]

Step 3 - Logical Organization:
[Organize the points in a coherent structure]

Step 4 - Summary Creation:
[Create the final summary in {format} format]

Please provide your chain of thought reasoning followed by the final summary."""

    messages = [{"role": "user", "content": cot_prompt}]

    try:
        response = react_with_llm(messages)
        
        # Extract the final summary from the chain of thought response
        summary = _extract_final_summary(response, format)
        
        return {
            "summary": summary,
            "reasoning_technique": "chain_of_thought",
            "reasoning_process": response,
            "key_concepts": key_concepts,
            "confidence": _calculate_confidence(response),
            "format": format
        }
    except Exception as e:
        print(f"[LLM Error] {e}")
        return {
            "summary": "Summary generation failed.",
            "reasoning_technique": "chain_of_thought",
            "error": str(e),
            "key_concepts": key_concepts,
            "confidence": 0.0
        }

def _summarize_with_react(text: str, format: str, key_concepts: List[str]) -> Dict[str, Any]:
    """Summarize using ReAct (Reasoning + Acting) approach"""
    
    react_prompt = f"""I'll use the ReAct approach (Reasoning + Acting) to summarize this document.

Available Actions:
1. ANALYZE: Examine specific aspects of the document
2. EXTRACT: Pull out key information
3. ORGANIZE: Structure the information logically
4. SYNTHESIZE: Create the final summary

Document to summarize:
{text}

Key concepts identified: {', '.join(key_concepts)}

Let me proceed with ReAct reasoning:

Thought 1: I need to understand what this document is about and its main purpose.
Action 1: ANALYZE the document's main theme and structure
Observation 1: [Analysis of main theme]

Thought 2: Now I should identify the most important points and information.
Action 2: EXTRACT key points, arguments, and findings
Observation 2: [Key points extracted]

Thought 3: I need to organize these points in a logical way for the summary.
Action 3: ORGANIZE the information into a coherent structure
Observation 3: [Organized structure]

Thought 4: Now I can create the final {format} summary.
Action 4: SYNTHESIZE all information into a {format} format summary
Observation 4: [Final summary]

Please follow this ReAct pattern and provide your reasoning and final summary in {format} format."""

    messages = [{"role": "user", "content": react_prompt}]

    try:
        response = react_with_llm(messages)
        
        # Extract the final summary from the ReAct response
        summary = _extract_final_summary(response, format)
        
        return {
            "summary": summary,
            "reasoning_technique": "react",
            "reasoning_process": response,
            "key_concepts": key_concepts,
            "confidence": _calculate_confidence(response),
            "format": format,
            "actions_taken": _extract_actions_from_react(response)
        }
    except Exception as e:
        print(f"[LLM Error] {e}")
        return {
            "summary": "Summary generation failed.",
            "reasoning_technique": "react",
            "error": str(e),
            "key_concepts": key_concepts,
            "confidence": 0.0
        }

def _extract_final_summary(response: str, format: str) -> str:
    """Extract the final summary from LLM response"""
    # Look for common summary indicators
    summary_indicators = [
        "final summary:",
        "summary:",
        "in conclusion:",
        "to summarize:",
        "observation 4:",
        "step 4"
    ]
    
    response_lower = response.lower()
    
    for indicator in summary_indicators:
        if indicator in response_lower:
            # Find the position and extract text after it
            pos = response_lower.find(indicator)
            if pos != -1:
                summary_start = pos + len(indicator)
                summary_text = response[summary_start:].strip()
                
                # If there's more text after, try to find natural ending
                paragraphs = summary_text.split('\n\n')
                if len(paragraphs) > 1 and format != "bullets":
                    return paragraphs[0].strip()
                elif format == "bullets" and summary_text:
                    # For bullet format, try to extract bullet points
                    lines = summary_text.split('\n')
                    bullets = [line.strip() for line in lines if line.strip().startswith(('•', '-', '*', '1.', '2.', '3.'))]
                    if bullets:
                        return '\n'.join(bullets)
                
                return summary_text.strip()
    
    # Fallback: return last paragraph if no indicators found
    paragraphs = response.split('\n\n')
    return paragraphs[-1].strip() if paragraphs else response.strip()

def _extract_actions_from_react(response: str) -> List[str]:
    """Extract actions taken during ReAct reasoning"""
    actions = []
    lines = response.split('\n')
    
    for line in lines:
        if line.strip().lower().startswith('action'):
            actions.append(line.strip())
    
    return actions

def _calculate_confidence(response: str) -> float:
    """Calculate confidence score based on response quality indicators"""
    confidence = 0.5  # Base confidence
    
    # Increase confidence for structured responses
    if any(indicator in response.lower() for indicator in ['step', 'first', 'second', 'finally', 'conclusion']):
        confidence += 0.2
    
    # Increase confidence for detailed responses
    if len(response) > 200:
        confidence += 0.1
    
    # Increase confidence if multiple reasoning steps are present
    if response.lower().count('thought') > 1 or response.lower().count('step') > 2:
        confidence += 0.1
    
    # Decrease confidence for very short responses
    if len(response) < 100:
        confidence -= 0.2
    
    return max(0.0, min(1.0, confidence))

def multi_document_summary(documents: List[Dict[str, str]], format: str = "paragraph", 
                          reasoning_technique: str = "chain_of_thought") -> Dict[str, Any]:
    """
    Create a comprehensive summary across multiple documents
    
    Parameters:
    - documents: List of {"filename": str, "content": str} dictionaries
    - format: Summary format
    - reasoning_technique: Reasoning approach to use
    
    Returns:
    - Dict with comprehensive summary and cross-document insights
    """
    if not documents:
        return {
            "summary": "No documents to summarize.",
            "reasoning_technique": reasoning_technique,
            "documents_processed": 0
        }
    
    # Combine all key concepts
    all_concepts = []
    document_summaries = []
    
    # First, summarize each document individually
    for doc in documents:
        doc_summary = summarize_text(doc["content"], "paragraph", reasoning_technique)
        document_summaries.append({
            "filename": doc["filename"],
            "summary": doc_summary["summary"],
            "key_concepts": doc_summary.get("key_concepts", [])
        })
        all_concepts.extend(doc_summary.get("key_concepts", []))
    
    # Find common concepts across documents
    from collections import Counter
    concept_counts = Counter(all_concepts)
    common_concepts = [concept for concept, count in concept_counts.most_common(10) if count > 1]
    
    # Create synthesis prompt
    synthesis_prompt = f"""I need to create a comprehensive summary that synthesizes information from {len(documents)} documents using {reasoning_technique} reasoning.

Individual document summaries:
"""
    
    for i, doc_sum in enumerate(document_summaries, 1):
        synthesis_prompt += f"\nDocument {i} ({doc_sum['filename']}):\n{doc_sum['summary']}\n"
    
    synthesis_prompt += f"""
Common concepts across documents: {', '.join(common_concepts)}

Please create a {format} synthesis that:
1. Identifies overarching themes
2. Notes complementary information
3. Highlights any contradictions
4. Provides integrated insights

Use {reasoning_technique} reasoning to work through this systematically."""

    messages = [{"role": "user", "content": synthesis_prompt}]
    
    try:
        response = react_with_llm(messages)
        synthesis_summary = _extract_final_summary(response, format)
        
        return {
            "summary": synthesis_summary,
            "reasoning_technique": reasoning_technique,
            "reasoning_process": response,
            "documents_processed": len(documents),
            "individual_summaries": document_summaries,
            "common_concepts": common_concepts,
            "confidence": _calculate_confidence(response),
            "format": format
        }
    except Exception as e:
        print(f"[LLM Error] {e}")
        return {
            "summary": "Multi-document synthesis failed.",
            "reasoning_technique": reasoning_technique,
            "error": str(e),
            "documents_processed": len(documents),
            "individual_summaries": document_summaries
        }


