// Fix 3: Enhanced MessageBubble with working Discuss/Copy for search results
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

const COLORS = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#34495e', '#e67e22'];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-gray-800 p-3 rounded-lg border border-white/20 shadow-lg">
        <p className="text-white font-medium">{label}</p>
        <p className="text-blue-400">
          Count: <span className="font-bold">{payload[0].value}</span>
        </p>
      </div>
    );
  }
  return null;
};

const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, label }) => {
  if (percent < 0.05) return null;
  
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text 
      x={x} 
      y={y} 
      fill="white" 
      textAnchor={x > cx ? 'start' : 'end'} 
      dominantBaseline="central"
      fontSize="12"
      fontWeight="bold"
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

function MessageBubble({ role, message, data, onDiscuss, onCopy }) {
  const isUser = role === 'user';
  
  // Check if message contains search results
  const isSearchResult = message.includes('🧠 Summary:') && message.includes('🔗 Sources:');
  
  // Check if message contains a Markdown-style link
  const isMarkdownLink = /\[.*?\]\(.*?\)/.test(message);
  const linkText = message.match(/\[([^\]]+)\]/)?.[1];
  const linkHref = message.match(/\((.*?)\)/)?.[1];

  // Copy message content to clipboard
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message);
      // You could add a toast notification here
      console.log('Message copied to clipboard');
    } catch (err) {
      console.error('Failed to copy message:', err);
    }
  };

  // Start a discussion based on the message content
  const handleDiscuss = () => {
    if (onDiscuss) {
      // Extract key points for discussion
      let discussionTopic = '';
      if (isSearchResult) {
        const summaryMatch = message.match(/🧠 Summary:\n(.*?)\n\n🔗 Sources:/s);
        discussionTopic = summaryMatch ? summaryMatch[1] : message.slice(0, 200);
      } else {
        discussionTopic = message.slice(0, 200);
      }
      onDiscuss(discussionTopic);
    }
  };

  // Enhanced visualization rendering
  const renderVisualization = (chartData) => {
    if (!chartData || !Array.isArray(chartData) || chartData.length === 0) {
      return (
        <div className="w-full p-4 bg-gray-800/30 rounded-lg border border-white/10">
          <h3 className="text-lg font-bold mb-2 text-white">📊 Research Insights</h3>
          <p className="text-gray-400">No data available for visualization</p>
        </div>
      );
    }

    const sortedData = [...chartData].sort((a, b) => (b.count || 0) - (a.count || 0));
    
    const processedData = sortedData.map(item => ({
      ...item,
      label: item.label && item.label.length > 12 
        ? item.label.substring(0, 12) + '...' 
        : item.label,
      originalLabel: item.label
    }));

    const shouldUsePieChart = chartData.length <= 5 && chartData.every(item => item.count > 0);
    const maxCount = Math.max(...chartData.map(item => item.count || 0));

    return (
      <div className="w-full max-w-3xl">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            📊 Research Insights
            <span className="text-sm font-normal text-gray-400">
              ({chartData.length} topics)
            </span>
          </h3>
          
          {/* Action buttons for visualizations */}
          <div className="flex gap-2">
            <button
              onClick={handleCopy}
              className="text-xs bg-gray-700 hover:bg-gray-600 text-white px-2 py-1 rounded transition"
              title="Copy visualization data"
            >
              📋 Copy
            </button>
            <button
              onClick={handleDiscuss}
              className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded transition"
              title="Discuss these insights"
            >
              💬 Discuss
            </button>
          </div>
        </div>
        
        <div className="bg-gray-800/30 rounded-lg border border-white/10 p-4">
          {shouldUsePieChart ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={processedData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={renderCustomLabel}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="count"
                    >
                      {processedData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              
              <div className="space-y-2">
                <h4 className="text-sm font-semibold text-white mb-2">Details</h4>
                {processedData.map((item, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-700/30 rounded">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: COLORS[index % COLORS.length] }}
                      ></div>
                      <span className="text-white text-xs" title={item.originalLabel}>
                        {item.originalLabel}
                      </span>
                    </div>
                    <span className="text-blue-400 font-bold text-sm">{item.count}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart
                  data={processedData}
                  margin={{ top: 20, right: 5, left: 5, bottom: 90 }}
                >
                  <XAxis 
                    dataKey="label" 
                    angle={-45}
                    textAnchor="end"
                    height={90}
                    interval={0}
                    tick={{ fontSize: 11, fill: '#cbd5e1', wordBreak: 'break-word' }}
                  />
                  <YAxis 
                    tick={{ fontSize: 12, fill: '#cbd5e1' }}
                    domain={[0, Math.ceil(maxCount * 1.1)]}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar 
                    dataKey="count" 
                    radius={[3, 3, 0, 0]}
                  >
                    {processedData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              
              <div className="mt-3 flex justify-center space-x-4 text-xs">
                <div className="text-center">
                  <div className="text-blue-400 font-bold">{chartData.length}</div>
                  <div className="text-gray-400">Topics</div>
                </div>
                <div className="text-center">
                  <div className="text-green-400 font-bold">{Math.max(...chartData.map(i => i.count))}</div>
                  <div className="text-gray-400">Max</div>
                </div>
                <div className="text-center">
                  <div className="text-yellow-400 font-bold">
                    {Math.round(chartData.reduce((sum, i) => sum + i.count, 0) / chartData.length)}
                  </div>
                  <div className="text-gray-400">Avg</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`p-3 rounded-lg text-sm whitespace-pre-wrap max-w-[95%] border relative group ${
          isUser
            ? 'bg-blue-600 text-white self-end border-blue-800'
            : 'bg-gray-700 text-white self-start border-white/10'
        }`}
      >
        {/* Message content */}
        {message === '[VISUALIZE]' && data ? (
          renderVisualization(data)
        ) : isMarkdownLink ? (
          <a
            href={linkHref}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 underline hover:text-blue-300"
          >
            {linkText}
          </a>
        ) : (
          message
        )}

        {/* Action buttons for search results and regular messages */}
        {!isUser && message !== '[VISUALIZE]' && (
          <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
            <button
              onClick={handleCopy}
              className="text-xs bg-gray-600 hover:bg-gray-500 text-white px-2 py-1 rounded transition"
              title="Copy message"
            >
              📋
            </button>
            <button
              onClick={handleDiscuss}
              className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded transition"
              title="Discuss this"
            >
              💬
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default MessageBubble;