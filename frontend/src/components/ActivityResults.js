import React from 'react';
import { MapPin, Clock, Users, DollarSign, Plus, Check } from 'lucide-react';

const ActivityResults = ({ activities, onActivitySelect, selectedActivities }) => {
  // Ensure activities is always an array
  const safeActivities = Array.isArray(activities) ? activities : [];
  const safeSelectedActivities = Array.isArray(selectedActivities) ? selectedActivities : [];

  if (safeActivities.length === 0) return null;

  const isActivitySelected = (index) => {
    return safeSelectedActivities.some(activity => activity.selectedIndex === index);
  };

  return (
    <div className="card mb-6" data-testid="activity-results">
      <div className="flex items-center gap-2 mb-4">
        <MapPin className="w-6 h-6 text-primary-600" />
        <h3 className="text-xl font-bold text-gray-800">Activities & Experiences</h3>
        {safeSelectedActivities.length > 0 && (
          <span className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded-full">
            ✓ {safeSelectedActivities.length} Selected
          </span>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {safeActivities.map((activity, index) => {
          // Ensure activity object exists with safe defaults
          const safeActivity = activity || {};
          const isSelected = isActivitySelected(index);

          return (
            <div
              key={index}
              className={`border rounded-lg overflow-hidden transition-all cursor-pointer ${
                isSelected 
                  ? 'border-green-500 bg-green-50 ring-2 ring-green-200' 
                  : 'border-gray-200 hover:border-primary-500'
              }`}
              data-testid={`activity-option-${index}`}
            >
              {/* Activity Image Placeholder */}
              <div className="h-32 bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center text-white text-3xl relative">
                {safeActivity.category === 'food' ? '🍜' : 
                 safeActivity.category === 'culture' ? '🏛️' :
                 safeActivity.category === 'adventure' ? '🏔️' : '🎆'}
                {isSelected && (
                  <div className="absolute top-2 right-2 bg-green-500 rounded-full p-1">
                    <Check className="w-3 h-3 text-white" />
                  </div>
                )}
              </div>
              
              <div className="p-4">
                <div className="flex items-start gap-2 mb-2">
                  <h4 className="font-bold text-gray-800 mb-2 line-clamp-2 flex-1">
                    {safeActivity.name || safeActivity.title || 'Activity'}
                  </h4>
                  {isSelected && (
                    <Check className="w-4 h-4 text-green-500 flex-shrink-0 mt-1" />
                  )}
                </div>
                
                {safeActivity.description && (
                  <p className="text-sm text-gray-600 mb-3 line-clamp-3">{safeActivity.description}</p>
                )}

                <div className="space-y-2 mb-3">
                  {safeActivity.duration && (
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Clock className="w-4 h-4" />
                      {safeActivity.duration}
                    </div>
                  )}
                  {safeActivity.location && (
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <MapPin className="w-4 h-4" />
                      {safeActivity.location}
                    </div>
                  )}
                  {safeActivity.group_size && (
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Users className="w-4 h-4" />
                      {safeActivity.group_size}
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-gray-100 mb-3">
                  {safeActivity.price !== undefined && (
                    <div className="font-bold text-primary-600 flex items-center">
                      <DollarSign className="w-4 h-4" />
                      {safeActivity.price}
                    </div>
                  )}
                  {safeActivity.category && (
                    <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                      {safeActivity.category}
                    </span>
                  )}
                </div>
                
                {/* Interactive Selection Button */}
                <button 
                  onClick={() => onActivitySelect && onActivitySelect(safeActivity, index)}
                  className={`w-full text-sm py-2 transition-all ${
                    isSelected 
                      ? 'bg-red-500 hover:bg-red-600 text-white' 
                      : 'bg-green-500 hover:bg-green-600 text-white'
                  }`}
                >
                  {isSelected ? (
                    <span className="flex items-center justify-center gap-2">
                      <Check className="w-4 h-4" />
                      Remove from Trip
                    </span>
                  ) : (
                    <span className="flex items-center justify-center gap-2">
                      <Plus className="w-4 h-4" />
                      Add to Trip
                    </span>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        📌 <strong>Demo:</strong> Select multiple activities to add them to your trip. Click again to remove.
      </div>
    </div>
  );
};

export default ActivityResults;