# Supabase Setup Instructions

## 🎯 Quick Setup (2 minutes)

Your backend is **already connected** to Supabase! Now you just need to create the database tables.

### Step 1: Open Supabase SQL Editor

Go to: [https://supabase.com/dashboard/project/uecltvvipyjtnqxuxozf/sql/new](https://supabase.com/dashboard/project/uecltvvipyjtnqxuxozf/sql/new)

Or:
1. Go to https://supabase.com/dashboard
2. Select your project: `uecltvvipyjtnqxuxozf`
3. Click "SQL Editor" in the left sidebar
4. Click "New Query"

### Step 2: Copy the Schema SQL

The schema is located at: `/app/backend/schema.sql`

```bash
# View the schema:
cat /app/backend/schema.sql
```

### Step 3: Execute the SQL

1. Copy the entire content of `schema.sql`
2. Paste it into the SQL Editor
3. Click "Run" (or press Cmd/Ctrl + Enter)

You should see: "Success. No rows returned"

### Step 4: Verify Tables Created

Run this query in SQL Editor:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;
```

You should see:
- `itineraries`
- `plans`
- `tool_cache`
- `user_sessions`

### Step 5: Test the Integration

```bash
# Test database operations:
cd /app/backend
python init_database.py
```

## 🎉 That's It!

Your AI Travel Planner now has:
- ✅ Persistent session storage
- ✅ Itinerary saving
- ✅ API result caching
- ✅ Conversation history

##  Tables Created

### `user_sessions`
Stores conversation state and history
- thread_id: Unique session ID
- state: Full session state (JSONB)
- messages: Message history (JSONB)
- current_itinerary: Latest itinerary (JSONB)
- created_at, last_active: Timestamps

### `itineraries`
Stores generated travel plans
- destination, dates, duration
- days: Day-by-day itinerary (JSONB)
- total_estimated_cost
- summary and metadata

### `tool_cache`
Caches API results (flights, hotels, activities)
- tool_name, params_hash
- result (JSONB)
- expires_at: TTL for cache invalidation

### `plans`
Stores execution plans from planner agent
- steps: Plan steps (JSONB)
- status: pending/completed
- metadata

## 🔍 Useful Queries

### View all sessions:
```sql
SELECT thread_id, last_active, created_at
FROM user_sessions
ORDER BY last_active DESC
LIMIT 10;
```

### View all itineraries:
```sql
SELECT destination, duration_days, total_estimated_cost, created_at
FROM itineraries
ORDER BY created_at DESC;
```

### Check cache entries:
```sql
SELECT tool_name, COUNT(*) as count
FROM tool_cache
WHERE expires_at > NOW()
GROUP BY tool_name;
```

### Clean expired cache:
```sql
SELECT clean_expired_cache();
```

## 🐛 Troubleshooting

**Issue**: Tables not created
- **Solution**: Make sure you're logged into the correct Supabase project
- **Solution**: Check for SQL syntax errors in the query results

**Issue**: Permission denied
- **Solution**: Make sure you're using the service role key in `.env`

**Issue**: Backend says "In-Memory (Fallback)"
- **Solution**: Tables need to be created first (follow steps above)
- **Solution**: Check backend logs: `tail -f /var/log/supervisor/backend.err.log`

## 📚 Next Steps

Once tables are created:
1. Restart backend: `sudo supervisorctl restart backend`
2. Test a query via frontend at http://localhost:3000
3. Check Supabase dashboard to see data being stored
4. Monitor tables growing with real data!

---

**Supabase Project**: `uecltvvipyjtnqxuxozf`  
**Region**: Auto-detected  
**Database**: PostgreSQL 15
