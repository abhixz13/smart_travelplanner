import React from 'react';
import { MapPin, Clock, Users, DollarSign } from 'lucide-react';

const ActivityResults = ({ activities }) => {
  // Ensure activities is always an array
  const safeActivities = Array.isArray(activities) ? activities : [];

  if (safeActivities.length === 0) return null;

  return (
    <div className="card mb-6" data-testid="activity-results">
      <div className="flex items-center gap-2 mb-4">
        <MapPin className="w-6 h-6 text-primary-600" />
        <h3 className="text-xl font-bold text-gray-800">Activities & Experiences</h3>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {safeActivities.map((activity, index) => {
          // Ensure activity object exists with safe defaults
          const safeActivity = activity || {};

          return (
            <div
              key={index}
              className="border border-gray-200 rounded-lg overflow-hidden hover:border-primary-500 transition-colors cursor-pointer"
              data-testid={`activity-option-${index}`}
            >
              {/* Activity Image Placeholder */}
              <div className="h-32 bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center text-white text-3xl">
                {safeActivity.category === 'food' ? '🍜' : 
                 safeActivity.category === 'culture' ? '🏛️' :
                 safeActivity.category === 'adventure' ? '🏔️' : '🎆'}
              </div>
              
              <div className="p-4">
                <h4 className="font-bold text-gray-800 mb-2 line-clamp-2">
                  {safeActivity.name || safeActivity.title || 'Activity'}
                </h4>
                
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

                <div className="flex items-center justify-between pt-3 border-t border-gray-100">
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
                
                <button className="mt-3 w-full btn-secondary text-sm py-2">
                  Learn More
                </button>
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        📌 <strong>Demo:</strong> These are mock activity results. Production version will integrate with real activity APIs.
      </div>
    </div>
  );
};

export default ActivityResults;