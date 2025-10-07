import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';

const ChatInterface = ({ messages, onSendMessage, isLoading }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">✈️</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Plan Your Perfect Trip</h2>
            <p className="text-gray-600">Tell me where you'd like to go and I'll help you create an amazing itinerary!</p>
            <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
              <button
                onClick={() => onSendMessage('Plan a 7-day trip to Japan, budget-friendly, interested in culture and food')}
                className="p-4 bg-white rounded-lg border-2 border-gray-200 hover:border-primary-500 transition-colors text-left"
              >
                <div className="font-semibold text-gray-800">🇯🇵 Japan Adventure</div>
                <div className="text-sm text-gray-600">7 days, culture & food</div>
              </button>
              <button
                onClick={() => onSendMessage('Plan a 5-day trip to Paris for art lovers')}
                className="p-4 bg-white rounded-lg border-2 border-gray-200 hover:border-primary-500 transition-colors text-left"
              >
                <div className="font-semibold text-gray-800">🇫🇷 Paris Getaway</div>
                <div className="text-sm text-gray-600">5 days, art & culture</div>
              </button>
              <button
                onClick={() => onSendMessage('Find flights from San Francisco to Tokyo for June 1-8')}
                className="p-4 bg-white rounded-lg border-2 border-gray-200 hover:border-primary-500 transition-colors text-left"
              >
                <div className="font-semibold text-gray-800">✈️ Flight Search</div>
                <div className="text-sm text-gray-600">Find the best flights</div>
              </button>
              <button
                onClick={() => onSendMessage('Show me hotel options in Barcelona')}
                className="p-4 bg-white rounded-lg border-2 border-gray-200 hover:border-primary-500 transition-colors text-left"
              >
                <div className="font-semibold text-gray-800">🏨 Hotel Search</div>
                <div className="text-sm text-gray-600">Find great accommodations</div>
              </button>
            </div>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`message flex ${
                msg.type === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-3xl rounded-2xl px-6 py-4 ${
                  msg.type === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-800'
                }`}
              >
                {msg.type === 'ai' && (
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-white font-bold">
                      AI
                    </div>
                    <span className="text-sm font-semibold text-gray-700">Travel Assistant</span>
                  </div>
                )}
                <div className="whitespace-pre-wrap">{msg.content}</div>
                {msg.timestamp && (
                  <div className="text-xs opacity-70 mt-2">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="message flex justify-start">
            <div className="max-w-3xl rounded-2xl px-6 py-4 bg-white border border-gray-200">
              <div className="flex items-center gap-3">
                <Loader2 className="w-5 h-5 animate-spin text-primary-600" />
                <span className="text-gray-600">Planning your trip...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white px-4 py-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me to plan a trip, search flights, find hotels..."
              className="input-field flex-1"
              disabled={isLoading}
              data-testid="chat-input"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="btn-primary flex items-center gap-2 px-6"
              data-testid="send-message-btn"
            >
              <Send className="w-5 h-5" />
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;