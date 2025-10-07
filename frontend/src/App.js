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
// TODO: Replace with environment variable for production deployment
const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  // State management
  const [messages, setMessages] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [currentItinerary, setCurrentItinerary] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState('default');
  const [sessions, setSessions] = useState([]);
  const [showSidebar, setShowSidebar] = useState(false);
  const [error, setError] = useState(null);

  // Mock data for tool results (flights, hotels, activities)
  // These are extracted from AI responses
  const [toolResults, setToolResults] = useState({
    flights: null,
    hotels: null,
    activities: null
  });

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // API call to send chat message
  // TODO: Backend Integration Point
  // - This currently calls /api/chat endpoint
  // - In production, add authentication headers
  // - Handle rate limiting and retries
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

      // Call backend API
      const response = await axios.post(`${API_URL}/api/chat`, {
        query,
        thread_id: threadId,
        user_preferences: {} // TODO: Add user preferences from settings
      });

      // Add AI response to messages
      const aiMessage = {
        type: 'ai',
        content: response.data.response,
        timestamp: response.data.timestamp
      };
      setMessages(prev => [...prev, aiMessage]);

      // Update suggestions
      setSuggestions(response.data.suggestions || []);

      // Update current itinerary if available
      if (response.data.current_itinerary) {
        setCurrentItinerary(response.data.current_itinerary);
      }

      // Extract tool results from response
      // TODO: Backend should return structured tool_results in response
      extractToolResults(response.data);

    } catch (err) {
      console.error('Error sending message:', err);
      setError(err.response?.data?.detail || 'Failed to send message. Please try again.');
      
      // Add error message to chat
      const errorMessage = {
        type: 'ai',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // API call to handle suggestion selection
  // TODO: Backend Integration Point
  // - Calls /api/suggestion endpoint
  // - Track analytics on suggestion usage
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

      // Call backend API
      const response = await axios.post(`${API_URL}/api/suggestion`, {
        token,
        thread_id: threadId
      });

      // Add AI response
      const aiMessage = {
        type: 'ai',
        content: response.data.response,
        timestamp: response.data.timestamp
      };
      setMessages(prev => [...prev, aiMessage]);

      // Update suggestions
      setSuggestions(response.data.suggestions || []);

      // Update current itinerary
      if (response.data.current_itinerary) {
        setCurrentItinerary(response.data.current_itinerary);
      }

      // Extract tool results
      extractToolResults(response.data);

    } catch (err) {
      console.error('Error handling suggestion:', err);
      setError(err.response?.data?.detail || 'Failed to process suggestion. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Extract mock tool results from response
  // TODO: Backend should return structured data in tool_results field
  // For now, we'll use mock data when certain keywords are detected
  const extractToolResults = (data) => {
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

  // Load all sessions
  // TODO: Backend Integration Point
  // - Query from Supabase user_sessions table
  // - Filter by authenticated user
  const loadSessions = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/sessions`);
      setSessions(response.data || []);
    } catch (err) {
      console.error('Error loading sessions:', err);
    }
  };

  // Switch to a different session
  const switchSession = (newThreadId) => {
    setThreadId(newThreadId);
    setMessages([]);
    setSuggestions([]);
    setCurrentItinerary(null);
    setToolResults({ flights: null, hotels: null, activities: null });
    setShowSidebar(false);
    
    // TODO: Load session history from backend
    // const session = await axios.get(`${API_URL}/api/session/${newThreadId}`);
  };

  // Create new session
  const createNewSession = () => {
    const newThreadId = `session_${Date.now()}`;
    switchSession(newThreadId);
  };

  // Mock data generators
  // TODO: Remove these when real API integrations are complete
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
            
            {sessions.length > 0 ? (
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
              messages={messages}
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
              {toolResults.flights && <FlightResults flights={toolResults.flights} />}
              {toolResults.hotels && <HotelResults hotels={toolResults.hotels} />}
              {toolResults.activities && <ActivityResults activities={toolResults.activities} />}
            </div>
          </div>

          {/* Suggestion Buttons */}
          <SuggestionButtons
            suggestions={suggestions}
            onSelectSuggestion={handleSuggestionSelect}
            isLoading={isLoading}
          />
        </main>
      </div>

      {/* Footer Note */}
      <div className="bg-gray-100 border-t border-gray-300 px-4 py-3 text-center text-sm text-gray-600">
        <strong>🚧 MVP Version:</strong> Using mock data for flights, hotels, and activities. 
        <span className="font-medium text-primary-700"> Phase 2: Supabase integration</span>
      </div>
    </div>
  );
}

export default App;
