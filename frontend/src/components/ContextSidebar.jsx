import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import { ChevronDownIcon, ChevronRightIcon, DocumentTextIcon, FolderIcon, PlusIcon, TrashIcon, XCircleIcon } from '@heroicons/react/24/outline';
import api from '../utils/api';

const ContextSidebar = forwardRef((props, ref) => {
  const [contexts, setContexts] = useState([]);
  const [currentContext, setCurrentContext] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expandedContexts, setExpandedContexts] = useState(new Set());
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newContextName, setNewContextName] = useState('');
  const [deletingContext, setDeletingContext] = useState(null);

  // Expose methods for parent components
  useImperativeHandle(ref, () => ({ 
    fetchContexts,
    refreshContexts: fetchContexts
  }));

  useEffect(() => {
    fetchContexts();
  }, []);

  const fetchContexts = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/context/');
      const fetchedContexts = res.data.contexts || [];
      const current = res.data.current || null;
      
      setContexts(fetchedContexts);
      setCurrentContext(current);
      
      // Auto-expand current context
      if (current) {
        setExpandedContexts(prev => new Set([...prev, current]));
      }
    } catch (err) {
      console.error('Context fetch error:', err);
      setError(err.userMessage || 'Failed to load contexts.');
      
      // Fallback mock data for development
      const mockContexts = [
        { 
          id: 'getting-started', 
          topic: 'Getting Started', 
          sources: ['Lecture 15 Computational Intelligence (Rev).docx'],
          created_at: new Date().toISOString(),
          message_count: 3
        }
      ];
      setContexts(mockContexts);
      setCurrentContext('getting-started');
    }
    setLoading(false);
  };

  const switchContext = async (id) => {
    if (id === currentContext) return;
    
    setLoading(true);
    setError('');
    try {
      await api.post('/context/', { context_id: id });
      setCurrentContext(id);
      
      // Notify parent component about context switch
      if (props.onContextSwitch) {
        props.onContextSwitch(id);
      }
    } catch (err) {
      console.error('Context switch error:', err);
      setError(err.userMessage || 'Failed to switch context.');
      // Still update UI for development
      setCurrentContext(id);
    }
    setLoading(false);
  };

  const createNewContext = async () => {
    if (!newContextName.trim()) return;
    
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/context/new', { 
        topic: newContextName.trim() 
      });
      
      await fetchContexts(); // Refresh contexts
      setNewContextName('');
      setShowCreateForm(false);
      
      // Switch to new context if created successfully
      if (res.data.context_id) {
        await switchContext(res.data.context_id);
      }
    } catch (err) {
      console.error('Context creation error:', err);
      setError(err.userMessage || 'Failed to create new context.');
    }
    setLoading(false);
  };

  const deleteContext = async (contextId, e) => {
    e.stopPropagation(); // Prevent context switch
    
    if (!confirm('Are you sure you want to delete this context? This action cannot be undone.')) {
      return;
    }
    
    setDeletingContext(contextId);
    try {
      await api.delete(`/context/${contextId}`);
      await fetchContexts(); // Refresh contexts
      
      // If we deleted the current context, clear it
      if (contextId === currentContext) {
        setCurrentContext(null);
      }
    } catch (err) {
      console.error('Context deletion error:', err);
      setError(err.userMessage || 'Failed to delete context.');
    }
    setDeletingContext(null);
  };

  const toggleContextExpansion = (contextId, e) => {
    e.stopPropagation();
    setExpandedContexts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(contextId)) {
        newSet.delete(contextId);
      } else {
        newSet.add(contextId);
      }
      return newSet;
    });
  };

  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Unknown';
    }
  };

  const dismissError = () => setError('');

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="p-4 border-b bg-white">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center">
            <FolderIcon className="w-5 h-5 mr-2 text-blue-600" />
            Research Contexts
          </h2>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
            title="Create new context"
          >
            <PlusIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Create New Context Form */}
        {showCreateForm && (
          <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <input
              type="text"
              value={newContextName}
              onChange={(e) => setNewContextName(e.target.value)}
              placeholder="Enter context topic..."
              className="w-full p-2 text-sm border border-blue-200 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              onKeyPress={(e) => e.key === 'Enter' && createNewContext()}
              autoFocus
            />
            <div className="flex justify-end gap-2 mt-2">
              <button
                onClick={() => {
                  setShowCreateForm(false);
                  setNewContextName('');
                }}
                className="px-3 py-1 text-xs text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={createNewContext}
                disabled={!newContextName.trim() || loading}
                className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Create
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="p-4">
          <div className="flex items-center text-gray-500 text-sm">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
            Loading contexts...
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4">
          <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            <XCircleIcon className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <div className="font-medium">Error</div>
              <div>{error}</div>
            </div>
            <button 
              onClick={dismissError}
              className="text-red-500 hover:text-red-700"
            >
              <XCircleIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Contexts List */}
      <div className="flex-1 overflow-auto p-4">
        <div className="space-y-2">
          {contexts.map((ctx) => {
            const isExpanded = expandedContexts.has(ctx.id);
            const isActive = ctx.id === currentContext;
            const hasSource = ctx.sources && ctx.sources.length > 0;
            
            return (
              <div key={ctx.id} className="group">
                <div
                  onClick={() => switchContext(ctx.id)}
                  className={`relative flex items-center p-3 rounded-lg cursor-pointer transition-all duration-200 ${
                    isActive 
                      ? 'bg-blue-600 text-white shadow-md' 
                      : 'bg-white hover:bg-gray-50 border border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {/* Expand/Collapse Button */}
                  {hasSource && (
                    <button
                      onClick={(e) => toggleContextExpansion(ctx.id, e)}
                      className={`mr-2 p-0.5 rounded transition-colors ${
                        isActive 
                          ? 'hover:bg-blue-500' 
                          : 'hover:bg-gray-200'
                      }`}
                    >
                      {isExpanded ? (
                        <ChevronDownIcon className="w-4 h-4" />
                      ) : (
                        <ChevronRightIcon className="w-4 h-4" />
                      )}
                    </button>
                  )}
                  
                  {/* Context Info */}
                  <div className={`flex-1 ${!hasSource ? 'ml-6' : ''}`}>
                    <div className="font-medium text-sm truncate">
                      {ctx.topic}
                    </div>
                    <div className={`text-xs mt-1 flex items-center gap-3 ${
                      isActive ? 'text-blue-100' : 'text-gray-500'
                    }`}>
                      {hasSource && (
                        <span>{ctx.sources.length} file{ctx.sources.length !== 1 ? 's' : ''}</span>
                      )}
                      {ctx.message_count && (
                        <span>{ctx.message_count} message{ctx.message_count !== 1 ? 's' : ''}</span>
                      )}
                      {ctx.created_at && (
                        <span>{formatDate(ctx.created_at)}</span>
                      )}
                    </div>
                  </div>

                  {/* Delete Button */}
                  <button
                    onClick={(e) => deleteContext(ctx.id, e)}
                    disabled={deletingContext === ctx.id}
                    className={`opacity-0 group-hover:opacity-100 p-1 rounded transition-all ${
                      isActive 
                        ? 'hover:bg-blue-500 text-blue-100' 
                        : 'hover:bg-red-50 text-red-500'
                    } ${deletingContext === ctx.id ? 'opacity-100' : ''}`}
                    title="Delete context"
                  >
                    {deletingContext === ctx.id ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                    ) : (
                      <TrashIcon className="w-4 h-4" />
                    )}
                  </button>
                </div>

                {/* Expanded Sources */}
                {isExpanded && hasSource && (
                  <div className="mt-2 ml-6 space-y-1">
                    {ctx.sources.map((source, i) => (
                      <div 
                        key={i} 
                        className="flex items-center text-xs text-gray-600 p-2 bg-gray-50 rounded border"
                      >
                        <DocumentTextIcon className="w-3 h-3 mr-2 text-gray-400 flex-shrink-0" />
                        <span className="truncate" title={source}>
                          {source}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Empty State */}
        {contexts.length === 0 && !loading && (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <FolderIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <div className="text-gray-500 mb-2">No research contexts yet</div>
              <div className="text-sm text-gray-400">
                Upload a file or create a new context to get started
              </div>
            </div>
            <button
              onClick={() => setShowCreateForm(true)}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Create Your First Context
            </button>
          </div>
        )}
      </div>

      {/* Footer Info */}
      {currentContext && (
        <div className="p-3 border-t bg-white">
          <div className="text-xs text-gray-500">
            Active: <span className="font-medium text-gray-700">
              {contexts.find(c => c.id === currentContext)?.topic || 'Unknown Context'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
});

ContextSidebar.displayName = 'ContextSidebar';

export default ContextSidebar;

