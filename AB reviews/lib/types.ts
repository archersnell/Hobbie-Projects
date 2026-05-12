export type Profile = {
  id: string;
  email: string;
  display_name: string | null;
  role: "admin" | "member";
};

export type Restaurant = {
  id: string;
  name: string;
  cuisine: string;
  city: string | null;
  state: string | null;
  price_level: "$" | "$$" | "$$$" | "$$$$";
  google_url: string | null;
  overall_rating: number;
  food_rating: number;
  service_rating: number;
  atmosphere_rating: number;
  ordered_items: string | null;
  notes: string | null;
  main_photo_path: string | null;
  created_by: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
  created_profile?: Pick<Profile, "display_name" | "email"> | null;
  updated_profile?: Pick<Profile, "display_name" | "email"> | null;
  signed_main_photo?: string | null;
  photos?: RestaurantPhoto[];
};

export type RestaurantPhoto = {
  id: string;
  restaurant_id: string;
  storage_path: string;
  caption: string | null;
  uploaded_by: string;
  created_at: string;
  signed_url?: string | null;
};

export type RestaurantFormValues = {
  reviewerName: string;
  name: string;
  cuisine: string;
  city: string;
  state: string;
  price_level: "$" | "$$" | "$$$" | "$$$$";
  google_url: string;
  overall_rating: number;
  food_rating: number;
  service_rating: number;
  atmosphere_rating: number;
  ordered_items: string;
  notes: string;
};
