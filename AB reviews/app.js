const STORAGE_KEY = "ab-reviews-restaurants";
const MEMBER_KEY = "ab-reviews-member";

const fallbackImage =
  "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=80";

const state = {
  restaurants: [],
  view: "dashboard",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const elements = {
  viewTitle: $("#viewTitle"),
  restaurantCount: $("#restaurantCount"),
  hallOfFame: $("#hallOfFame"),
  recentUpdates: $("#recentUpdates"),
  bestByCuisine: $("#bestByCuisine"),
  restaurantList: $("#restaurantList"),
  searchInput: $("#searchInput"),
  cuisineFilter: $("#cuisineFilter"),
  priceFilter: $("#priceFilter"),
  sortSelect: $("#sortSelect"),
  form: $("#restaurantForm"),
  formTitle: $("#formTitle"),
  restaurantId: $("#restaurantId"),
  reviewerName: $("#reviewerName"),
  detailDialog: $("#detailDialog"),
  detailContent: $("#detailContent"),
};

function loadRestaurants() {
  const saved = localStorage.getItem(STORAGE_KEY);
  state.restaurants = saved ? JSON.parse(saved) : seedRestaurants();
  saveRestaurants();
}

function saveRestaurants() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state.restaurants));
}

function seedRestaurants() {
  const now = new Date().toISOString();
  return [
    {
      id: crypto.randomUUID(),
      name: "Sample: The Corner Table",
      cuisine: "American",
      city: "Orlando",
      state: "FL",
      price: "$$",
      googleUrl: "https://www.google.com/maps",
      overall: 4.5,
      food: 4.5,
      service: 4,
      atmosphere: 4.5,
      orderedItems: "Burger, fries, wedge salad",
      notes: "A strong neighborhood pick. Great for an easy family dinner and worth a return visit.",
      mainPhoto: "",
      extraPhotos: [],
      createdBy: "AB Reviews",
      updatedBy: "AB Reviews",
      createdAt: now,
      updatedAt: now,
    },
    {
      id: crypto.randomUUID(),
      name: "Sample: Noodle House",
      cuisine: "Ramen",
      city: "Winter Park",
      state: "FL",
      price: "$$",
      googleUrl: "https://www.google.com/maps",
      overall: 4,
      food: 4.5,
      service: 3.5,
      atmosphere: 4,
      orderedItems: "Tonkotsu ramen, pork buns",
      notes: "Food carried the night. Service was fine, but the broth deserves respect.",
      mainPhoto: "",
      extraPhotos: [],
      createdBy: "AB Reviews",
      updatedBy: "AB Reviews",
      createdAt: now,
      updatedAt: now,
    },
  ];
}

function currentMember() {
  return elements.reviewerName.value.trim() || "Friend or family";
}

