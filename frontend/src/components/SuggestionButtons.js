import React from 'react';
import { Plane, Hotel, MapPin, Calendar, DollarSign, RefreshCw } from 'lucide-react';

const SuggestionButtons = ({ suggestions, onSelectSuggestion, isLoading }) => {
  // Ensure suggestions is always an array
  const safeSuggestions = Array.isArray(suggestions) ? suggestions : [];

  if (safeSuggestions.length === 0) return null;

  const getIcon = (description) => {
    if (!description) return <RefreshCw className="w-4 h-4" />;
    
    const lowerDesc = description.toLowerCase();
    if (lowerDesc.includes('flight')) return <Plane className="w-4 h-4" />;
    if (lowerDesc.includes('hotel') || lowerDesc.includes('accommodation')) return <Hotel className="w-4 h-4" />;
    if (lowerDesc.includes('activity') || lowerDesc.includes('things to do')) return <MapPin className="w-4 h-4" />;
    if (lowerDesc.includes('itinerary') || lowerDesc.includes('schedule')) return <Calendar className="w-4 h-4" />;
    if (lowerDesc.includes('cost') || lowerDesc.includes('budget')) return <DollarSign className="w-4 h-4" />;
    return <RefreshCw className="w-4 h-4" />;
  };

  return (
    <div className="bg-gradient-to-r from-primary-50 to-blue-50 border-t border-primary-100 px-4 py-4">
      <div className="max-w-3xl mx-auto">
        <h3 className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-2">
          <span className="text-sm">💡</span>
          Next Steps
        </h3>
        <div className="flex flex-wrap gap-2">
          {safeSuggestions.map((suggestion, index) => {
            // Ensure suggestion object has required properties
            const token = suggestion?.token || `suggestion-${index}`;
            const description = suggestion?.description || 'Continue';
            
            return (
              <button
                key={index}
                onClick={() => onSelectSuggestion && onSelectSuggestion(token)}
                disabled={isLoading}
                className="suggestion-btn bg-white hover:bg-primary-50 text-gray-800 px-3 py-2 rounded-md border border-primary-200 hover:border-primary-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1 shadow-xs text-xs"
                data-testid={`suggestion-${token}`}
              >
                {getIcon(description)}
                <span className="font-medium text-primary-600">[{token}]</span>
                <span className="truncate max-w-20">{description}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default SuggestionButtons;