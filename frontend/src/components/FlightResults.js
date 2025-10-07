import React from 'react';
import { Plane, Clock, DollarSign, Users } from 'lucide-react';

const FlightResults = ({ flights }) => {
  if (!flights || flights.length === 0) return null;

  return (
    <div className="card mb-6" data-testid="flight-results">
      <div className="flex items-center gap-2 mb-4">
        <Plane className="w-6 h-6 text-primary-600" />
        <h3 className="text-xl font-bold text-gray-800">Flight Options</h3>
      </div>
      <div className="space-y-4">
        {flights.map((flight, index) => (
          <div
            key={index}
            className="border border-gray-200 rounded-lg p-4 hover:border-primary-500 transition-colors cursor-pointer"
            data-testid={`flight-option-${index}`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className="font-bold text-lg text-gray-800">{flight.airline || 'Airline'}</span>
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                    {flight.flight_number || 'FL123'}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-600">
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {flight.departure_time || '10:00 AM'} - {flight.arrival_time || '2:00 PM'}
                  </div>
                  {flight.duration && (
                    <div className="flex items-center gap-1">
                      ⏱️ {flight.duration}
                    </div>
                  )}
                  {flight.stops !== undefined && (
                    <div className="flex items-center gap-1">
                      {flight.stops === 0 ? '✅ Non-stop' : `🔁 ${flight.stops} stop(s)`}
                    </div>
                  )}
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-primary-600">
                  ${flight.price || flight.cost || 0}
                </div>
                <div className="text-xs text-gray-500">{flight.class || 'Economy'}</div>
              </div>
            </div>
            <div className="flex items-center justify-between pt-3 border-t border-gray-100">
              <div className="text-sm text-gray-600">
                {flight.origin || 'SFO'} → {flight.destination || 'NRT'}
              </div>
              {flight.seats_available && (
                <div className="text-xs text-gray-500 flex items-center gap-1">
                  <Users className="w-3 h-3" />
                  {flight.seats_available} seats left
                </div>
              )}
            </div>
            {/* TODO: Add booking button when payment integration is ready */}
            <button className="mt-3 w-full btn-secondary text-sm py-2">
              Select Flight
            </button>
          </div>
        ))}
      </div>
      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        📌 <strong>TODO:</strong> These are mock flight results. In production, integrate with Amadeus or Skyscanner API.
      </div>
    </div>
  );
};

export default FlightResults;