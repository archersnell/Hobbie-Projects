# AB Reviews

AB Reviews is Brooke and Archer's invite-only restaurant tracker for friends and family. It is now scaffolded as a hosted Next.js app with Supabase auth, database records, and private photo storage.

The original zero-dependency prototype files are still in this folder as `index.html`, `styles.css`, and `app.js`. The hosted version uses the `app/`, `lib/`, and `supabase/` folders.

## Production Stack

- Next.js app router
- Supabase magic-link auth
- Supabase Postgres database
- Supabase private storage bucket for restaurant photos
- Vercel hosting

## Local Setup

Install Node.js from https://nodejs.org if `npm` is not available on your machine.

```bash
npm install
cp .env.example .env.local
npm run dev
```

Then open http://localhost:3000.

## Supabase Setup

1. Create a free Supabase project.
2. Open the SQL editor.
3. Run `supabase/schema.sql`.
4. Add your first admin invite:

```sql
insert into public.invites (email, role)
values ('your-email@example.com', 'admin');
```

5. Go to Project Settings > API.
6. Copy the project URL and anon public key.
7. Put them in `.env.local`:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

8. In Supabase Auth URL settings, add your local and Vercel URLs as allowed redirect URLs:

```text
http://localhost:3000
https://your-vercel-app.vercel.app
```

## Inviting Friends And Family

For now, add invited emails in Supabase SQL:

```sql
insert into public.invites (email, role)
values
  ('friend@example.com', 'member'),
  ('family@example.com', 'member');
```

Only invited emails can claim a profile and use the app.

## Vercel Deploy

1. Push this folder to GitHub.
2. Import the GitHub repo into Vercel.
3. Add these environment variables in Vercel:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
4. Deploy.
5. Add the Vercel URL to Supabase Auth redirect URLs.

## What The Hosted App Supports

- Invite-only login by email magic link
- Shared restaurant records for all invited members
- Add and edit restaurants
- Rate overall, food, service, and atmosphere in half-star steps
- Track cuisine, city, state, price, ordered items, notes, and Google link
- Upload one main photo plus extra photos
- Private Supabase photo storage with signed display URLs
- Hall of Fame dashboard for restaurants rated 4.5+
- Best-by-cuisine awards
- Search, filter, and sort restaurants
- Added by / updated by member tracking
