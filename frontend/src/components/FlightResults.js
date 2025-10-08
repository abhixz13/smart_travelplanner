import React from 'react';
import { Plane, Clock, Users, CheckCircle } from 'lucide-react';

const FlightResults = ({ flights, onFlightSelect, selectedFlight }) => {
  // Ensure flights is always an array
  const safeFlights = Array.isArray(flights) ? flights : [];

  if (safeFlights.length === 0) return null;

  return (
    <div className="card mb-6" data-testid="flight-results">
      <div className="flex items-center gap-2 mb-4">
        <Plane className="w-6 h-6 text-primary-600" />
        <h3 className="text-xl font-bold text-gray-800">Flight Options</h3>
        {selectedFlight && (
          <span className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded-full">
            ✓ Flight Selected
          </span>
        )}
      </div>
      <div className="space-y-4">
        {safeFlights.map((flight, index) => {
          // Ensure flight object exists with safe defaults
          const safeFlight = flight || {};
          const isSelected = selectedFlight && selectedFlight.selectedIndex === index;
          
          return (
            <div
              key={index}
              className={`border rounded-lg p-4 transition-all cursor-pointer ${
                isSelected 
                  ? 'border-green-500 bg-green-50 ring-2 ring-green-200' 
                  : 'border-gray-200 hover:border-primary-500'
              }`}
              data-testid={`flight-option-${index}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-bold text-lg text-gray-800">{safeFlight.airline || 'Airline'}</span>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                      {safeFlight.flight_number || 'FL123'}
                    </span>
                    {isSelected && (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {safeFlight.departure_time || '10:00 AM'} - {safeFlight.arrival_time || '2:00 PM'}
                    </div>
                    {safeFlight.duration && (
                      <div className="flex items-center gap-1">
                        ⏱️ {safeFlight.duration}
                      </div>
                    )}
                    {safeFlight.stops !== undefined && (
                      <div className="flex items-center gap-1">
                        {safeFlight.stops === 0 ? '✅ Non-stop' : `🔁 ${safeFlight.stops} stop(s)`}
                      </div>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-primary-600">
                    ${safeFlight.price || safeFlight.cost || 0}
                  </div>
                  <div className="text-xs text-gray-500">{safeFlight.class || 'Economy'}</div>
                </div>
              </div>
              <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                <div className="text-sm text-gray-600">
                  {safeFlight.origin || 'SFO'} → {safeFlight.destination || 'NRT'}
                </div>
                {safeFlight.seats_available && (
                  <div className="text-xs text-gray-500 flex items-center gap-1">
                    <Users className="w-3 h-3" />
                    {safeFlight.seats_available} seats left
                  </div>
                )}
              </div>
              
              {/* Interactive Selection Button */}
              <button 
                onClick={() => onFlightSelect && onFlightSelect(safeFlight, index)}
                disabled={isSelected}
                className={`mt-3 w-full text-sm py-2 transition-all ${
                  isSelected 
                    ? 'bg-green-500 text-white cursor-default' 
                    : 'btn-primary hover:bg-primary-700'
                }`}
              >
                {isSelected ? (
                  <span className="flex items-center justify-center gap-2">
                    <CheckCircle className="w-4 h-4" />
                    Flight Selected
                  </span>
                ) : (
                  'Select Flight'
                )}
              </button>
            </div>
          );
        })}
      </div>
      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        📌 <strong>Demo:</strong> Select a flight to add it to your trip. You can change your selection anytime.
      </div>
    </div>
  );
};

export default FlightResults;