import React from 'react';
import { Plane, Hotel, MapPin, Calendar, DollarSign, RefreshCw } from 'lucide-react';

const SuggestionButtons = ({ suggestions, onSelectSuggestion, isLoading }) => {
  if (!suggestions || suggestions.length === 0) return null;

  const getIcon = (description) => {
    const lowerDesc = description.toLowerCase();
    if (lowerDesc.includes('flight')) return <Plane className="w-4 h-4" />;
    if (lowerDesc.includes('hotel') || lowerDesc.includes('accommodation')) return <Hotel className="w-4 h-4" />;
    if (lowerDesc.includes('activity') || lowerDesc.includes('things to do')) return <MapPin className="w-4 h-4" />;
    if (lowerDesc.includes('itinerary') || lowerDesc.includes('schedule')) return <Calendar className="w-4 h-4" />;
    if (lowerDesc.includes('cost') || lowerDesc.includes('budget')) return <DollarSign className="w-4 h-4" />;
    return <RefreshCw className="w-4 h-4" />;
  };

  return (
    <div className="bg-gradient-to-r from-primary-50 to-blue-50 border-t border-primary-100 px-4 py-6">
      <div className="max-w-4xl mx-auto">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <span className="text-lg">💡</span>
          Suggested Next Steps
        </h3>
        <div className="flex flex-wrap gap-3">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => onSelectSuggestion(suggestion.token)}
              disabled={isLoading}
              className="suggestion-btn bg-white hover:bg-primary-50 text-gray-800 px-4 py-3 rounded-lg border-2 border-primary-200 hover:border-primary-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-sm"
              data-testid={`suggestion-${suggestion.token}`}
            >
              {getIcon(suggestion.description)}
              <span className="font-medium text-primary-700">[{suggestion.token}]</span>
              <span className="text-sm">{suggestion.description}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SuggestionButtons;