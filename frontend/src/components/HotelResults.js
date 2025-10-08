import React from 'react';
import { Hotel, MapPin, Star, Wifi, Coffee, DollarSign } from 'lucide-react';

const HotelResults = ({ hotels }) => {
  // Ensure hotels is always an array
  const safeHotels = Array.isArray(hotels) ? hotels : [];

  if (safeHotels.length === 0) return null;

  return (
    <div className="card mb-6" data-testid="hotel-results">
      <div className="flex items-center gap-2 mb-4">
        <Hotel className="w-6 h-6 text-primary-600" />
        <h3 className="text-xl font-bold text-gray-800">Hotel Options</h3>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {safeHotels.map((hotel, index) => {
          // Ensure hotel object exists with safe defaults
          const safeHotel = hotel || {};
          const safeAmenities = Array.isArray(safeHotel.amenities) ? safeHotel.amenities : [];

          return (
            <div
              key={index}
              className="border border-gray-200 rounded-lg overflow-hidden hover:border-primary-500 transition-colors cursor-pointer"
              data-testid={`hotel-option-${index}`}
            >
              {/* Hotel Image Placeholder */}
              <div className="h-40 bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-4xl">
                🏨
              </div>
              
              <div className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="font-bold text-gray-800 mb-1">{safeHotel.name || 'Hotel Name'}</h4>
                    <div className="flex items-center gap-1 text-sm text-gray-600 mb-2">
                      <MapPin className="w-3 h-3" />
                      {safeHotel.location || safeHotel.address || 'City Center'}
                    </div>
                  </div>
                  {safeHotel.rating && (
                    <div className="flex items-center gap-1 bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-sm font-semibold">
                      <Star className="w-3 h-3 fill-current" />
                      {safeHotel.rating}
                    </div>
                  )}
                </div>

                {safeHotel.description && (
                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">{safeHotel.description}</p>
                )}

                {/* Amenities */}
                {safeAmenities.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-3">
                    {safeAmenities.slice(0, 3).map((amenity, idx) => {
                      let icon = null;
                      if (amenity && typeof amenity === 'string') {
                        if (amenity.toLowerCase().includes('wifi')) icon = <Wifi className="w-3 h-3" />;
                        if (amenity.toLowerCase().includes('breakfast')) icon = <Coffee className="w-3 h-3" />;
                      }
                      
                      return (
                        <span key={idx} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded flex items-center gap-1">
                          {icon}
                          {amenity || 'Amenity'}
                        </span>
                      );
                    })}
                  </div>
                )}

                <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                  <div>
                    <div className="text-xl font-bold text-primary-600 flex items-center">
                      <DollarSign className="w-4 h-4" />
                      {safeHotel.price_per_night || safeHotel.price || 0}
                    </div>
                    <div className="text-xs text-gray-500">per night</div>
                  </div>
                  <button className="btn-secondary text-sm px-4 py-2">
                    View Details
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        📌 <strong>Demo:</strong> These are mock hotel results. Production version will integrate with real hotel APIs.
      </div>
    </div>
  );
};

export default HotelResults;