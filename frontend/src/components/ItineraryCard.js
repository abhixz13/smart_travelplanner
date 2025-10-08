import React from 'react';
import { MapPin, Calendar, DollarSign, Clock } from 'lucide-react';

const ItineraryCard = ({ itinerary }) => {
  if (!itinerary) return null;

  // Ensure nested arrays are safe
  const safeDays = Array.isArray(itinerary.days) ? itinerary.days : [];
  const safeMetadata = itinerary.metadata || {};

  return (
    <div className="itinerary-card bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden mb-6" data-testid="itinerary-card">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 text-white px-6 py-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">{itinerary.destination || 'Travel Destination'}</h2>
            <div className="flex flex-wrap gap-4 text-sm">
              {itinerary.start_date && (
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  {itinerary.start_date} {itinerary.end_date && `- ${itinerary.end_date}`}
                </div>
              )}
              {itinerary.duration_days && (
                <div className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  {itinerary.duration_days} days
                </div>
              )}
              {itinerary.total_estimated_cost && (
                <div className="flex items-center gap-1">
                  <DollarSign className="w-4 h-4" />
                  ${Number(itinerary.total_estimated_cost).toFixed(2)}
                </div>
              )}
            </div>
          </div>
        </div>
        {itinerary.summary && (
          <p className="mt-4 text-primary-100">{itinerary.summary}</p>
        )}
      </div>

      {/* Day-by-day itinerary */}
      {safeDays.length > 0 && (
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Day-by-Day Itinerary</h3>
          <div className="space-y-6">
            {safeDays.map((day, index) => {
              // Ensure day object exists and has safe arrays
              const safeDay = day || {};
              const safeActivities = Array.isArray(safeDay.activities) ? safeDay.activities : [];
              const safeMeals = Array.isArray(safeDay.meals) ? safeDay.meals : [];

              return (
                <div key={index} className="border-l-4 border-primary-500 pl-4" data-testid={`day-${safeDay.day_number || index + 1}`}>
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-semibold text-gray-800">
                        Day {safeDay.day_number || index + 1}
                        {safeDay.date && <span className="text-gray-600 ml-2">({safeDay.date})</span>}
                      </h4>
                      {safeDay.location && (
                        <div className="flex items-center gap-1 text-sm text-gray-600 mt-1">
                          <MapPin className="w-3 h-3" />
                          {safeDay.location}
                        </div>
                      )}
                    </div>
                    {safeDay.estimated_cost && (
                      <div className="text-sm font-medium text-primary-600">
                        ${Number(safeDay.estimated_cost).toFixed(2)}
                      </div>
                    )}
                  </div>

                  {/* Activities */}
                  {safeActivities.length > 0 && (
                    <div className="mb-3">
                      <div className="text-xs font-semibold text-gray-500 uppercase mb-2">Activities</div>
                      <ul className="space-y-2">
                        {safeActivities.map((activity, idx) => {
                          const safeActivity = activity || {};
                          return (
                            <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                              <span className="text-primary-500 mt-1">•</span>
                              <div>
                                <div className="font-medium">{safeActivity.name || safeActivity.title || 'Activity'}</div>
                                {safeActivity.description && (
                                  <div className="text-gray-600 text-xs mt-1">{safeActivity.description}</div>
                                )}
                                {safeActivity.time && (
                                  <div className="text-gray-500 text-xs mt-1">⏰ {safeActivity.time}</div>
                                )}
                              </div>
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  )}

                  {/* Meals */}
                  {safeMeals.length > 0 && (
                    <div className="mb-3">
                      <div className="text-xs font-semibold text-gray-500 uppercase mb-2">Meals</div>
                      <div className="flex flex-wrap gap-2">
                        {safeMeals.map((meal, idx) => {
                          const safeMeal = meal || {};
                          return (
                            <span key={idx} className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded">
                              🍽️ {safeMeal.name || safeMeal.type || 'Meal'}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Accommodation */}
                  {safeDay.accommodation && (
                    <div className="mb-3">
                      <div className="text-xs font-semibold text-gray-500 uppercase mb-2">Accommodation</div>
                      <div className="text-sm text-gray-700">
                        🏨 {safeDay.accommodation.name || safeDay.accommodation.type || 'Hotel'}
                      </div>
                    </div>
                  )}

                  {/* Notes */}
                  {safeDay.notes && (
                    <div className="mt-2 text-xs text-gray-600 italic bg-gray-50 p-2 rounded">
                      💭 {safeDay.notes}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Metadata */}
      {Object.keys(safeMetadata).length > 0 && (
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <div className="text-xs text-gray-600">
            {safeMetadata.planning_notes && (
              <div>📝 {safeMetadata.planning_notes}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ItineraryCard;