// Fix 1: Document Insights Panel with working Generate button
import { useEffect, useState } from 'react';
import axios from 'axios';

function ContextPanel({ messages, activeTool, uploadedDocs, userId }) {
  const [topic, setTopic] = useState('New Conversation');
  const [sources, setSources] = useState([]);
  const [isGeneratingTopic, setIsGeneratingTopic] = useState(false);
  const [insights, setInsights] = useState([]);
  const [isGeneratingInsights, setIsGeneratingInsights] = useState(false);

  // Generate insights from uploaded documents
  const generateInsights = async () => {
    if (uploadedDocs.length === 0) {
      alert('No documents uploaded to generate insights from.');
      return;
    }

    setIsGeneratingInsights(true);

    try {
      // Get the last few assistant messages that contain document content
      const documentMessages = messages
        .filter(m => m.role === 'assistant' && 
          (m.message.includes('📄 Uploaded') || m.message.includes('Summary:')))
        .slice(-3); // Get last 3 document-related messages

      if (documentMessages.length === 0) {
        alert('No document content found in conversation history.');
        setIsGeneratingInsights(false);
        return;
      }

      // Combine document content for analysis
      const combinedContent = documentMessages
        .map(msg => msg.message)
        .join('\n\n');

      // Use the visualize tool to generate insights
      const response = await axios.post('http://localhost:8000/tools/use', {
        tool_name: 'visualize',
        input_text: combinedContent,
        user_id: userId
      });

      if (Array.isArray(response.data.result)) {
        setInsights(response.data.result);
      } else {
        console.error('Unexpected response format:', response.data);
        alert('Failed to generate insights. Please try again.');
      }
    } catch (error) {
      console.error('Error generating insights:', error);
      alert('Error generating insights. Please check the console for details.');
    } finally {
      setIsGeneratingInsights(false);
    }
  };

  // Generate intelligent topic title
  const generateTopicTitle = async (conversationHistory) => {
    if (conversationHistory.length < 2) return 'New Conversation';
    
    setIsGeneratingTopic(true);
    
    try {
      const relevantMessages = conversationHistory.slice(0, 6);
      const conversationText = relevantMessages
        .map(msg => `${msg.role}: ${msg.message}`)
        .join('\n');

      const response = await axios.post('http://localhost:8000/tools/generate_topic', {
        conversation_text: conversationText
      });

      let generatedTitle = response.data.topic;
      
      generatedTitle = generatedTitle
        .replace(/^["']|["']$/g, '')
        .replace(/^Title:\s*/i, '')
        .replace(/^\d+\.\s*/, '')
        .trim();

      if (!generatedTitle || generatedTitle.length > 50) {
        generatedTitle = extractSimpleTopic(conversationHistory);
      }

      setTopic(generatedTitle);
    } catch (error) {
      console.error('Topic generation failed:', error);
      setTopic(extractSimpleTopic(conversationHistory));
    } finally {
      setIsGeneratingTopic(false);
    }
  };

  const extractSimpleTopic = (conversationHistory) => {
    const firstUserMessage = conversationHistory.find(m => m.role === 'user')?.message || '';
    
    const words = firstUserMessage.toLowerCase().split(' ');
    const stopWords = ['what', 'how', 'why', 'when', 'where', 'is', 'are', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'about', 'can', 'could', 'would', 'should', 'tell', 'me', 'you', 'i', 'we', 'they'];
    
    const keyWords = words
      .filter(word => word.length > 3 && !stopWords.includes(word))
      .slice(0, 3);
    
    if (keyWords.length > 0) {
      return keyWords.map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    }
    
    return 'Research Discussion';
  };

  useEffect(() => {
    if (messages.length >= 2 && messages.length % 4 === 0) {
      generateTopicTitle(messages);
    } else if (messages.length === 2) {
      generateTopicTitle(messages);
    }

    // Extract sources from assistant messages
    const searchResults = messages
      .filter(m => m.role === 'assistant' && m.message.includes("http"))
      .flatMap(m =>
        [...m.message.matchAll(/https?:\/\/[^\s)]+/g)].map(match => match[0])
      );

    setSources([...new Set(searchResults)].slice(0, 5));
  }, [messages]);

  return (
    <div className="text-white text-sm space-y-3 h-full overflow-y-auto">
      <div>
        <p className="text-white/60 mb-1">Current Topic:</p>
        <div className="bg-white/10 p-2 rounded-md relative">
          {isGeneratingTopic && (
            <div className="absolute right-2 top-2">
              <div className="animate-spin h-3 w-3 border border-white/30 border-t-white rounded-full"></div>
            </div>
          )}
          <span className={isGeneratingTopic ? 'opacity-50' : ''}>
            {topic}
          </span>
        </div>
      </div>

      <div>
        <p className="text-white/60 mb-1">Last Used Tool:</p>
        <div className="bg-white/10 p-2 rounded-md">
          {activeTool || '---'}
        </div>
      </div>

      <div>
        <p className="text-white/60 mb-1">Message Count:</p>
        <div className="bg-white/10 p-2 rounded-md">
          {messages.length} messages
        </div>
      </div>

      {/* FIX: Document Insights Section */}
      <div>
        <div className="flex justify-between items-center mb-1">
          <p className="text-white/60">Document Insights:</p>
          <button
            onClick={generateInsights}
            disabled={isGeneratingInsights || uploadedDocs.length === 0}
            className={`text-xs px-2 py-1 rounded transition ${
              uploadedDocs.length === 0 
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            {isGeneratingInsights ? 'Generating...' : 'Generate'}
          </button>
        </div>
        
        {uploadedDocs.length > 0 ? (
          <div className="space-y-1">
            {uploadedDocs.map((doc, i) => (
              <div key={i} className="bg-white/10 p-2 rounded-md text-xs">
                📄 {doc}
              </div>
            ))}
            
            {/* Display generated insights */}
            {insights.length > 0 && (
              <div className="mt-2 space-y-1">
                <p className="text-white/60 text-xs">Key Topics:</p>
                {insights.slice(0, 3).map((insight, i) => (
                  <div key={i} className="bg-blue-900/30 p-2 rounded text-xs">
                    <span className="font-medium">{insight.label}</span>
                    <span className="text-blue-400 ml-2">({insight.count})</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="bg-white/10 p-2 rounded-md">No documents uploaded</div>
        )}
      </div>

      <div>
        <p className="text-white/60 mb-1">Sources Found:</p>
        {sources.length > 0 ? (
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {sources.map((url, i) => (
              <a
                key={i}
                href={url}
                target="_blank"
                rel="noreferrer"
                className="block text-blue-400 hover:text-blue-300 underline text-xs truncate p-1 bg-white/5 rounded"
                title={url}
              >
                {url.replace(/https?:\/\/(www\.)?/, '').split('/')[0]}
              </a>
            ))}
          </div>
        ) : (
          <div className="bg-white/10 p-2 rounded-md">No sources found</div>
        )}
      </div>
    </div>
  );
}

export default ContextPanel;