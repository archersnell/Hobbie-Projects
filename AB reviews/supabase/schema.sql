create extension if not exists pgcrypto;

create type public.ab_role as enum ('admin', 'member');
create type public.price_level as enum ('$', '$$', '$$$', '$$$$');

create table public.invites (
  email text primary key check (position('@' in email) > 1),
  role public.ab_role not null default 'member',
  invited_by uuid references auth.users(id),
  accepted_at timestamptz,
  created_at timestamptz not null default now()
);

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null unique,
  display_name text,
  role public.ab_role not null default 'member',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.restaurants (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  cuisine text not null,
  city text,
  state text,
  price_level public.price_level not null default '$$',
  google_url text,
  overall_rating numeric(2, 1) not null check (overall_rating between 0.5 and 5 and overall_rating * 2 = floor(overall_rating * 2)),
  food_rating numeric(2, 1) not null check (food_rating between 0.5 and 5 and food_rating * 2 = floor(food_rating * 2)),
  service_rating numeric(2, 1) not null check (service_rating between 0.5 and 5 and service_rating * 2 = floor(service_rating * 2)),
  atmosphere_rating numeric(2, 1) not null check (atmosphere_rating between 0.5 and 5 and atmosphere_rating * 2 = floor(atmosphere_rating * 2)),
  ordered_items text,
  notes text,
  main_photo_path text,
  created_by uuid not null constraint restaurants_created_by_fkey references public.profiles(id),
  updated_by uuid not null constraint restaurants_updated_by_fkey references public.profiles(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.photos (
  id uuid primary key default gen_random_uuid(),
  restaurant_id uuid not null references public.restaurants(id) on delete cascade,
  storage_path text not null unique,
  caption text,
  uploaded_by uuid not null references public.profiles(id),
  created_at timestamptz not null default now()
);

create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger profiles_touch_updated_at
before update on public.profiles
for each row execute function public.touch_updated_at();

create trigger restaurants_touch_updated_at
before update on public.restaurants
for each row execute function public.touch_updated_at();

create or replace function public.is_ab_member()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.profiles
    where id = auth.uid()
  );
$$;

create or replace function public.is_ab_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.profiles
    where id = auth.uid()
      and role = 'admin'
  );
$$;

create or replace function public.claim_profile(requested_display_name text default '')
returns public.profiles
language plpgsql
security definer
set search_path = public
as $$
declare
  user_email text := lower(auth.jwt() ->> 'email');
  invite_row public.invites%rowtype;
  profile_row public.profiles%rowtype;
begin
  if auth.uid() is null or user_email is null then
    raise exception 'Not authenticated';
  end if;

  select *
  into invite_row
  from public.invites
  where lower(email) = user_email;

  if not found then
    raise exception 'Email is not invited';
  end if;

  insert into public.profiles (id, email, display_name, role)
  values (
    auth.uid(),
    user_email,
    nullif(trim(requested_display_name), ''),
    invite_row.role
  )
  on conflict (id) do update
  set
    display_name = coalesce(nullif(trim(excluded.display_name), ''), profiles.display_name),
    role = excluded.role,
    updated_at = now()
  returning * into profile_row;

  update public.invites
  set accepted_at = coalesce(accepted_at, now())
  where lower(email) = user_email;

  return profile_row;
end;
$$;

alter table public.invites enable row level security;
alter table public.profiles enable row level security;
alter table public.restaurants enable row level security;
alter table public.photos enable row level security;

create policy "admins can manage invites"
on public.invites
for all
using (public.is_ab_admin())
with check (public.is_ab_admin());

create policy "members can read profiles"
on public.profiles
for select
using (public.is_ab_member());

create policy "members can update own profile"
on public.profiles
for update
using (id = auth.uid())
with check (id = auth.uid());

create policy "members can read restaurants"
on public.restaurants
for select
using (public.is_ab_member());

create policy "members can add restaurants"
on public.restaurants
for insert
with check (public.is_ab_member() and created_by = auth.uid() and updated_by = auth.uid());

create policy "members can edit restaurants"
on public.restaurants
for update
using (public.is_ab_member())
with check (public.is_ab_member() and updated_by = auth.uid());

create policy "admins can delete restaurants"
on public.restaurants
for delete
using (public.is_ab_admin());

create policy "members can read photos"
on public.photos
for select
using (public.is_ab_member());

create policy "members can add photos"
on public.photos
for insert
with check (public.is_ab_member() and uploaded_by = auth.uid());

create policy "admins can delete photos"
on public.photos
for delete
using (public.is_ab_admin());

insert into storage.buckets (id, name, public)
values ('restaurant-photos', 'restaurant-photos', false)
on conflict (id) do nothing;

create policy "members can read restaurant photo objects"
on storage.objects
for select
using (bucket_id = 'restaurant-photos' and public.is_ab_member());

create policy "members can upload restaurant photo objects"
on storage.objects
for insert
with check (bucket_id = 'restaurant-photos' and public.is_ab_member());

create policy "admins can delete restaurant photo objects"
on storage.objects
for delete
using (bucket_id = 'restaurant-photos' and public.is_ab_admin());

-- Add at least your first invite after running the schema:
-- insert into public.invites (email, role) values ('your-email@example.com', 'admin');
