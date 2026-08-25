# Deployment Guide

## Prerequisites

- Supabase account (free tier works fine)
- Static hosting (Vercel, Netlify, GitHub Pages, etc.)

## Setup

### 1. Supabase Database

Create a new Supabase project and run this SQL:

```sql
create table public.castle_go_matches (
  id uuid primary key default gen_random_uuid(),
  lobby_code text not null unique,
  state jsonb not null,
  updated_at timestamptz default timezone('utc', now())
);

create table public.castle_go_results (
  id uuid primary key default gen_random_uuid(),
  lobby_code text not null,
  black_name text,
  white_name text,
  winner_name text,
  black_kingdoms int,
  white_kingdoms int,
  finished_at timestamptz default timezone('utc', now())
);

-- Enable RLS
alter table public.castle_go_matches enable row level security;
create policy "anon can insert matches" on public.castle_go_matches for insert with check (true);
create policy "anon can select matches" on public.castle_go_matches for select using (true);
create policy "anon can update matches" on public.castle_go_matches for update using (true);

alter table public.castle_go_results enable row level security;
create policy "anon can insert results" on public.castle_go_results for insert with check (true);
create policy "anon can select results" on public.castle_go_results for select using (true);

-- Enable Realtime
alter publication supabase_realtime add table castle_go_matches;
alter publication supabase_realtime add table castle_go_results;
```

### 2. Update database.js

In `database.js`, replace the placeholders:

```javascript
const SUPABASE_URL = "https://YOUR_PROJECT_REF.supabase.co";
const SUPABASE_KEY = "YOUR_ANON_PUBLIC_KEY";
```

Get these from your Supabase project settings → API.

### 3. Deploy to Static Host

**Vercel (recommended)**
```bash
npm i -g vercel
vercel
```

**Netlify**
- Connect your GitHub repo to Netlify
- No build step needed (static site)
- Deploy

**GitHub Pages**
- Push to `gh-pages` branch or use GitHub Actions

## Environment Notes

- All three files (index.html, database.js, game-engine.py, ai-engine.py) must be in the same directory
- No build step or npm install required
- The game works entirely client-side (browser + Supabase)
- Supabase provides the database and real-time sync

## Troubleshooting

**"Game engine still loading"**
- Wait 2-3 seconds before clicking (PyScript takes time to initialize)
- Refresh the page if it persists

**AI doesn't move**
- Make sure ai-engine.py is in the same directory as index.html
- Check browser console (F12) for errors

**Moves not syncing**
- Verify Realtime is enabled in Supabase (Database → Replication)
- Check that castle_go_matches table is in the publication

**Table not found errors**
- Run the SQL setup queries in Supabase SQL Editor
- Verify table names (lowercase with underscores)