function switchView(view) {
  state.view = view;
  $$(".view").forEach((node) => node.classList.remove("active-view"));
  $(`#${view}View`).classList.add("active-view");
  $$(".nav-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  elements.viewTitle.textContent = view === "add" ? "Add Review" : titleCase(view);
  if (view === "add" && !elements.restaurantId.value) {
    elements.formTitle.textContent = "Add Restaurant";
  }
}

function titleCase(value) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function ratingText(value) {
  return `${Number(value).toFixed(1)} ★`;
}

function cardImage(restaurant) {
  return restaurant.mainPhoto || fallbackImage;
}

function sortRestaurants(restaurants, sortBy = "overall") {
  const scoreSort = (a, b, key) => b[key] - a[key] || leaderboardTieBreak(a, b);
  const copy = [...restaurants];
  if (sortBy === "updated") {
    return copy.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
  }
  return copy.sort((a, b) => scoreSort(a, b, sortBy));
}

function leaderboardTieBreak(a, b) {
  return (
    b.food - a.food ||
    b.atmosphere - a.atmosphere ||
    b.service - a.service ||
    new Date(b.updatedAt) - new Date(a.updatedAt)
  );
}

function render() {
  updateCuisineFilter();
  renderDashboard();
  renderRestaurantList();
}

function renderDashboard() {
  elements.restaurantCount.textContent = state.restaurants.length;

  const hall = sortRestaurants(state.restaurants.filter((restaurant) => restaurant.overall >= 4.5));
  elements.hallOfFame.innerHTML = hall.length
    ? hall.slice(0, 5).map(renderCompactCard).join("")
    : renderEmpty("No Hall of Fame entries yet. A 4.5+ star restaurant will land here.");

  const recent = sortRestaurants(state.restaurants, "updated").slice(0, 5);
  elements.recentUpdates.innerHTML = recent.length
    ? recent.map(renderCompactCard).join("")
    : renderEmpty("No restaurants logged yet.");

  const bestByCuisine = bestCuisineWinners();
  elements.bestByCuisine.innerHTML = bestByCuisine.length
    ? bestByCuisine.map(renderAwardCard).join("")
    : renderEmpty("Cuisine awards will appear once you add restaurants.");
}

function bestCuisineWinners() {
  const winners = new Map();
  state.restaurants.forEach((restaurant) => {
    const key = restaurant.cuisine || "Other";
    const current = winners.get(key);
    if (!current || sortRestaurants([current, restaurant])[0].id === restaurant.id) {
      winners.set(key, restaurant);
    }
  });
  return Array.from(winners.entries()).sort((a, b) => a[0].localeCompare(b[0]));
}

function renderRestaurantList() {
  const query = elements.searchInput.value.trim().toLowerCase();
  const cuisine = elements.cuisineFilter.value;
  const price = elements.priceFilter.value;
  const sortBy = elements.sortSelect.value;

  const filtered = state.restaurants.filter((restaurant) => {
    const text = [
      restaurant.name,
      restaurant.cuisine,
      restaurant.city,
      restaurant.state,
      restaurant.notes,
      restaurant.orderedItems,
    ]
      .join(" ")
      .toLowerCase();

    return (
      (!query || text.includes(query)) &&
      (!cuisine || restaurant.cuisine === cuisine) &&
      (!price || restaurant.price === price)
    );
  });

  elements.restaurantList.innerHTML = filtered.length
    ? sortRestaurants(filtered, sortBy).map(renderRestaurantCard).join("")
    : renderEmpty("No matches yet. Try clearing a filter or add the next great spot.");
}

function renderCompactCard(restaurant) {
  return `
    <article class="review-card">
      <div class="review-body">
        <div class="review-title">
          <div>
            <h4>${escapeHtml(restaurant.name)}</h4>
            <div class="meta">${escapeHtml(locationLine(restaurant))} · ${escapeHtml(restaurant.cuisine)}</div>
          </div>
          <div class="stars">${ratingText(restaurant.overall)}</div>
        </div>
        <div class="card-actions">
          <button type="button" data-detail="${restaurant.id}">View</button>
          <button type="button" data-edit="${restaurant.id}">Edit</button>
        </div>
      </div>
    </article>
  `;
}

function renderAwardCard([cuisine, restaurant]) {
  return `
    <article class="award-card">
      <div class="review-body">
        <p class="eyebrow">${escapeHtml(cuisine)}</p>
        <div class="review-title">
          <h4>${escapeHtml(restaurant.name)}</h4>
          <span class="stars">${ratingText(restaurant.overall)}</span>
        </div>
        <div class="meta">${escapeHtml(locationLine(restaurant))} · ${escapeHtml(restaurant.price)}</div>
      </div>
    </article>
  `;
}

function renderRestaurantCard(restaurant) {
  return `
    <article class="review-card">
      <div class="review-image"><img src="${cardImage(restaurant)}" alt="${escapeHtml(restaurant.name)}" /></div>
      <div class="review-body">
        <div class="review-title">
          <div>
            <h4>${escapeHtml(restaurant.name)}</h4>
            <div class="meta">${escapeHtml(locationLine(restaurant))} · ${escapeHtml(restaurant.cuisine)} · ${escapeHtml(restaurant.price)}</div>
          </div>
          <div class="stars">${ratingText(restaurant.overall)}</div>
        </div>
        <div class="score-row">
          <span class="score-pill">Food ${ratingText(restaurant.food)}</span>
          <span class="score-pill">Service ${ratingText(restaurant.service)}</span>
          <span class="score-pill">Vibe ${ratingText(restaurant.atmosphere)}</span>
        </div>
        <div class="meta">Updated by ${escapeHtml(restaurant.updatedBy)} · ${formatDate(restaurant.updatedAt)}</div>
        <div class="card-actions">
          <button type="button" data-detail="${restaurant.id}">View</button>
          <button type="button" data-edit="${restaurant.id}">Edit</button>
          ${restaurant.googleUrl ? `<a href="${escapeAttribute(restaurant.googleUrl)}" target="_blank" rel="noreferrer">Google</a>` : ""}
        </div>
      </div>
    </article>
  `;
}

function renderEmpty(message) {
  return `<div class="empty-state">${escapeHtml(message)}</div>`;
}

function locationLine(restaurant) {
  return [restaurant.city, restaurant.state].filter(Boolean).join(", ") || "Location TBD";
}

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(
    new Date(value),
  );
}

