import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

// Components
import ChatInterface from './components/ChatInterface';
import SuggestionButtons from './components/SuggestionButtons';
import ItineraryCard from './components/ItineraryCard';
import FlightResults from './components/FlightResults';
import HotelResults from './components/HotelResults';
import ActivityResults from './components/ActivityResults';

// Icons
import { Plane, Menu, X, MessageSquare, History } from 'lucide-react';

// Backend API URL
const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  // State management - Initialize with proper default values
  const [messages, setMessages] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [currentItinerary, setCurrentItinerary] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState('default');
  const [sessions, setSessions] = useState([]);
  const [showSidebar, setShowSidebar] = useState(false);
  const [error, setError] = useState(null);
  const [backendAvailable, setBackendAvailable] = useState(true);

  // New state for user selections
  const [selectedFlight, setSelectedFlight] = useState(null);
  const [selectedHotel, setSelectedHotel] = useState(null);
  const [selectedActivities, setSelectedActivities] = useState([]);

  // Mock data for tool results (flights, hotels, activities)
  const [toolResults, setToolResults] = useState({
    flights: null,
    hotels: null,
    activities: null
  });

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Safe array helper function
  const ensureArray = (value) => {
    if (Array.isArray(value)) return value;
    return [];
  };

  // Handle flight selection
  const handleFlightSelection = (flight, index) => {
    setSelectedFlight({ ...flight, selectedIndex: index });
    
    // Add confirmation message to chat
    const confirmationMessage = {
      type: 'ai',
      content: `✅ Great choice! I've selected ${flight.airline || 'the'} flight ${flight.flight_number || ''} for $${flight.price || flight.cost || 0}. This flight departs at ${flight.departure_time || 'scheduled time'} and arrives at ${flight.arrival_time || 'destination'}.`,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, confirmationMessage]);

    // Update suggestions with next steps
    setSuggestions([
      { token: 'hotels', description: 'Browse hotel options' },
      { token: 'activities', description: 'Find activities' },
      { token: 'modify-flight', description: 'Choose different flight' }
    ]);
  };

  // Handle hotel selection
  const handleHotelSelection = (hotel, index) => {
    setSelectedHotel({ ...hotel, selectedIndex: index });
    
    // Add confirmation message to chat
    const confirmationMessage = {
      type: 'ai',
      content: `🏨 Excellent! I've noted ${hotel.name || 'this hotel'} as your accommodation. Located in ${hotel.location || 'the city'}, this ${hotel.rating ? hotel.rating + '-star' : ''} hotel costs $${hotel.price_per_night || hotel.price || 0} per night.`,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, confirmationMessage]);

    // Update suggestions with next steps
    setSuggestions([
      { token: 'activities', description: 'Discover activities' },
      { token: 'itinerary', description: 'Create detailed itinerary' },
      { token: 'modify-hotel', description: 'Choose different hotel' }
    ]);
  };

  // Handle activity selection
  const handleActivitySelection = (activity, index) => {
    const isAlreadySelected = selectedActivities.some(a => a.selectedIndex === index);
    
    if (isAlreadySelected) {
      // Remove activity
      setSelectedActivities(prev => prev.filter(a => a.selectedIndex !== index));
      
      const removalMessage = {
        type: 'ai',
        content: `❌ Removed "${activity.name || activity.title || 'activity'}" from your selections.`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, removalMessage]);
    } else {
      // Add activity
      setSelectedActivities(prev => [...prev, { ...activity, selectedIndex: index }]);
      
      const confirmationMessage = {
        type: 'ai',
        content: `🎉 Added "${activity.name || activity.title || 'activity'}" to your trip! This ${activity.duration || 'experience'} costs $${activity.price || 0} and takes place in ${activity.location || 'the area'}.`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, confirmationMessage]);
    }

    // Update suggestions
    setSuggestions([
      { token: 'more-activities', description: 'Find more activities' },
      { token: 'itinerary', description: 'Create final itinerary' },
      { token: 'summary', description: 'Review selections' }
    ]);
  };

  // API call to send chat message with improved error handling
  const sendMessage = async (query) => {
    setIsLoading(true);
    setError(null);

    try {
      // Add user message to UI immediately
      const userMessage = {
        type: 'user',
        content: query,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, userMessage]);

      if (!backendAvailable) {
        // Handle offline mode with mock responses
        handleMockResponse(query);
        return;
      }

      // Call backend API
      const response = await axios.post(`${API_URL}/api/chat`, {
        query,
        thread_id: threadId,
        user_preferences: {},
        selected_flight: selectedFlight,
        selected_hotel: selectedHotel,
        selected_activities: selectedActivities
      }, {
        timeout: 180000 // Increased to 180 seconds
      });

      if (response.data) {
        // Add AI response to messages
        const aiMessage = {
          type: 'ai',
          content: response.data.response || 'I received your request and I\'m working on a response.',
          timestamp: response.data.timestamp || new Date().toISOString()
        };
        setMessages(prev => [...prev, aiMessage]);

        // Update suggestions - ensure it's an array
        setSuggestions(ensureArray(response.data.suggestions));

        // Update current itinerary if available
        if (response.data.current_itinerary) {
          setCurrentItinerary(response.data.current_itinerary);
        }

        // Extract tool results from response
        extractToolResults(response.data);
      }

    } catch (err) {
      console.error('Error sending message:', err);
      setBackendAvailable(false);
      
      // Handle backend unavailable - switch to mock mode
      const errorMessage = {
        type: 'ai',
        content: 'I\'m running in demo mode right now. Let me show you what I can do with some sample data!',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
      
      // Generate mock response
      setTimeout(() => {
        handleMockResponse(query);
      }, 1000);
      
    } finally {
      setIsLoading(false);
    }
  };

  // Handle mock responses when backend is unavailable
  const handleMockResponse = (query) => {
    const lowerQuery = query.toLowerCase();
    
    let mockResponse = "I understand you're looking for travel assistance. Here's what I can help you with in demo mode:";
    let mockSuggestions = [
      { token: 'flights', description: 'Show sample flights' },
      { token: 'hotels', description: 'Browse hotel options' },
      { token: 'activities', description: 'Discover activities' },
      { token: 'itinerary', description: 'Create sample itinerary' }
    ];

    // Generate relevant mock data based on query
    if (lowerQuery.includes('flight')) {
      setToolResults(prev => ({
        ...prev,
        flights: generateMockFlights()
      }));
      mockResponse = "Here are some sample flight options for your trip:";
    }
    
    if (lowerQuery.includes('hotel')) {
      setToolResults(prev => ({
        ...prev,
        hotels: generateMockHotels()
      }));
      mockResponse = "I found some great hotel options for you:";
    }
    
    if (lowerQuery.includes('activity')) {
      setToolResults(prev => ({
        ...prev,
        activities: generateMockActivities()
      }));
      mockResponse = "Here are some exciting activities you might enjoy:";
    }

    if (lowerQuery.includes('japan') || lowerQuery.includes('tokyo')) {
      setCurrentItinerary(generateMockItinerary());
      mockResponse = "I've created a sample 7-day Japan itinerary for you:";
    }

    // Handle selection summaries
    if (lowerQuery.includes('summary') || lowerQuery.includes('review')) {
      mockResponse = generateSelectionSummary();
    }

    const aiMessage = {
      type: 'ai',
      content: mockResponse,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, aiMessage]);
    setSuggestions(mockSuggestions);
  };

  // Generate selection summary
  const generateSelectionSummary = () => {
    let summary = "📋 Here's a summary of your current selections:\n\n";
    
    if (selectedFlight) {
      summary += `✈️ **Flight**: ${selectedFlight.airline} ${selectedFlight.flight_number} - $${selectedFlight.price || selectedFlight.cost}\n`;
      summary += `   ${selectedFlight.departure_time} to ${selectedFlight.arrival_time}\n\n`;
    }
    
    if (selectedHotel) {
      summary += `🏨 **Hotel**: ${selectedHotel.name} - $${selectedHotel.price_per_night || selectedHotel.price}/night\n`;
      summary += `   ${selectedHotel.location}${selectedHotel.rating ? ` (${selectedHotel.rating}★)` : ''}\n\n`;
    }
    
    if (selectedActivities.length > 0) {
      summary += `🎯 **Activities** (${selectedActivities.length} selected):\n`;
      selectedActivities.forEach(activity => {
        summary += `   • ${activity.name || activity.title} - $${activity.price || 0}\n`;
      });
      summary += '\n';
    }
    
    if (!selectedFlight && !selectedHotel && selectedActivities.length === 0) {
      summary = "You haven't made any selections yet. Browse through the available options and click 'Select' to add them to your trip!";
    } else {
      const totalCost = (selectedFlight?.price || selectedFlight?.cost || 0) + 
                       (selectedHotel?.price_per_night || selectedHotel?.price || 0) + 
                       selectedActivities.reduce((sum, activity) => sum + (activity.price || 0), 0);
      summary += `💰 **Estimated Total**: $${totalCost}`;
    }
    
    return summary;
  };

  // API call to handle suggestion selection with error handling
  const handleSuggestionSelect = async (token) => {
    setIsLoading(true);
    setError(null);

    try {
      // Add user selection message
      const userMessage = {
        type: 'user',
        content: `Selected: ${token}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, userMessage]);

      if (!backendAvailable) {
        handleMockSuggestionResponse(token);
        return;
      }

      // Call backend API
      const response = await axios.post(`${API_URL}/api/suggestion`, {
        token,
        thread_id: threadId,
        selected_flight: selectedFlight,
        selected_hotel: selectedHotel,
        selected_activities: selectedActivities
      }, {
        timeout: 180000 // Increased to 180 seconds
      });

      if (response.data) {
        // Add AI response
        const aiMessage = {
          type: 'ai',
          content: response.data.response || 'Processing your selection...',
          timestamp: response.data.timestamp || new Date().toISOString()
        };
        setMessages(prev => [...prev, aiMessage]);

        // Update suggestions
        setSuggestions(ensureArray(response.data.suggestions));

        // Update current itinerary
        if (response.data.current_itinerary) {
          setCurrentItinerary(response.data.current_itinerary);
        }

        // Extract tool results
        extractToolResults(response.data);
      }

    } catch (err) {
      console.error('Error handling suggestion:', err);
      setBackendAvailable(false);
      handleMockSuggestionResponse(token);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle mock suggestion responses
  const handleMockSuggestionResponse = (token) => {
    let response = '';
    
    switch (token) {
      case 'flights':
        setToolResults(prev => ({ ...prev, flights: generateMockFlights() }));
        response = 'Here are some sample flight options:';
        break;
      case 'hotels':
        setToolResults(prev => ({ ...prev, hotels: generateMockHotels() }));
        response = 'Here are some hotel recommendations:';
        break;
      case 'activities':
      case 'more-activities':
        setToolResults(prev => ({ ...prev, activities: generateMockActivities() }));
        response = 'Here are some activity suggestions:';
        break;
      case 'itinerary':
        setCurrentItinerary(generateMockItineraryWithSelections());
        response = 'I\'ve created a personalized itinerary based on your selections:';
        break;
      case 'summary':
        response = generateSelectionSummary();
        break;
      case 'modify-flight':
        setSelectedFlight(null);
        setToolResults(prev => ({ ...prev, flights: generateMockFlights() }));
        response = 'Let\'s find you a different flight. Here are the available options:';
        break;
      case 'modify-hotel':
        setSelectedHotel(null);
        setToolResults(prev => ({ ...prev, hotels: generateMockHotels() }));
        response = 'No problem! Here are other hotel options to choose from:';
        break;
      default:
        response = 'Here\'s some information about your selection:';
    }

    const aiMessage = {
      type: 'ai',
      content: response,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, aiMessage]);
  };

  // Extract mock tool results from response
  const extractToolResults = (data) => {
    if (!data || !data.response) return;
    
    const content = data.response.toLowerCase();
    
    // Mock flight data
    if (content.includes('flight')) {
      setToolResults(prev => ({
        ...prev,
        flights: generateMockFlights()
      }));
    }
    
    // Mock hotel data
    if (content.includes('hotel') || content.includes('accommodation')) {
      setToolResults(prev => ({
        ...prev,
        hotels: generateMockHotels()
      }));
    }
    
    // Mock activity data
    if (content.includes('activity') || content.includes('activities')) {
      setToolResults(prev => ({
        ...prev,
        activities: generateMockActivities()
      }));
    }
  };

  // Load all sessions with error handling
  const loadSessions = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/sessions`, {
        timeout: 5000
      });
      setSessions(ensureArray(response.data));
    } catch (err) {
      console.error('Error loading sessions:', err);
      setBackendAvailable(false);
      // Use mock sessions for demo
      setSessions([
        { thread_id: 'demo-japan', last_active: new Date().toISOString(), has_itinerary: true },
        { thread_id: 'demo-paris', last_active: new Date().toISOString(), has_itinerary: false }
      ]);
    }
  };

  // Switch to a different session
  const switchSession = (newThreadId) => {
    setThreadId(newThreadId);
    setMessages([]);
    setSuggestions([]);
    setCurrentItinerary(null);
    setToolResults({ flights: null, hotels: null, activities: null });
    // Clear selections when switching sessions
    setSelectedFlight(null);
    setSelectedHotel(null);
    setSelectedActivities([]);
    setShowSidebar(false);
  };

  // Create new session
  const createNewSession = () => {
    const newThreadId = `session_${Date.now()}`;
    switchSession(newThreadId);
  };

  // Mock data generators
  const generateMockFlights = () => [
    {
      airline: 'Japan Airlines',
      flight_number: 'JAL001',
      origin: 'SFO',
      destination: 'NRT',
      departure_time: '10:30 AM',
      arrival_time: '2:15 PM (+1)',
      duration: '11h 45m',
      price: 850,
      class: 'Economy',
      stops: 0,
      seats_available: 12
    },
    {
      airline: 'ANA',
      flight_number: 'NH007',
      origin: 'SFO',
      destination: 'NRT',
      departure_time: '1:00 PM',
      arrival_time: '4:45 PM (+1)',
      duration: '11h 45m',
      price: 820,
      class: 'Economy',
      stops: 0,
      seats_available: 8
    },
    {
      airline: 'United Airlines',
      flight_number: 'UA837',
      origin: 'SFO',
      destination: 'NRT',
      departure_time: '11:00 AM',
      arrival_time: '3:00 PM (+1)',
      duration: '12h 00m',
      price: 780,
      class: 'Economy',
      stops: 0,
      seats_available: 20
    }
  ];

  const generateMockHotels = () => [
    {
      name: 'Tokyo Grand Hotel',
      location: 'Shinjuku, Tokyo',
      rating: 4.5,
      price_per_night: 150,
      description: 'Modern hotel in the heart of Tokyo with stunning city views',
      amenities: ['Free WiFi', 'Breakfast included', 'Gym', 'Restaurant']
    },
    {
      name: 'Sakura Inn',
      location: 'Shibuya, Tokyo',
      rating: 4.2,
      price_per_night: 120,
      description: 'Boutique hotel with traditional Japanese design',
      amenities: ['Free WiFi', 'Onsen', 'Tea ceremony room']
    },
    {
      name: 'Business Plaza Tokyo',
      location: 'Ginza, Tokyo',
      rating: 4.0,
      price_per_night: 100,
      description: 'Affordable hotel perfect for budget travelers',
      amenities: ['Free WiFi', 'Breakfast', '24/7 reception']
    }
  ];

  const generateMockActivities = () => [
    {
      name: 'Tokyo Food Tour',
      category: 'food',
      duration: '3 hours',
      location: 'Tsukiji Market',
      price: 75,
      description: 'Explore Tokyo\'s best street food and local delicacies',
      group_size: 'Small group (max 10)'
    },
    {
      name: 'Senso-ji Temple Visit',
      category: 'culture',
      duration: '2 hours',
      location: 'Asakusa',
      price: 25,
      description: 'Guided tour of Tokyo\'s oldest temple',
      group_size: 'Medium group'
    },
    {
      name: 'Mt. Fuji Day Trip',
      category: 'adventure',
      duration: 'Full day',
      location: 'Mt. Fuji',
      price: 150,
      description: 'Scenic tour to Japan\'s iconic mountain',
      group_size: 'Large group'
    },
    {
      name: 'Tokyo Nightlife Experience',
      category: 'nightlife',
      duration: '4 hours',
      location: 'Roppongi',
      price: 90,
      description: 'Experience Tokyo\'s vibrant nightlife',
      group_size: 'Small group'
    }
  ];

  const generateMockItinerary = () => ({
    destination: 'Tokyo, Japan',
    start_date: '2024-06-01',
    end_date: '2024-06-07',
    duration_days: 7,
    total_estimated_cost: 2500,
    summary: 'A wonderful week exploring Tokyo\'s culture, food, and traditions',
    days: [
      {
        day_number: 1,
        date: '2024-06-01',
        location: 'Tokyo',
        estimated_cost: 150,
        activities: [
          { name: 'Arrive at Narita Airport', time: '2:00 PM' },
          { name: 'Check into hotel in Shibuya', time: '4:00 PM' },
          { name: 'Explore Shibuya Crossing', time: '6:00 PM' }
        ],
        meals: [{ name: 'Welcome dinner at local ramen shop', type: 'dinner' }],
        accommodation: { name: 'Shibuya Hotel' }
      },
      {
        day_number: 2,
        date: '2024-06-02',
        location: 'Tokyo',
        estimated_cost: 200,
        activities: [
          { name: 'Visit Senso-ji Temple', time: '9:00 AM' },
          { name: 'Explore Asakusa district', time: '11:00 AM' },
          { name: 'Tokyo Skytree visit', time: '2:00 PM' }
        ],
        meals: [
          { name: 'Traditional breakfast', type: 'breakfast' },
          { name: 'Street food lunch', type: 'lunch' },
          { name: 'Kaiseki dinner', type: 'dinner' }
        ]
      }
    ]
  });

  // Generate itinerary with user selections
  const generateMockItineraryWithSelections = () => {
    const baseItinerary = generateMockItinerary();
    
    // Update with user selections
    if (selectedFlight) {
      baseItinerary.flight = selectedFlight;
      baseItinerary.days[0].activities[0] = {
        name: `Arrive via ${selectedFlight.airline} ${selectedFlight.flight_number}`,
        time: selectedFlight.arrival_time
      };
    }
    
    if (selectedHotel) {
      baseItinerary.accommodation = selectedHotel;
      baseItinerary.days.forEach(day => {
        if (day.accommodation) {
          day.accommodation = { name: selectedHotel.name };
        }
      });
    }
    
    if (selectedActivities.length > 0) {
      // Add selected activities to the itinerary
      selectedActivities.forEach((activity, index) => {
        const dayIndex = index < baseItinerary.days.length ? index : 0;
        baseItinerary.days[dayIndex].activities.push({
          name: activity.name || activity.title,
          time: 'TBD',
          description: activity.description
        });
      });
    }
    
    return baseItinerary;
  };

  return (
    <div className="App min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-4 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="lg:hidden p-2 hover:bg-gray-100 rounded-lg"
            >
              {showSidebar ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
            <Plane className="w-8 h-8 text-primary-600" />
            <h1 className="text-2xl font-bold text-gray-800">AI Travel Planner</h1>
            {!backendAvailable && (
              <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                Demo Mode
              </span>
            )}
          </div>
          <button
            onClick={createNewSession}
            className="btn-primary text-sm flex items-center gap-2"
            data-testid="new-session-btn"
          >
            <MessageSquare className="w-4 h-4" />
            New Trip
          </button>
        </div>
      </header>

      <div className="flex max-w-7xl mx-auto">
        {/* Sidebar - Session History */}
        <aside
          className={`${
            showSidebar ? 'block' : 'hidden'
          } lg:block w-64 bg-white border-r border-gray-200 h-[calc(100vh-80px)] overflow-y-auto`}
        >
          <div className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <History className="w-5 h-5 text-gray-600" />
              <h2 className="font-semibold text-gray-800">Trip History</h2>
            </div>
            
            {/* Selection Summary in Sidebar */}
            {(selectedFlight || selectedHotel || selectedActivities.length > 0) && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <h3 className="text-sm font-semibold text-green-800 mb-2">Current Selections</h3>
                {selectedFlight && (
                  <div className="text-xs text-green-700 mb-1">✈️ Flight: {selectedFlight.airline}</div>
                )}
                {selectedHotel && (
                  <div className="text-xs text-green-700 mb-1">🏨 Hotel: {selectedHotel.name}</div>
                )}
                {selectedActivities.length > 0 && (
                  <div className="text-xs text-green-700">🎯 Activities: {selectedActivities.length}</div>
                )}
              </div>
            )}
            
            {sessions && sessions.length > 0 ? (
              <div className="space-y-2">
                {sessions.map((session) => (
                  <button
                    key={session.thread_id}
                    onClick={() => switchSession(session.thread_id)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      session.thread_id === threadId
                        ? 'bg-primary-100 text-primary-800 border border-primary-300'
                        : 'bg-gray-50 hover:bg-gray-100 text-gray-700'
                    }`}
                  >
                    <div className="font-medium text-sm truncate">{session.thread_id}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {new Date(session.last_active).toLocaleDateString()}
                    </div>
                    {session.has_itinerary && (
                      <div className="text-xs text-green-600 mt-1">✓ Has itinerary</div>
                    )}
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-sm text-gray-500 text-center py-8">
                No trips yet.<br />Start planning!
              </div>
            )}
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col h-[calc(100vh-80px)]">
          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 mx-4 mt-4 rounded-lg">
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Results Display Area */}
          <div className="flex-1 overflow-y-auto">
            {/* Chat Interface */}
            <ChatInterface
              messages={ensureArray(messages)}
              onSendMessage={sendMessage}
              isLoading={isLoading}
            />

            {/* Itinerary Display */}
            {currentItinerary && (
              <div className="px-4 py-6">
                <ItineraryCard itinerary={currentItinerary} />
              </div>
            )}

            {/* Tool Results Display */}
            <div className="px-4 pb-6">
              {toolResults.flights && (
                <FlightResults 
                  flights={ensureArray(toolResults.flights)} 
                  onFlightSelect={handleFlightSelection}
                  selectedFlight={selectedFlight}
                />
              )}
              {toolResults.hotels && (
                <HotelResults 
                  hotels={ensureArray(toolResults.hotels)} 
                  onHotelSelect={handleHotelSelection}
                  selectedHotel={selectedHotel}
                />
              )}
              {toolResults.activities && (
                <ActivityResults 
                  activities={ensureArray(toolResults.activities)} 
                  onActivitySelect={handleActivitySelection}
                  selectedActivities={selectedActivities}
                />
              )}
            </div>
          </div>

          {/* Suggestion Buttons */}
          <SuggestionButtons
            suggestions={ensureArray(suggestions)}
            onSelectSuggestion={handleSuggestionSelect}
            isLoading={isLoading}
          />
        </main>
      </div>

      {/* Footer Note */}
      <div className="bg-gray-100 border-t border-gray-300 px-4 py-3 text-center text-sm text-gray-600">
        <strong>🚧 Demo Version:</strong> 
        {backendAvailable 
          ? 'Using mock data for flights, hotels, and activities.'
          : 'Running in offline demo mode with sample data.'
        }
        <span className="font-medium text-primary-700"> Ready for production integration</span>
      </div>
    </div>
  );
}

export default App;