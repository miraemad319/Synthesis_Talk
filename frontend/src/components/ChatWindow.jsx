import { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import axios from 'axios';
import { FiPlus, FiDownload, FiMessageCircle } from 'react-icons/fi';

function ChatWindow({ userId, messages, setMessages, activeTool, setActiveTool, uploadedDocs, setUploadedDocs }) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [exporting, setExporting] = useState(false);
  
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle discuss functionality for MessageBubble
  const handleDiscuss = (content) => {
    const discussPrompt = `Let's discuss this further: ${content.slice(0, 200)}${content.length > 200 ? '...' : ''}`;
    setInput(discussPrompt);
  };

  // Handle copy functionality
  const handleCopy = () => {
    console.log('Content copied to clipboard');
    // You could add a toast notification here
  };

  const sendMessage = async () => {
    if (!input.trim() && activeTool !== "visualize") return;

    const newMessages = [...messages];
    const userMessage = input.trim() || "[Using Visualize Tool]";
    newMessages.push({ role: "user", message: userMessage });
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      let reply, result;

      if (!activeTool) {
        const res = await axios.post("http://localhost:8000/chat/message", {
          user_id: userId,
          message: userMessage,
        });
        
        console.log("Chat response:", res.data);
        reply = res.data.reply || res.data.message || "No response";
        
      } else {
        let toolInput = input;

        if (activeTool === "visualize" && !input.trim()) {
          const lastAssistant = [...messages].reverse().find(m => m.role === "assistant");
          if (lastAssistant) {
            toolInput = lastAssistant.message;
          }
        }

        const res = await axios.post("http://localhost:8000/tools/use", {
          tool_name: activeTool,
          input_text: toolInput,
          user_id: userId,
        });

        console.log("Tool response:", res.data);

        if (activeTool === "visualize" && Array.isArray(res.data.result)) {
          reply = "[VISUALIZE]";
          result = res.data.result;
        } else if (activeTool === "search" && typeof res.data.result === "string") {
          reply = res.data.result;
        } else if (activeTool === "search" && Array.isArray(res.data.result)) {
          reply = res.data.result
            .map(
              (item) =>
                `🔗 ${item.title}\n${item.href}\n${item.body?.slice(0, 150)}...`
            )
            .join("\n\n");
        } else {
          if (typeof res.data.result === "string") {
            reply = res.data.result;
          } else if (typeof res.data.result === "object" && res.data.result !== null) {
            reply = JSON.stringify(res.data.result, null, 2);
          } else {
            reply = "Tool completed successfully";
          }
        }
      }

      // Ensure reply is always a string
      if (typeof reply !== "string") {
        console.error("Reply is not a string:", reply);
        reply = JSON.stringify(reply);
      }

      setMessages([...newMessages, { role: "assistant", message: reply, data: result }]);
    } catch (err) {
      console.error("Error:", err);
      setMessages([
        ...newMessages,
        { role: "assistant", message: "❌ Error connecting to backend." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("user_id", userId);

    setUploading(true);

    try {
      const res = await axios.post("http://localhost:8000/tools/upload", formData);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          message: `📄 Uploaded **${res.data.filename}**\n\n📝 Summary:\n${res.data.summary}`
        }
      ]);
      setUploadedDocs((prev) => [...prev, file.name]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", message: "❌ Failed to upload and summarize PDF." }
      ]);
    } finally {
      setUploading(false);
    }
  };

  const handleExport = async () => {
    if (messages.length === 0) {
      alert('No conversation to export!');
      return;
    }

    setExporting(true);

    try {
      // Combine all messages for export
      const conversationText = messages
        .map(msg => `${msg.role.toUpperCase()}: ${msg.message}`)
        .join('\n\n');

      const res = await axios.post("http://localhost:8000/tools/use", {
        tool_name: "export_pdf",
        input_text: conversationText,
        user_id: userId
      });

      if (res.data.result && res.data.result.file_path) {
        let filePath = res.data.result.file_path.replace(/\\/g, "/");
        const fileName = filePath.split("/").pop();

        // Create download link
        const downloadUrl = `http://localhost:8000/${filePath}`;
        
        // Add export confirmation message
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            message: `📄 **Export Complete!**\n\n[📥 Download ${fileName}](${downloadUrl})\n\nYour conversation has been exported to PDF.`
          }
        ]);

        // Auto-download
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    } catch (err) {
      console.error('Export error:', err);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", message: "❌ Failed to export conversation. Please try again." }
      ]);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="flex flex-col h-full max-h-[90vh]">
      {/* Scrollable chat container */}
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-3 scroll-smooth scrollable-chat"
      >
        {uploading && (
          <div className="text-sm text-blue-400 animate-pulse px-2">
            ⏳ Uploading and analyzing document...
          </div>
        )}
        
        {messages.length === 0 && (
          <div className="text-center text-white/60 py-8">
            <h3 className="text-lg mb-2">Welcome to SynthesisTalk!</h3>
            <p>Start a conversation or use one of the research tools below.</p>
          </div>
        )}
        
        {messages.map((msg, i) => (
          <MessageBubble 
            key={i} 
            role={msg.role} 
            message={msg.message} 
            data={msg.data}
            onDiscuss={handleDiscuss}
            onCopy={handleCopy}
          />
        ))}
        
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-700 text-white p-3 rounded-lg animate-pulse">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-white rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input area with improved layout */}
      <div className="shrink-0 border-t border-white/10 bg-white/5 px-4 py-3 backdrop-blur-lg">
        {/* Main input row */}
        <div className="flex gap-2 items-center mb-2">
          {/* Upload PDF */}
          <label className="cursor-pointer flex-shrink-0" title="Upload PDF">
            <input
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={handleUpload}
              disabled={uploading}
            />
            <FiPlus className={`text-white text-xl transition ${
              uploading ? 'text-gray-500 cursor-not-allowed' : 'hover:text-blue-500'
            }`} />
          </label>

          {/* Tool Dropdown */}
          <select
            className="bg-gray-800 text-white border border-white/20 px-3 py-2 rounded-lg text-sm flex-shrink-0"
            value={activeTool}
            onChange={(e) => setActiveTool(e.target.value)}
          >
            <option value="">💬 Chat</option>
            <option value="summarize">📝 Summarize</option>
            <option value="clarify">💡 Clarify</option>
            <option value="search">🔍 Search</option>
            <option value="visualize">📊 Visualize</option>
            <option value="react_agent">🤖 ReAct Agent</option>
            <option value="qa">❓ Q&A</option>
          </select>

          {/* Input Field */}
          <input
            className="flex-1 bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white placeholder-white/60 focus:outline-none focus:ring focus:ring-blue-500"
            placeholder={activeTool ? `Use ${activeTool} on...` : 'Chat with SynthesisTalk...'}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
          />

          {/* Send Button */}
          <button
            onClick={sendMessage}
            className="bg-blue-600 hover:bg-blue-700 transition text-white px-4 py-2 rounded-lg font-semibold flex-shrink-0"
            disabled={loading}
          >
            {loading ? '⏳' : '📤'}
          </button>
        </div>

        {/* Secondary action row */}
        <div className="flex gap-2 justify-end">
          {/* Export Button - Now properly visible */}
          <button
            onClick={handleExport}
            disabled={exporting || messages.length === 0}
            className={`flex items-center gap-2 px-3 py-1 rounded-md text-sm transition ${
              messages.length === 0 
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-zinc-800 border border-zinc-600 text-white hover:bg-zinc-700 hover:border-zinc-500'
            }`}
            title="Export conversation to PDF"
          >
            <FiDownload className="text-sm" />
            {exporting ? 'Exporting...' : 'Export PDF'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatWindow;