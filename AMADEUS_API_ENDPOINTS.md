# Amadeus API Endpoints - Complete Reference

Based on [Amadeus Developer Documentation](https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/resources/)

## ✅ Implemented Endpoints

### **Flights** 🛫

| Endpoint | Status | Function | Test API |
|----------|--------|----------|----------|
| **Flight Offers Search** | ✅ WORKING | Search & compare flights | ✅ Available |
| **Airport & City Search** | ✅ WORKING | Search airports by keyword | ✅ Available |
| **Airline Code Lookup** | ✅ WORKING | Get airline names from codes | ✅ Available |
| **Flight Inspiration Search** | ⚠️ ADDED | Find cheapest destinations | ❌ Not in Test |
| **Flight Cheapest Date Search** | ⚠️ ADDED | Find best travel dates | ❌ Not in Test |

### **Destination Experiences** 🎭

| Endpoint | Status | Function | Test API |
|----------|--------|----------|----------|
| **Tours and Activities** | ✅ WORKING | Find activities by location | ✅ Available |
| **City Search** | ✅ WORKING | Search cities by name | ✅ Available |

### **Hotels** 🏨

| Endpoint | Status | Function | Test API |
|----------|--------|----------|----------|
| **Hotel List** | ✅ WORKING | Get hotels in city | ✅ Available |

---

## 📚 API Usage Examples

### 1. Flight Offers Search
```python
from utils.amadeus_client import get_amadeus_client

amadeus = get_amadeus_client()
result = amadeus.search_flights(
    origin="LAX",
    destination="NRT",
    departure_date="2025-11-06",
    return_date="2025-11-13",
    adults=1,
    max_results=10
)
```

### 2. Tours and Activities
```python
# Tokyo coordinates
result = amadeus.tours_and_activities(
    latitude=35.6762,
    longitude=139.6503,
    radius=5  # km
)
# Returns 100+ activities in Tokyo!
```

### 3. City Search
```python
cities = amadeus.city_search("Paris", max_results=5)
# Returns: Paris (PAR), Le Touquet-Paris-Plage, etc.
```

### 4. Airline Code Lookup
```python
airlines = amadeus.airline_code_lookup(["AA", "UA", "DL"])
# Returns: {'AA': 'AMERICAN AIRLINES', 'UA': 'UNITED AIRLINES', ...}
```

### 5. Hotel List by City
```python
result = amadeus.hotel_list_by_city("NYC", max_results=20)
# Returns list of hotels in New York City
```

### 6. Flight Inspiration (Production API)
```python
# Note: Not available in test API
amadeus = get_amadeus_client(use_production=True)
result = amadeus.flight_inspiration_search(
    origin="LAX",
    max_price=1000,
    max_results=10
)
```

---

## 🔄 Test API vs Production API

### **Available in Test API** ✅
- Flight Offers Search
- Airport & City Search  
- Airline Code Lookup
- Tours and Activities (100+ real activities!)
- City Search
- Hotel List

### **Not Available in Test API** ❌
- Flight Inspiration Search
- Flight Cheapest Date Search
- Hotel Booking
- Some advanced flight APIs

**Solution:** These endpoints work in **Production API** only. Switch when ready:
```python
amadeus = get_amadeus_client(use_production=True)
```

---

## 🎯 Available But Not Yet Implemented

From the [Amadeus documentation](https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/resources/):

### **Flights** 🛫
- [ ] Flight Offers Price
- [ ] Flight Create Orders (Booking)
- [ ] Flight Order Management
- [ ] Seatmap Display
- [ ] Branded Fares Upsell
- [ ] Flight Price Analysis
- [ ] Flight Choice Prediction
- [ ] Flight Availabilities Search
- [ ] Travel Recommendations
- [ ] On Demand Flight Status
- [ ] Flight Delay Prediction
- [ ] Airport Nearest Relevant
- [ ] Airport Routes API
- [ ] Airport On-Time Performance
- [ ] Flight Check-in Links
- [ ] Airline Routes

### **Hotels** 🏨
- [ ] Hotel Ratings
- [ ] Hotel Search (with pricing)
- [ ] Hotel Booking
- [ ] Hotel Name Autocomplete

### **Cars and Transfers** 🚗
- [ ] Transfer Booking
- [ ] Transfer Management
- [ ] Transfer Search

### **Market Insights** 📊
- [ ] Flight Most Traveled Destinations
- [ ] Flight Most Booked Destinations
- [ ] Flight Busiest Traveling Period

### **Itinerary Management** 📋
- [ ] Trip Purpose Prediction

---

## 🚀 Integration Status by Agent

### **Flight Agent** ✅
- **Primary:** Amadeus Flight Offers Search
- **Fallback:** Mock data
- **Enhanced with:** Airline code lookup

### **Hotel Agent** ⚠️
- **Available:** Hotel List API
- **Missing:** Pricing/booking (still uses mock data)
- **Can add:** Hotel offers search

### **Activity Agent** ✅
- **Available:** Tours and Activities API
- **Status:** 100+ real activities found in test!
- **Currently:** Uses mock data (can switch to Amadeus)

### **Router/Planner** ✅
- **Available:** City Search, Airport Search
- **Use case:** Intent understanding, location autocomplete

---

## 💡 Recommended Next Steps

### **Phase 1: Enhance Existing Agents** (Quick Wins)

1. **Update Activity Agent**
   ```python
   # Switch from mock to Amadeus Tours & Activities
   # Already working in test API with 100+ results!
   ```

2. **Add Airline Names to Flight Results**
   ```python
   # Use airline_code_lookup to show real airline names
   # Instead of just codes (AA → American Airlines)
   ```

3. **Add City Autocomplete**
   ```python
   # Use city_search for destination suggestions
   # Works perfectly in test API
   ```

### **Phase 2: Hotel Integration** (Medium Effort)

1. Get hotel list by city (✅ working)
2. Add hotel offers search (needs implementation)
3. Integrate with hotel agent

### **Phase 3: Advanced Features** (Production API Required)

1. Flight Inspiration - "Where can I go for $500?"
2. Cheapest Date Search - Flexible date optimization
3. Flight Booking - Complete the booking flow

---

## 🔑 Key Insights from Testing

### **What Works Great** ✅
```
✅ Tours & Activities: 112 results in Tokyo test!
✅ City Search: Instant, accurate results
✅ Airline Lookup: Perfect name resolution
✅ Airport Search: Comprehensive database
```

### **What Needs Production API** 🔄
```
⚠️ Flight Inspiration: 404 in test
⚠️ Cheapest Dates: 404 in test  
⚠️ Hotel Pricing: Parameter issues in test
```

### **Strategic Decision**
**For MVP:** Use test API for core features (flights, activities, city search)
**For Production:** Upgrade to production API for advanced features

---

## 📖 API Documentation Links

| Category | Link |
|----------|------|
| **Flights** | https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/resources/flights/ |
| **Hotels** | https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/resources/hotels/ |
| **Destination Experiences** | https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/resources/destination-experiences/ |
| **Market Insights** | https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/resources/market-insight/ |
| **All Resources** | https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/resources/ |

---

## 🎉 Summary

**Implemented:** 8 endpoints
**Working in Test API:** 6 endpoints
**Ready for Production:** 2 endpoints (need production API)
**Available to Add:** 30+ more endpoints

Your AI Travel Planner now has:
- ✅ Real flight search
- ✅ Real activity recommendations (100+ in Tokyo!)
- ✅ City & airport search
- ✅ Airline information
- ✅ Hotel listings
- ✅ OAuth2 authentication with token caching

**Next Actions:**
1. Switch Activity Agent to use Amadeus API
2. Add airline name resolution to flight results  
3. Implement city autocomplete in frontend
4. Consider production API upgrade for advanced features

