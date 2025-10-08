import React from 'react';
import { Hotel, MapPin, Star, Wifi, Coffee, DollarSign, CheckCircle } from 'lucide-react';

const HotelResults = ({ hotels, onHotelSelect, selectedHotel }) => {
  // Ensure hotels is always an array
  const safeHotels = Array.isArray(hotels) ? hotels : [];

  if (safeHotels.length === 0) return null;

  return (
    <div className="card mb-6" data-testid="hotel-results">
      <div className="flex items-center gap-2 mb-4">
        <Hotel className="w-6 h-6 text-primary-600" />
        <h3 className="text-xl font-bold text-gray-800">Hotel Options</h3>
        {selectedHotel && (
          <span className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded-full">
            ✓ Hotel Selected
          </span>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {safeHotels.map((hotel, index) => {
          // Ensure hotel object exists with safe defaults
          const safeHotel = hotel || {};
          const safeAmenities = Array.isArray(safeHotel.amenities) ? safeHotel.amenities : [];
          const isSelected = selectedHotel && selectedHotel.selectedIndex === index;

          return (
            <div
              key={index}
              className={`border rounded-lg overflow-hidden transition-all cursor-pointer ${
                isSelected 
                  ? 'border-green-500 bg-green-50 ring-2 ring-green-200' 
                  : 'border-gray-200 hover:border-primary-500'
              }`}
              data-testid={`hotel-option-${index}`}
            >
              {/* Hotel Image Placeholder */}
              <div className="h-40 bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-4xl relative">
                🏨
                {isSelected && (
                  <div className="absolute top-3 right-3 bg-green-500 rounded-full p-1">
                    <CheckCircle className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>
              
              <div className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="flex items-start gap-2">
                      <h4 className="font-bold text-gray-800 mb-1 flex-1">{safeHotel.name || 'Hotel Name'}</h4>
                      {isSelected && (
                        <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                      )}
                    </div>
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

                <div className="flex items-center justify-between pt-3 border-t border-gray-100 mb-3">
                  <div>
                    <div className="text-xl font-bold text-primary-600 flex items-center">
                      <DollarSign className="w-4 h-4" />
                      {safeHotel.price_per_night || safeHotel.price || 0}
                    </div>
                    <div className="text-xs text-gray-500">per night</div>
                  </div>
                </div>

                {/* Interactive Selection Button */}
                <button 
                  onClick={() => onHotelSelect && onHotelSelect(safeHotel, index)}
                  disabled={isSelected}
                  className={`w-full text-sm py-2 px-4 transition-all ${
                    isSelected 
                      ? 'bg-green-500 text-white cursor-default rounded' 
                      : 'btn-secondary hover:bg-primary-50'
                  }`}
                >
                  {isSelected ? (
                    <span className="flex items-center justify-center gap-2">
                      <CheckCircle className="w-4 h-4" />
                      Hotel Selected
                    </span>
                  ) : (
                    'Select Hotel'
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
        📌 <strong>Demo:</strong> Select a hotel to add it to your trip. You can change your selection anytime.
      </div>
    </div>
  );
};

export default HotelResults;