# AB Reviews Product Spec

## Goal

Build an invite-only restaurant review website for friends and family. Members can log restaurants, rate them, upload photos, save what they ordered, link to Google reviews or Google Maps, and browse leaderboards.

## Audience

- Owner/admin
- Invited friends and family

## Access

- Invite-only
- All invited members can view, add, and edit restaurants
- Users should see who added and who last updated each record
- Production version should use email magic-link login

## Core Screens

### Dashboard

- Hall of Fame shown by default
- Overall leaderboard
- Best by cuisine
- Recent updates
- Optional low-score "Never Again" section

### Restaurant List

- Search by restaurant, dish, note, cuisine, or city
- Filter by cuisine
- Filter by price
- Sort by overall, food, service, atmosphere, or recently updated

### Restaurant Detail

- Main photo
- Extra photo gallery
- Name, cuisine, city, state, price
- Google review or Maps link
- Overall, food, service, and atmosphere ratings
- Ordered items
- Notes suitable for copying into a Google review
- Added by and updated by metadata

### Add/Edit Restaurant

- Mobile-friendly form
- Half-star rating controls
- Main photo upload
- Extra photo upload
- Notes and ordered items text fields
- Google review / Maps URL field

## Rating Rules

- 0.5 to 5 stars
- Half-star increments
- Overall rating is manual
- Subscores: food, service, atmosphere
- Subsequent visits may update notes/photos/orders, but do not create separate scores by default

## Leaderboard Rules

- Main ranking by overall rating
- Tie-breakers: food, atmosphere, service, recently updated
- Hall of Fame threshold: 4.5+ stars
- Optional Never Again threshold: 2 stars or below

## Production Data Model

### profiles

- id
- email
- display_name
- role
- created_at

### invites

- id
- email
- invited_by
- accepted_at
- created_at

### restaurants

- id
- name
- cuisine
- city
- state
- price_level
- google_url
- overall_rating
- food_rating
- service_rating
- atmosphere_rating
- ordered_items
- notes
- main_photo_url
- created_by
- updated_by
- created_at
- updated_at

### photos

- id
- restaurant_id
- image_url
- caption
- uploaded_by
- created_at

### visits

- id
- restaurant_id
- visit_date
- ordered_items
- visit_notes
- created_by
- created_at

## MVP Acceptance Criteria

- Invited users can access the site
- Members can add and edit restaurants
- Members can upload one main photo plus extras
- Members can add Google links, ordered items, and notes
- Members can rate overall, food, service, and atmosphere with half-stars
- Dashboard shows Hall of Fame and best-by-cuisine sections
- Restaurant list supports search, filters, and sorting
- App works well on mobile and desktop

## Implementation Status

The hosted app scaffold is implemented with Next.js and Supabase.

Completed:

- Magic-link login screen
- Invite-only profile claim through `claim_profile`
- Shared restaurants table
- Private photo bucket with signed URLs
- Add/edit review form
- Dashboard, Hall of Fame, recent updates, and best-by-cuisine views
- Restaurant list search, filters, and sorting

Not yet implemented:

- Admin invite-management screen inside the app
- Delete restaurant/photo controls
- Separate visit-history records
- CSV import/export