function updateCuisineFilter() {
  const current = elements.cuisineFilter.value;
  const cuisines = [...new Set(state.restaurants.map((restaurant) => restaurant.cuisine).filter(Boolean))].sort();
  elements.cuisineFilter.innerHTML = `<option value="">All cuisines</option>${cuisines
    .map((cuisine) => `<option value="${escapeAttribute(cuisine)}">${escapeHtml(cuisine)}</option>`)
    .join("")}`;
  elements.cuisineFilter.value = cuisines.includes(current) ? current : "";
}

function bindEvents() {
  $$(".nav-button").forEach((button) => {
    button.addEventListener("click", () => switchView(button.dataset.view));
  });

  $("#quickAdd").addEventListener("click", () => {
    resetForm();
    switchView("add");
  });

  $("#resetForm").addEventListener("click", resetForm);
  $("#closeDetail").addEventListener("click", () => elements.detailDialog.close());

  [elements.searchInput, elements.cuisineFilter, elements.priceFilter, elements.sortSelect].forEach((input) => {
    input.addEventListener("input", renderRestaurantList);
  });

  ["overall", "food", "service", "atmosphere"].forEach((id) => {
    const input = $(`#${id}`);
    const output = $(`#${id}Value`);
    input.addEventListener("input", () => {
      output.textContent = Number(input.value).toFixed(1);
    });
  });

  document.addEventListener("click", (event) => {
    const detailButton = event.target.closest("[data-detail]");
    const editButton = event.target.closest("[data-edit]");
    if (detailButton) showDetail(detailButton.dataset.detail);
    if (editButton) {
      if (elements.detailDialog.open) elements.detailDialog.close();
      editRestaurant(editButton.dataset.edit);
    }
  });

  elements.reviewerName.addEventListener("input", () => {
    localStorage.setItem(MEMBER_KEY, elements.reviewerName.value);
  });

  elements.form.addEventListener("submit", handleSubmit);
}

async function handleSubmit(event) {
  event.preventDefault();
  const id = elements.restaurantId.value || crypto.randomUUID();
  const existing = state.restaurants.find((restaurant) => restaurant.id === id);
  const now = new Date().toISOString();
  const mainPhoto = await readSinglePhoto($("#mainPhoto").files[0]);
  const extraPhotos = await readPhotoList($("#extraPhotos").files);

  const restaurant = {
    id,
    name: $("#name").value.trim(),
    cuisine: $("#cuisine").value.trim(),
    city: $("#city").value.trim(),
    state: $("#state").value.trim(),
    price: $("#price").value,
    googleUrl: $("#googleUrl").value.trim(),
    overall: Number($("#overall").value),
    food: Number($("#food").value),
    service: Number($("#service").value),
    atmosphere: Number($("#atmosphere").value),
    orderedItems: $("#orderedItems").value.trim(),
    notes: $("#notes").value.trim(),
    mainPhoto: mainPhoto || existing?.mainPhoto || "",
    extraPhotos: [...(existing?.extraPhotos || []), ...extraPhotos],
    createdBy: existing?.createdBy || currentMember(),
    updatedBy: currentMember(),
    createdAt: existing?.createdAt || now,
    updatedAt: now,
  };

  if (!restaurant.name || !restaurant.cuisine) return;

  state.restaurants = existing
    ? state.restaurants.map((item) => (item.id === id ? restaurant : item))
    : [restaurant, ...state.restaurants];

  saveRestaurants();
  resetForm();
  switchView("restaurants");
  render();
}

