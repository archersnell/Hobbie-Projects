"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { isSupabaseConfigured, supabase } from "@/lib/supabase";
import type { Profile, Restaurant, RestaurantFormValues, RestaurantPhoto } from "@/lib/types";

const fallbackImage =
  "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=80";

const defaultForm: RestaurantFormValues = {
  reviewerName: "",
  name: "",
  cuisine: "",
  city: "",
  state: "",
  price_level: "$$",
  google_url: "",
  overall_rating: 4,
  food_rating: 4,
  service_rating: 4,
  atmosphere_rating: 4,
  ordered_items: "",
  notes: ""
};

type View = "dashboard" | "restaurants" | "add";

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [view, setView] = useState<View>("dashboard");
  const [form, setForm] = useState<RestaurantFormValues>(defaultForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [selected, setSelected] = useState<Restaurant | null>(null);
  const [query, setQuery] = useState("");
  const [cuisineFilter, setCuisineFilter] = useState("");
  const [priceFilter, setPriceFilter] = useState("");
  const [sortBy, setSortBy] = useState("overall_rating");
  const [mainPhoto, setMainPhoto] = useState<File | null>(null);
  const [extraPhotos, setExtraPhotos] = useState<FileList | null>(null);
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isSupabaseConfigured) {
      setLoading(false);
      setStatus("Supabase is not configured yet. Add your project URL and anon key to .env.local or Vercel.");
      return;
    }

    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });

    const { data: authListener } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
    });

    return () => authListener.subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (!session) return;
    bootstrapUser();
  }, [session]);

  async function bootstrapUser() {
    setStatus("Checking invite...");
    const { error: claimError } = await supabase.rpc("claim_profile", { requested_display_name: "" });

    if (claimError) {
      setStatus("This email is not on the invite list yet.");
      await supabase.auth.signOut();
      return;
    }

    const { data, error } = await supabase
      .from("profiles")
      .select("id,email,display_name,role")
      .eq("id", session?.user.id)
      .single();

    if (error || !data) {
      setStatus("Could not load your profile.");
      return;
    }

    setProfile(data);
    setForm((current) => ({
      ...current,
      reviewerName: data.display_name || data.email.split("@")[0] || ""
    }));
    setStatus("");
    await loadRestaurants();
  }

  async function loadRestaurants() {
    const { data, error } = await supabase
      .from("restaurants")
      .select(
        "*, created_profile:profiles!restaurants_created_by_fkey(display_name,email), updated_profile:profiles!restaurants_updated_by_fkey(display_name,email)"
      )
      .order("updated_at", { ascending: false });

    if (error) {
      setStatus(error.message);
      return;
    }

    const photoMap = await loadPhotoMap();
    const hydrated = await Promise.all(
      (data || []).map(async (restaurant) => hydrateRestaurant(restaurant as Restaurant, photoMap))
    );
    setRestaurants(hydrated);
  }

  async function loadPhotoMap() {
    const { data } = await supabase.from("photos").select("*").order("created_at", { ascending: true });
    return (data || []).reduce<Record<string, RestaurantPhoto[]>>((acc, photo) => {
      acc[photo.restaurant_id] ||= [];
      acc[photo.restaurant_id].push(photo as RestaurantPhoto);
      return acc;
    }, {});
  }

  async function hydrateRestaurant(restaurant: Restaurant, photoMap: Record<string, RestaurantPhoto[]>) {
    const signedMain = restaurant.main_photo_path ? await signedUrl(restaurant.main_photo_path) : null;
    const photos = await Promise.all(
      (photoMap[restaurant.id] || []).map(async (photo) => ({
        ...photo,
        signed_url: await signedUrl(photo.storage_path)
      }))
    );

    return {
      ...restaurant,
      signed_main_photo: signedMain,
      photos
    };
  }

  async function signedUrl(path: string) {
    const { data } = await supabase.storage.from("restaurant-photos").createSignedUrl(path, 60 * 60);
    return data?.signedUrl || null;
  }

  async function sendMagicLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("Sending login link...");
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: window.location.origin }
    });
    setStatus(error ? error.message : "Check your email for the login link.");
  }

  async function signOut() {
    await supabase.auth.signOut();
    setSession(null);
    setProfile(null);
    setRestaurants([]);
  }

  async function saveRestaurant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session || !profile) return;
    setStatus("Saving review...");

    const displayName = form.reviewerName.trim();
    if (displayName) {
      await supabase.rpc("claim_profile", { requested_display_name: displayName });
      setProfile((current) => (current ? { ...current, display_name: displayName } : current));
    }

    const existing = restaurants.find((restaurant) => restaurant.id === editingId);
    const restaurantId = editingId || crypto.randomUUID();
    const mainPhotoPath = mainPhoto
      ? await uploadPhoto(mainPhoto, restaurantId)
      : existing?.main_photo_path || null;

    const payload = {
      id: restaurantId,
      name: form.name.trim(),
      cuisine: form.cuisine.trim(),
      city: form.city.trim() || null,
      state: form.state.trim() || null,
      price_level: form.price_level,
      google_url: form.google_url.trim() || null,
      overall_rating: form.overall_rating,
      food_rating: form.food_rating,
      service_rating: form.service_rating,
      atmosphere_rating: form.atmosphere_rating,
      ordered_items: form.ordered_items.trim() || null,
      notes: form.notes.trim() || null,
      main_photo_path: mainPhotoPath,
      created_by: existing?.created_by || session.user.id,
      updated_by: session.user.id
    };

    const { error } = await supabase.from("restaurants").upsert(payload);
    if (error) {
      setStatus(error.message);
      return;
    }

    if (extraPhotos?.length) {
      const rows = await Promise.all(
        Array.from(extraPhotos).map(async (file) => ({
          restaurant_id: restaurantId,
          storage_path: await uploadPhoto(file, restaurantId),
          uploaded_by: session.user.id
        }))
      );
      const { error: photoError } = await supabase.from("photos").insert(rows);
      if (photoError) {
        setStatus(photoError.message);
        return;
      }
    }

    resetForm(displayName);
    setView("restaurants");
    setStatus("Saved.");
    await loadRestaurants();
  }

  async function uploadPhoto(file: File, restaurantId: string) {
    const cleanName = file.name.replace(/[^a-z0-9_.-]/gi, "-").toLowerCase();
    const path = `${restaurantId}/${crypto.randomUUID()}-${cleanName}`;
    const { error } = await supabase.storage.from("restaurant-photos").upload(path, file);
    if (error) throw error;
    return path;
  }

  function resetForm(reviewerName = form.reviewerName) {
    setForm({ ...defaultForm, reviewerName });
    setEditingId(null);
    setMainPhoto(null);
    setExtraPhotos(null);
  }

  function startEdit(restaurant: Restaurant) {
    setEditingId(restaurant.id);
    setSelected(null);
    setForm({
      reviewerName: profile?.display_name || profile?.email.split("@")[0] || "",
      name: restaurant.name,
      cuisine: restaurant.cuisine,
      city: restaurant.city || "",
      state: restaurant.state || "",
      price_level: restaurant.price_level,
      google_url: restaurant.google_url || "",
      overall_rating: restaurant.overall_rating,
      food_rating: restaurant.food_rating,
      service_rating: restaurant.service_rating,
      atmosphere_rating: restaurant.atmosphere_rating,
      ordered_items: restaurant.ordered_items || "",
      notes: restaurant.notes || ""
    });
    setView("add");
  }

  const cuisines = useMemo(
    () => [...new Set(restaurants.map((restaurant) => restaurant.cuisine).filter(Boolean))].sort(),
    [restaurants]
  );

  const filteredRestaurants = useMemo(() => {
    const search = query.trim().toLowerCase();
    return sortRestaurants(
      restaurants.filter((restaurant) => {
        const haystack = [
          restaurant.name,
          restaurant.cuisine,
          restaurant.city,
          restaurant.state,
          restaurant.notes,
          restaurant.ordered_items
        ]
          .join(" ")
          .toLowerCase();

        return (
          (!search || haystack.includes(search)) &&
          (!cuisineFilter || restaurant.cuisine === cuisineFilter) &&
          (!priceFilter || restaurant.price_level === priceFilter)
        );
      }),
      sortBy
    );
  }, [restaurants, query, cuisineFilter, priceFilter, sortBy]);

  const hallOfFame = useMemo(
    () => sortRestaurants(restaurants.filter((restaurant) => restaurant.overall_rating >= 4.5)).slice(0, 5),
    [restaurants]
  );

  const recentUpdates = useMemo(() => sortRestaurants(restaurants, "updated_at").slice(0, 5), [restaurants]);
  const cuisineWinners = useMemo(() => bestCuisineWinners(restaurants), [restaurants]);

  if (loading) {
    return <main className="login-screen"><div className="login-card">Loading AB Reviews...</div></main>;
  }

  if (!isSupabaseConfigured) {
    return (
      <main className="login-screen">
        <section className="login-card">
          <div>
            <p className="eyebrow">Setup needed</p>
            <h1>AB Reviews</h1>
          </div>
          <p>Add your Supabase project URL and anon key to start the hosted shared version.</p>
          <div className="status-message">{status}</div>
        </section>
      </main>
    );
  }

  if (!session || !profile) {
    return (
      <main className="login-screen">
        <form className="login-card" onSubmit={sendMagicLink}>
          <div>
            <p className="eyebrow">Invite-only</p>
            <h1>AB Reviews</h1>
          </div>
          <p>Use the email address Brooke or Archer invited. Supabase will send a magic login link.</p>
          <label>
            Email
            <input type="email" required value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          <button className="primary-action wide" type="submit">Send login link</button>
          {status ? <div className="status-message">{status}</div> : null}
        </form>
      </main>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Primary">
        <div className="brand">
          <div className="brand-mark">AB</div>
          <div>
            <p className="eyebrow">Invite-only taste log</p>
            <h1>AB Reviews</h1>
          </div>
        </div>

        <nav className="nav">
          {(["dashboard", "restaurants", "add"] as View[]).map((nextView) => (
            <button
              key={nextView}
              className={`nav-button ${view === nextView ? "active" : ""}`}
              onClick={() => {
                if (nextView === "add") resetForm();
                setView(nextView);
              }}
              type="button"
            >
              {nextView === "add" ? "Add Review" : titleCase(nextView)}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div>
            <p className="eyebrow">Signed in</p>
            <strong>{profile.display_name || profile.email}</strong>
          </div>
          <button className="ghost-action" type="button" onClick={signOut}>Sign out</button>
        </div>
      </aside>

      <main className="main">
        <section className="toolbar">
          <div>
            <p className="eyebrow">Brooke and Archer&apos;s Eats</p>
            <h2>{view === "add" ? "Add Review" : titleCase(view)}</h2>
          </div>
          <button className="primary-action" onClick={() => { resetForm(); setView("add"); }} type="button">
            Add restaurant
          </button>
        </section>

        {status ? <div className="status-message">{status}</div> : null}

        {view === "dashboard" ? (
          <Dashboard
            restaurants={restaurants}
            hallOfFame={hallOfFame}
            recentUpdates={recentUpdates}
            cuisineWinners={cuisineWinners}
            onSelect={setSelected}
            onEdit={startEdit}
          />
        ) : null}

        {view === "restaurants" ? (
          <section className="view">
            <div className="filters">
              <input
                placeholder="Search restaurants, dishes, notes..."
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
              <select value={cuisineFilter} onChange={(event) => setCuisineFilter(event.target.value)}>
                <option value="">All cuisines</option>
                {cuisines.map((cuisine) => <option key={cuisine} value={cuisine}>{cuisine}</option>)}
              </select>
              <select value={priceFilter} onChange={(event) => setPriceFilter(event.target.value)}>
                <option value="">All prices</option>
                {["$", "$$", "$$$", "$$$$"].map((price) => <option key={price} value={price}>{price}</option>)}
              </select>
              <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
                <option value="overall_rating">Overall</option>
                <option value="food_rating">Food</option>
                <option value="service_rating">Service</option>
                <option value="atmosphere_rating">Atmosphere</option>
                <option value="updated_at">Recently updated</option>
              </select>
            </div>
            <div className="restaurant-grid">
              {filteredRestaurants.length ? filteredRestaurants.map((restaurant) => (
                <RestaurantCard key={restaurant.id} restaurant={restaurant} onSelect={setSelected} onEdit={startEdit} />
              )) : <Empty message="No matches yet. Try clearing a filter or add the next great spot." />}
            </div>
          </section>
        ) : null}

        {view === "add" ? (
          <RestaurantForm
            editing={Boolean(editingId)}
            form={form}
            setForm={setForm}
            onSubmit={saveRestaurant}
            onReset={() => resetForm()}
            setMainPhoto={setMainPhoto}
            setExtraPhotos={setExtraPhotos}
          />
        ) : null}
      </main>

      {selected ? <DetailModal restaurant={selected} onClose={() => setSelected(null)} onEdit={startEdit} /> : null}
    </div>
  );
}

function Dashboard({
  restaurants,
  hallOfFame,
  recentUpdates,
  cuisineWinners,
  onSelect,
  onEdit
}: {
  restaurants: Restaurant[];
  hallOfFame: Restaurant[];
  recentUpdates: Restaurant[];
  cuisineWinners: [string, Restaurant][];
  onSelect: (restaurant: Restaurant) => void;
  onEdit: (restaurant: Restaurant) => void;
}) {
  return (
    <section className="view">
      <div className="hero-panel">
        <div>
          <p className="eyebrow">Hall of Fame</p>
          <h3>Best bites rise to the top.</h3>
        </div>
        <div className="hero-stat">
          <span>{restaurants.length}</span>
          <small>restaurants logged</small>
        </div>
      </div>

      <div className="grid two-col">
        <section className="panel">
          <div className="panel-header">
            <h3>Hall of Fame</h3>
            <span>4.5 stars and up</span>
          </div>
          <div className="stack">
            {hallOfFame.length ? hallOfFame.map((restaurant) => (
              <CompactCard key={restaurant.id} restaurant={restaurant} onSelect={onSelect} onEdit={onEdit} />
            )) : <Empty message="No Hall of Fame entries yet. A 4.5+ star restaurant will land here." />}
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <h3>Recent Updates</h3>
            <span>Latest activity</span>
          </div>
          <div className="stack">
            {recentUpdates.length ? recentUpdates.map((restaurant) => (
              <CompactCard key={restaurant.id} restaurant={restaurant} onSelect={onSelect} onEdit={onEdit} />
            )) : <Empty message="No restaurants logged yet." />}
          </div>
        </section>
      </div>

      <section className="panel">
        <div className="panel-header">
          <h3>Best By Cuisine</h3>
          <span>Top rated in each category</span>
        </div>
        <div className="award-grid">
          {cuisineWinners.length ? cuisineWinners.map(([cuisine, restaurant]) => (
            <article className="award-card" key={cuisine}>
              <div className="review-body">
                <p className="eyebrow">{cuisine}</p>
                <div className="review-title">
                  <h4>{restaurant.name}</h4>
                  <span className="stars">{ratingText(restaurant.overall_rating)}</span>
                </div>
                <div className="meta">{locationLine(restaurant)} · {restaurant.price_level}</div>
              </div>
            </article>
          )) : <Empty message="Cuisine awards will appear once you add restaurants." />}
        </div>
      </section>
    </section>
  );
}

function RestaurantForm({
  editing,
  form,
  setForm,
  onSubmit,
  onReset,
  setMainPhoto,
  setExtraPhotos
}: {
  editing: boolean;
  form: RestaurantFormValues;
  setForm: (form: RestaurantFormValues) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onReset: () => void;
  setMainPhoto: (file: File | null) => void;
  setExtraPhotos: (files: FileList | null) => void;
}) {
  const update = <K extends keyof RestaurantFormValues>(key: K, value: RestaurantFormValues[K]) => {
    setForm({ ...form, [key]: value });
  };

  return (
    <section className="view">
      <form className="form-panel" onSubmit={onSubmit}>
        <div className="form-title">
          <div>
            <p className="eyebrow">Restaurant record</p>
            <h3>{editing ? "Edit Restaurant" : "Add Restaurant"}</h3>
          </div>
          <button className="ghost-action" onClick={onReset} type="button">Clear</button>
        </div>

        <div className="form-grid">
          <label>
            Posting as
            <input value={form.reviewerName} onChange={(event) => update("reviewerName", event.target.value)} />
          </label>
          <label>
            Name
            <input required value={form.name} onChange={(event) => update("name", event.target.value)} />
          </label>
          <label>
            Cuisine
            <input required value={form.cuisine} onChange={(event) => update("cuisine", event.target.value)} />
          </label>
          <label>
            City
            <input value={form.city} onChange={(event) => update("city", event.target.value)} />
          </label>
          <label>
            State
            <input value={form.state} onChange={(event) => update("state", event.target.value)} />
          </label>
          <label>
            Price
            <select value={form.price_level} onChange={(event) => update("price_level", event.target.value as RestaurantFormValues["price_level"])}>
              {["$", "$$", "$$$", "$$$$"].map((price) => <option key={price} value={price}>{price}</option>)}
            </select>
          </label>
          <label>
            Google review / maps link
            <input type="url" value={form.google_url} onChange={(event) => update("google_url", event.target.value)} />
          </label>
        </div>

        <div className="ratings-grid">
          <Rating label="Overall" value={form.overall_rating} onChange={(value) => update("overall_rating", value)} />
          <Rating label="Food" value={form.food_rating} onChange={(value) => update("food_rating", value)} />
          <Rating label="Service" value={form.service_rating} onChange={(value) => update("service_rating", value)} />
          <Rating label="Atmosphere" value={form.atmosphere_rating} onChange={(value) => update("atmosphere_rating", value)} />
        </div>

        <label>
          Ordered items
          <textarea rows={3} value={form.ordered_items} onChange={(event) => update("ordered_items", event.target.value)} />
        </label>

        <label>
          Notes
          <textarea rows={5} value={form.notes} onChange={(event) => update("notes", event.target.value)} />
        </label>

        <div className="photo-fields">
          <label>
            Main photo
            <input accept="image/*" type="file" onChange={(event) => setMainPhoto(event.target.files?.[0] || null)} />
          </label>
          <label>
            Extra photos
            <input accept="image/*" multiple type="file" onChange={(event) => setExtraPhotos(event.target.files)} />
          </label>
        </div>

        <button className="primary-action wide" type="submit">Save review</button>
      </form>
    </section>
  );
}

function Rating({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return (
    <div className="rating-row">
      <span>{label}</span>
      <input min="0.5" max="5" step="0.5" type="range" value={value} onChange={(event) => onChange(Number(event.target.value))} />
      <strong>{value.toFixed(1)}</strong>
    </div>
  );
}

function CompactCard({ restaurant, onSelect, onEdit }: CardProps) {
  return (
    <article className="review-card">
      <div className="review-body">
        <div className="review-title">
          <div>
            <h4>{restaurant.name}</h4>
            <div className="meta">{locationLine(restaurant)} · {restaurant.cuisine}</div>
          </div>
          <div className="stars">{ratingText(restaurant.overall_rating)}</div>
        </div>
        <div className="card-actions">
          <button type="button" onClick={() => onSelect(restaurant)}>View</button>
          <button type="button" onClick={() => onEdit(restaurant)}>Edit</button>
        </div>
      </div>
    </article>
  );
}

type CardProps = {
  restaurant: Restaurant;
  onSelect: (restaurant: Restaurant) => void;
  onEdit: (restaurant: Restaurant) => void;
};

function RestaurantCard({ restaurant, onSelect, onEdit }: CardProps) {
  return (
    <article className="review-card">
      <div className="review-image">
        <img src={restaurant.signed_main_photo || fallbackImage} alt={restaurant.name} />
      </div>
      <div className="review-body">
        <div className="review-title">
          <div>
            <h4>{restaurant.name}</h4>
            <div className="meta">{locationLine(restaurant)} · {restaurant.cuisine} · {restaurant.price_level}</div>
          </div>
          <div className="stars">{ratingText(restaurant.overall_rating)}</div>
        </div>
        <div className="score-row">
          <span className="score-pill">Food {ratingText(restaurant.food_rating)}</span>
          <span className="score-pill">Service {ratingText(restaurant.service_rating)}</span>
          <span className="score-pill">Vibe {ratingText(restaurant.atmosphere_rating)}</span>
        </div>
        <div className="meta">Updated by {displayName(restaurant.updated_profile)} · {formatDate(restaurant.updated_at)}</div>
        <div className="card-actions">
          <button type="button" onClick={() => onSelect(restaurant)}>View</button>
          <button type="button" onClick={() => onEdit(restaurant)}>Edit</button>
          {restaurant.google_url ? <a href={restaurant.google_url} target="_blank" rel="noreferrer">Google</a> : null}
        </div>
      </div>
    </article>
  );
}

function DetailModal({ restaurant, onClose, onEdit }: { restaurant: Restaurant; onClose: () => void; onEdit: (restaurant: Restaurant) => void }) {
  const photos = [restaurant.signed_main_photo, ...(restaurant.photos || []).map((photo) => photo.signed_url)].filter(Boolean);

  return (
    <div className="detail-modal" role="dialog" aria-modal="true">
      <article className="detail-card">
        <button className="close-button" onClick={onClose} aria-label="Close detail" type="button">x</button>
        <div className="detail-hero" style={{ backgroundImage: `url('${restaurant.signed_main_photo || fallbackImage}')` }}>
          <div>
            <p className="eyebrow">{restaurant.cuisine} · {restaurant.price_level}</p>
            <h3>{restaurant.name}</h3>
            <div className="stars">{ratingText(restaurant.overall_rating)}</div>
          </div>
        </div>
        <div className="detail-content">
          <div className="detail-grid">
            <span className="score-pill">Food {ratingText(restaurant.food_rating)}</span>
            <span className="score-pill">Service {ratingText(restaurant.service_rating)}</span>
            <span className="score-pill">Atmosphere {ratingText(restaurant.atmosphere_rating)}</span>
            <span className="score-pill">{locationLine(restaurant)}</span>
          </div>
          <div className="meta">
            Added by {displayName(restaurant.created_profile)} · Updated by {displayName(restaurant.updated_profile)} on {formatDate(restaurant.updated_at)}
          </div>
          {restaurant.ordered_items ? <section><h4>Ordered</h4><p className="detail-note">{restaurant.ordered_items}</p></section> : null}
          {restaurant.notes ? <section><h4>Notes</h4><p className="detail-note">{restaurant.notes}</p></section> : null}
          {photos.length ? (
            <section>
              <h4>Photos</h4>
              <div className="photo-gallery">
                {photos.map((photo, index) => <img key={`${photo}-${index}`} src={photo || ""} alt={`${restaurant.name} photo`} />)}
              </div>
            </section>
          ) : null}
          <div className="card-actions">
            <button type="button" onClick={() => onEdit(restaurant)}>Edit</button>
            {restaurant.google_url ? <a href={restaurant.google_url} target="_blank" rel="noreferrer">Open Google link</a> : null}
          </div>
        </div>
      </article>
    </div>
  );
}

function Empty({ message }: { message: string }) {
  return <div className="empty-state">{message}</div>;
}

function sortRestaurants(restaurants: Restaurant[], sortKey = "overall_rating") {
  const copy = [...restaurants];
  if (sortKey === "updated_at") {
    return copy.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
  }

  return copy.sort((a, b) => {
    const key = sortKey as keyof Pick<Restaurant, "overall_rating" | "food_rating" | "service_rating" | "atmosphere_rating">;
    return (
      Number(b[key]) - Number(a[key]) ||
      b.food_rating - a.food_rating ||
      b.atmosphere_rating - a.atmosphere_rating ||
      b.service_rating - a.service_rating ||
      new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    );
  });
}

function bestCuisineWinners(restaurants: Restaurant[]) {
  const winners = new Map<string, Restaurant>();
  restaurants.forEach((restaurant) => {
    const current = winners.get(restaurant.cuisine);
    if (!current || sortRestaurants([current, restaurant])[0].id === restaurant.id) {
      winners.set(restaurant.cuisine, restaurant);
    }
  });
  return Array.from(winners.entries()).sort((a, b) => a[0].localeCompare(b[0]));
}

function ratingText(value: number) {
  return `${Number(value).toFixed(1)} ★`;
}

function titleCase(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function locationLine(restaurant: Restaurant) {
  return [restaurant.city, restaurant.state].filter(Boolean).join(", ") || "Location TBD";
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(value));
}

function displayName(profile?: Pick<Profile, "display_name" | "email"> | null) {
  return profile?.display_name || profile?.email?.split("@")[0] || "AB member";
}
