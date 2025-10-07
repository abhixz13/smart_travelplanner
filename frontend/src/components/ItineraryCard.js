import React from 'react';
import { MapPin, Calendar, DollarSign, Clock } from 'lucide-react';

const ItineraryCard = ({ itinerary }) => {
  if (!itinerary) return null;

  return (
    <div className="itinerary-card bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden mb-6" data-testid="itinerary-card">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 text-white px-6 py-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">{itinerary.destination}</h2>
            <div className="flex flex-wrap gap-4 text-sm">
              {itinerary.start_date && (
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  {itinerary.start_date} {itinerary.end_date && `- ${itinerary.end_date}`}
                </div>
              )}
              <div className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {itinerary.duration_days} days
              </div>
              {itinerary.total_estimated_cost && (
                <div className="flex items-center gap-1">
                  <DollarSign className="w-4 h-4" />
                  ${itinerary.total_estimated_cost.toFixed(2)}
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
      {itinerary.days && itinerary.days.length > 0 && (
        <div className="p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Day-by-Day Itinerary</h3>
          <div className="space-y-6">
            {itinerary.days.map((day, index) => (
              <div key={index} className="border-l-4 border-primary-500 pl-4" data-testid={`day-${day.day_number}`}>
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="font-semibold text-gray-800">
                      Day {day.day_number}
                      {day.date && <span className="text-gray-600 ml-2">({day.date})</span>}
                    </h4>
                    {day.location && (
                      <div className="flex items-center gap-1 text-sm text-gray-600 mt-1">
                        <MapPin className="w-3 h-3" />
                        {day.location}
                      </div>
                    )}
                  </div>
                  {day.estimated_cost && (
                    <div className="text-sm font-medium text-primary-600">
                      ${day.estimated_cost.toFixed(2)}
                    </div>
                  )}
                </div>

                {/* Activities */}
                {day.activities && day.activities.length > 0 && (
                  <div className="mb-3">
                    <div className="text-xs font-semibold text-gray-500 uppercase mb-2">Activities</div>
                    <ul className="space-y-2">
                      {day.activities.map((activity, idx) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                          <span className="text-primary-500 mt-1">•</span>
                          <div>
                            <div className="font-medium">{activity.name || activity.title}</div>
                            {activity.description && (
                              <div className="text-gray-600 text-xs mt-1">{activity.description}</div>
                            )}
                            {activity.time && (
                              <div className="text-gray-500 text-xs mt-1">⏰ {activity.time}</div>
                            )}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Meals */}
                {day.meals && day.meals.length > 0 && (
                  <div className="mb-3">
                    <div className="text-xs font-semibold text-gray-500 uppercase mb-2">Meals</div>
                    <div className="flex flex-wrap gap-2">
                      {day.meals.map((meal, idx) => (
                        <span key={idx} className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded">
                          🍽️ {meal.name || meal.type}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Accommodation */}
                {day.accommodation && (
                  <div className="mb-3">
                    <div className="text-xs font-semibold text-gray-500 uppercase mb-2">Accommodation</div>
                    <div className="text-sm text-gray-700">
                      🏨 {day.accommodation.name || day.accommodation.type}
                    </div>
                  </div>
                )}

                {/* Notes */}
                {day.notes && (
                  <div className="mt-2 text-xs text-gray-600 italic bg-gray-50 p-2 rounded">
                    💭 {day.notes}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metadata */}
      {itinerary.metadata && Object.keys(itinerary.metadata).length > 0 && (
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <div className="text-xs text-gray-600">
            {itinerary.metadata.planning_notes && (
              <div>📝 {itinerary.metadata.planning_notes}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ItineraryCard;