function editRestaurant(id) {
  const restaurant = state.restaurants.find((item) => item.id === id);
  if (!restaurant) return;
  elements.restaurantId.value = restaurant.id;
  elements.formTitle.textContent = `Edit ${restaurant.name}`;
  $("#name").value = restaurant.name;
  $("#cuisine").value = restaurant.cuisine;
  $("#city").value = restaurant.city;
  $("#state").value = restaurant.state;
  $("#price").value = restaurant.price;
  $("#googleUrl").value = restaurant.googleUrl;
  $("#orderedItems").value = restaurant.orderedItems;
  $("#notes").value = restaurant.notes;
  ["overall", "food", "service", "atmosphere"].forEach((id) => {
    $(`#${id}`).value = restaurant[id];
    $(`#${id}Value`).textContent = Number(restaurant[id]).toFixed(1);
  });
  switchView("add");
}

function resetForm() {
  const reviewerName = elements.reviewerName.value;
  elements.form.reset();
  elements.reviewerName.value = reviewerName;
  elements.restaurantId.value = "";
  elements.formTitle.textContent = "Add Restaurant";
  ["overall", "food", "service", "atmosphere"].forEach((id) => {
    $(`#${id}`).value = 4;
    $(`#${id}Value`).textContent = "4.0";
  });
}

function showDetail(id) {
  const restaurant = state.restaurants.find((item) => item.id === id);
  if (!restaurant) return;
  const photos = [restaurant.mainPhoto, ...(restaurant.extraPhotos || [])].filter(Boolean);
  elements.detailContent.innerHTML = `
    <div class="detail-hero" style="background-image: url('${cardImage(restaurant)}')">
      <div>
        <p class="eyebrow">${escapeHtml(restaurant.cuisine)} · ${escapeHtml(restaurant.price)}</p>
        <h3>${escapeHtml(restaurant.name)}</h3>
        <div class="stars">${ratingText(restaurant.overall)}</div>
      </div>
    </div>
    <div class="detail-content">
      <div class="detail-grid">
        <span class="score-pill">Food ${ratingText(restaurant.food)}</span>
        <span class="score-pill">Service ${ratingText(restaurant.service)}</span>
        <span class="score-pill">Atmosphere ${ratingText(restaurant.atmosphere)}</span>
        <span class="score-pill">${escapeHtml(locationLine(restaurant))}</span>
      </div>
      <div class="meta">Added by ${escapeHtml(restaurant.createdBy)} · Updated by ${escapeHtml(restaurant.updatedBy)} on ${formatDate(restaurant.updatedAt)}</div>
      ${restaurant.orderedItems ? `<section><h4>Ordered</h4><p class="detail-note">${escapeHtml(restaurant.orderedItems)}</p></section>` : ""}
      ${restaurant.notes ? `<section><h4>Notes</h4><p class="detail-note">${escapeHtml(restaurant.notes)}</p></section>` : ""}
      ${photos.length ? `<section><h4>Photos</h4><div class="photo-gallery">${photos.map((photo) => `<img src="${photo}" alt="${escapeHtml(restaurant.name)} photo" />`).join("")}</div></section>` : ""}
      <div class="card-actions">
        <button type="button" data-edit="${restaurant.id}">Edit</button>
        ${restaurant.googleUrl ? `<a href="${escapeAttribute(restaurant.googleUrl)}" target="_blank" rel="noreferrer">Open Google link</a>` : ""}
      </div>
    </div>
  `;
  elements.detailDialog.showModal();
}

function readSinglePhoto(file) {
  if (!file) return Promise.resolve("");
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.readAsDataURL(file);
  });
}

function readPhotoList(fileList) {
  return Promise.all(Array.from(fileList || []).map(readSinglePhoto));
}

function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, (char) => {
    const chars = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
    return chars[char];
  });
}

function escapeAttribute(value = "") {
  return escapeHtml(value).replace(/`/g, "&#96;");
}

function init() {
  elements.reviewerName.value = localStorage.getItem(MEMBER_KEY) || "";
  loadRestaurants();
  bindEvents();
  render();
}

init();
