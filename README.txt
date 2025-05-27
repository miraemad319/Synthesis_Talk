CSAI 422: Advanced Topics in Generative AI Group Project:
SynthesisTalk - Collaborative Research Assistant Overview
In this group project, you will apply the concepts learned throughout this course to build a sophisticated LLM-powered application that demonstrates conversational agency, tool usage, and advanced reasoning techniques. Working in teams of three, you will create “SynthesisTalk,” an intelligent research assistant that helps users explore complex topics through an interactive, conversational interface. SynthesisTalk combines document analysis, web search capabilities, and customizable outputs to support deep research on complex topics. The system will demonstrate how LLM-based conversational agents can effectively utilize tools, maintain context, apply reasoning techniques, and generate useful outputs in various formats.
Project Requirements:
Core Features:
1.	Contextual Research Conversation:
a.	Implement multi-turn conversations that maintain context about the research topic
b.	Support document uploads (PDFs, text files) with content extraction and analysis
c.	Integrate web search to supplement user knowledge and document content
d.	Maintain coherent conversation across multiple information sources
2.	Intelligent Synthesis Engine
a.	Extract key information from documents and web searches
b.	Connect related concepts across different sources
c.	Generate insights based on patterns in collected information
d.	Implement at least one advanced reasoning technique (Chain of Thought or ReAct)
3.	Flexible Output Generation:
a.	Generate structured summaries in at least two different formats
b.	Create simple visualizations based on research findings
c.	Support exporting findings in a standard document format
4.	Tool-Enhanced Experience:
a.	Implement at least four different tool types:
i.	Document analysis tools (extraction, summarization)
ii.	Web search tools for fact-finding and verification
iii.	Note-taking and organization tools
iv.	Explanation and clarification tools
Technical Requirements:
1.	Frontend:
-	Build a React-based web application with responsive design
-	Implement a chat interface supporting text and document uploads
-	Create components for displaying research insights and visualizations
-	Design a context management UI showing current research topics and sources
-	Provide real-time feedback for lengthy operations
2.	Backend:
-	Develop a FastAPI or Flask backend serving LLM integration
-	Implement a tool management system for handling different LLM tool calls
-	Create a document processing pipeline for extracting and indexing content
-	Design a conversation history management system
-	Implement at least one advanced reasoning technique (Chain of Thought, ReAct)
3.	LLM Integration:
-	Integrate with an NGU LLM API
-	Define and implement tools for various research functions
-	Create a workflow that effectively orchestrates multiple tools
-	Implement some form of self-correction mechanism

Important Notes:
-	You may use any LLM provider, but your application should be designed to be easily adapted to different providers
-	You should implement proper error handling and fallback mechanisms
-	Consider usability and accessibility in your design
-	Document any limitations or potential improvements for your system

Limitations:
- Limited to first 3000 characters for summarization/insights
- No authentication or user account separation
- No rate limiting or pagination for long sessions

Future Improvements:
- Add /define/ or /compare/ tools
- Enable document download/export in .pdf or .md
- Add long-term memory (e.g., using SQLite or Redis)