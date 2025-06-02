import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Legend,
  ScatterChart,
  Scatter,
  Area,
  AreaChart
} from 'recharts';
import { 
  BarChart3, 
  LineChart as LineChartIcon, 
  PieChart as PieChartIcon, 
  Activity,
  TrendingUp,
  Download,
  RefreshCw,
  Settings,
  ChevronDown
} from 'lucide-react';
import { synthesisAPI } from '../utils/api';

const CHART_TYPES = {
  bar: { name: 'Bar Chart', icon: BarChart3, component: 'BarChart' },
  line: { name: 'Line Chart', icon: LineChartIcon, component: 'LineChart' },
  pie: { name: 'Pie Chart', icon: PieChartIcon, component: 'PieChart' },
  area: { name: 'Area Chart', icon: Activity, component: 'AreaChart' },
  scatter: { name: 'Scatter Plot', icon: TrendingUp, component: 'ScatterChart' }
};

const COLORS = ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#F97316', '#84CC16'];

export default function VisualizationPanel() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasAttemptedLoad, setHasAttemptedLoad] = useState(false);
  const [chartType, setChartType] = useState('bar');
  const [showSettings, setShowSettings] = useState(false);
  const [chartTitle, setChartTitle] = useState('Data Visualization');
  const [dataKey, setDataKey] = useState('value');
  const [nameKey, setNameKey] = useState('name');
  const [availableVisualizations, setAvailableVisualizations] = useState([]);

  // Auto-detect data keys when data changes
  useEffect(() => {
    if (data.length > 0) {
      const firstItem = data[0];
      const keys = Object.keys(firstItem);
      
      // Try to find appropriate keys
      const possibleNameKeys = keys.filter(key => 
        typeof firstItem[key] === 'string' || key.toLowerCase().includes('name') || key.toLowerCase().includes('label')
      );
      const possibleValueKeys = keys.filter(key => 
        typeof firstItem[key] === 'number' || key.toLowerCase().includes('value') || key.toLowerCase().includes('count')
      );

      if (possibleNameKeys.length > 0) setNameKey(possibleNameKeys[0]);
      if (possibleValueKeys.length > 0) setDataKey(possibleValueKeys[0]);
    }
  }, [data]);

  const fetchVisualization = async (type = 'keywords') => {
    setLoading(true);
    setError("");
    setHasAttemptedLoad(true);
    
    try {
      let response;
      
      // Try different visualization endpoints based on type
      switch (type) {
        case 'keywords':
          response = await synthesisAPI.visualization.getKeywords(10);
          setChartTitle('Top Keywords');
          break;
        case 'sources':
          response = await synthesisAPI.visualization.getSources();
          setChartTitle('Document Sources');
          break;
        case 'conversation':
          response = await synthesisAPI.visualization.getConversationFlow();
          setChartTitle('Conversation Flow');
          break;
        case 'topics':
          response = await synthesisAPI.visualization.getTopicAnalysis();
          setChartTitle('Topic Analysis');
          break;
        case 'timeline':
          response = await synthesisAPI.visualization.getResearchTimeline();
          setChartTitle('Research Timeline');
          break;
        default:
          // Try the main visualization endpoint
          response = await synthesisAPI.visualization.getAvailable();
          if (response.data.available_visualizations?.length > 0) {
            setAvailableVisualizations(response.data.available_visualizations);
            // Try to fetch the first available visualization
            const firstViz = response.data.available_visualizations[0];
            const vizType = firstViz.endpoint.split('/').pop();
            return fetchVisualization(vizType);
          } else {
            // Fallback to keywords if no specific visualizations available
            return fetchVisualization('keywords');
          }
      }
      
      const responseData = response.data.data || response.data || [];
      setData(responseData);
      
      // Set chart title if provided
      if (response.data.title) {
        setChartTitle(response.data.title);
      }
      
      // Auto-select best chart type based on data
      if (responseData.length > 0) {
        const firstItem = responseData[0];
        const numericKeys = Object.keys(firstItem).filter(key => typeof firstItem[key] === 'number');
        
        if (numericKeys.length > 1) {
          setChartType('scatter');
        } else if (responseData.length > 10) {
          setChartType('line');
        } else if (responseData.length <= 5) {
          setChartType('pie');
        }
      }
    } catch (err) {
      console.error('Visualization fetch error:', err);
      setError(err.response?.data?.detail || err.userMessage || "Failed to load visualization.");
      
      // Provide fallback demo data for development
      if (err.code === 'ECONNREFUSED' || err.response?.status === 404) {
        const demoData = [
          { name: 'Research', value: 45 },
          { name: 'Analysis', value: 32 },
          { name: 'Documents', value: 28 },
          { name: 'Insights', value: 21 },
          { name: 'Synthesis', value: 15 }
        ];
        setData(demoData);
        setChartTitle('Demo Visualization');
      } else {
        setData([]);
      }
    }
    setLoading(false);
  };

  const exportChart = async () => {
    try {
      // This would typically generate an image or PDF of the chart
      const chartData = {
        type: chartType,
        data: data,
        title: chartTitle,
        settings: { dataKey, nameKey }
      };
      
      const blob = new Blob([JSON.stringify(chartData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chart-${chartTitle.toLowerCase().replace(/\s+/g, '-')}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export error:', err);
    }
  };

  const renderChart = () => {
    if (!data.length) return null;

    const commonProps = {
      width: "100%",
      height: 350,
      data: data,
      margin: { top: 20, right: 30, left: 20, bottom: 60 }
    };

    switch (chartType) {
      case 'bar':
        return (
          <ResponsiveContainer {...commonProps}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis 
                dataKey={nameKey}
                fontSize={12}
                angle={-45}
                textAnchor="end"
                height={80}
                stroke="#6B7280"
              />
              <YAxis fontSize={12} stroke="#6B7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#F9FAFB', 
                  border: '1px solid #E5E7EB',
                  borderRadius: '8px'
                }}
              />
              <Bar 
                dataKey={dataKey} 
                fill="#4F46E5" 
                radius={[4, 4, 0, 0]}
                fillOpacity={0.8}
              />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line':
        return (
          <ResponsiveContainer {...commonProps}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis 
                dataKey={nameKey}
                fontSize={12}
                stroke="#6B7280"
              />
              <YAxis fontSize={12} stroke="#6B7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#F9FAFB', 
                  border: '1px solid #E5E7EB',
                  borderRadius: '8px'
                }}
              />
              <Line 
                type="monotone" 
                dataKey={dataKey} 
                stroke="#4F46E5" 
                strokeWidth={3}
                dot={{ fill: '#4F46E5', strokeWidth: 2, r: 6 }}
                activeDot={{ r: 8, stroke: '#4F46E5', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'pie':
        return (
          <ResponsiveContainer {...commonProps}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={120}
                fill="#8884d8"
                dataKey={dataKey}
                nameKey={nameKey}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#F9FAFB', 
                  border: '1px solid #E5E7EB',
                  borderRadius: '8px'
                }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );

      case 'area':
        return (
          <ResponsiveContainer {...commonProps}>
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis 
                dataKey={nameKey}
                fontSize={12}
                stroke="#6B7280"
              />
              <YAxis fontSize={12} stroke="#6B7280" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#F9FAFB', 
                  border: '1px solid #E5E7EB',
                  borderRadius: '8px'
                }}
              />
              <Area 
                type="monotone" 
                dataKey={dataKey} 
                stroke="#4F46E5" 
                fill="#4F46E5"
                fillOpacity={0.3}
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'scatter':
        // For scatter plot, try to use first two numeric keys
        const numericKeys = Object.keys(data[0]).filter(key => typeof data[0][key] === 'number');
        const xKey = numericKeys[0] || dataKey;
        const yKey = numericKeys[1] || dataKey;
        
        return (
          <ResponsiveContainer {...commonProps}>
            <ScatterChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis 
                type="number" 
                dataKey={xKey}
                fontSize={12}
                stroke="#6B7280"
                name={xKey}
              />
              <YAxis 
                type="number" 
                dataKey={yKey}
                fontSize={12}
                stroke="#6B7280"
                name={yKey}
              />
              <Tooltip 
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{ 
                  backgroundColor: '#F9FAFB', 
                  border: '1px solid #E5E7EB',
                  borderRadius: '8px'
                }}
              />
              <Scatter 
                name="Data Points" 
                dataKey={yKey} 
                fill="#4F46E5"
              />
            </ScatterChart>
          </ResponsiveContainer>
        );

      default:
        return null;
    }
  };

  return (
    <div className="p-6 flex-1 overflow-auto bg-gradient-to-br from-slate-50 to-blue-50 min-h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-1">Data Visualization</h2>
          <p className="text-sm text-gray-600">Interactive charts and insights from your research</p>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-white rounded-lg transition-colors"
            title="Chart Settings"
          >
            <Settings className="w-5 h-5" />
          </button>
          
          {data.length > 0 && (
            <button
              onClick={exportChart}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-white rounded-lg transition-colors"
              title="Export Chart"
            >
              <Download className="w-5 h-5" />
            </button>
          )}
          
          <button
            onClick={() => fetchVisualization()}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? "Loading..." : hasAttemptedLoad ? "Refresh" : "Load Chart"}
          </button>
        </div>
      </div>

      {/* Visualization Type Selector */}
      {availableVisualizations.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Available Visualizations:</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {availableVisualizations.map((viz) => (
              <button
                key={viz.endpoint}
                onClick={() => {
                  const vizType = viz.endpoint.split('/').pop();
                  fetchVisualization(vizType);
                }}
                className="p-3 text-left bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
              >
                <div className="font-medium text-sm text-gray-900">{viz.name}</div>
                <div className="text-xs text-gray-500 mt-1">{viz.description}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Settings Panel */}
      {showSettings && data.length > 0 && (
        <div className="bg-white rounded-xl p-4 mb-6 border border-gray-200 shadow-sm">
          <h3 className="font-semibold text-gray-900 mb-3">Chart Settings</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Chart Type</label>
              <div className="relative">
                <select
                  value={chartType}
                  onChange={(e) => setChartType(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white pr-8"
                >
                  {Object.entries(CHART_TYPES).map(([key, type]) => (
                    <option key={key} value={key}>{type.name}</option>
                  ))}
                </select>
                <ChevronDown className="w-4 h-4 text-gray-400 absolute right-2 top-3 pointer-events-none" />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Chart Title</label>
              <input
                type="text"
                value={chartTitle}
                onChange={(e) => setChartTitle(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter chart title"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">X-Axis</label>
                <select
                  value={nameKey}
                  onChange={(e) => setNameKey(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                >
                  {data.length > 0 && Object.keys(data[0]).map(key => (
                    <option key={key} value={key}>{key}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Y-Axis</label>
                <select
                  value={dataKey}
                  onChange={(e) => setDataKey(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                >
                  {data.length > 0 && Object.keys(data[0]).map(key => (
                    <option key={key} value={key}>{key}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Chart Type Selector */}
      {data.length > 0 && !showSettings && (
        <div className="flex items-center gap-2 mb-6">
          <span className="text-sm font-medium text-gray-700">Chart Type:</span>
          {Object.entries(CHART_TYPES).map(([key, type]) => {
            const IconComponent = type.icon;
            return (
              <button
                key={key}
                onClick={() => setChartType(key)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  chartType === key
                    ? 'bg-blue-100 text-blue-700 border border-blue-200'
                    : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
                }`}
              >
                <IconComponent className="w-4 h-4" />
                {type.name}
              </button>
            );
          })}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-16">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
            <div className="text-gray-600 font-medium">Generating visualization...</div>
            <div className="text-sm text-gray-500 mt-1">This may take a moment</div>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
              <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-red-900">Visualization Error</h3>
              <p className="text-red-700 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Chart Display */}
      {!loading && !error && hasAttemptedLoad && data.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-4 border-b border-gray-100 bg-gray-50">
            <h3 className="font-semibold text-gray-900">{chartTitle}</h3>
            <p className="text-sm text-gray-600 mt-1">
              {data.length} data points • {CHART_TYPES[chartType].name}
            </p>
          </div>
          
          <div className="p-6">
            {renderChart()}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && hasAttemptedLoad && data.length === 0 && (
        <div className="text-center py-16">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <BarChart3 className="w-10 h-10 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Data Available</h3>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Upload some documents and engage in conversations to generate data for visualization.
          </p>
          <div className="text-sm text-gray-500">
            <p>Try:</p>
            <ul className="list-disc list-inside mt-2 space-y-1">
              <li>Uploading research documents</li>
              <li>Asking analytical questions in chat</li>
              <li>Requesting data summaries or insights</li>
            </ul>
          </div>
        </div>
      )}

      {/* Welcome State */}
      {!hasAttemptedLoad && (
        <div className="text-center py-20">
          <div className="w-24 h-24 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full flex items-center justify-center mx-auto mb-8">
            <TrendingUp className="w-12 h-12 text-blue-600" />
          </div>
          <h3 className="text-xl font-bold text-gray-900 mb-3">Ready to Visualize</h3>
          <p className="text-gray-600 mb-8 max-w-lg mx-auto">
            Transform your research data into beautiful, interactive charts and gain deeper insights from your analysis.
          </p>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto mb-8">
            {Object.entries(CHART_TYPES).map(([key, type]) => {
              const IconComponent = type.icon;
              return (
                <div key={key} className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
                  <IconComponent className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                  <div className="text-sm font-medium text-gray-900">{type.name}</div>
                </div>
              );
            })}
          </div>
          
          <button
            onClick={() => fetchVisualization()}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-sm"
          >
            Generate First Visualization
          </button>
        </div>
      )}
    </div>
  );
}