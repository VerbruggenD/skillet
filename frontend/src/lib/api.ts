const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Tag = { id: number; name: string };

export type Ingredient = {
  id: number;
  name: string;
  quantity: number | null;
  unit: string | null;
  notes: string | null;
};

export type Step = { id: number; order: number; instruction: string };

export type Image = { id: number; filename: string; created_at: string };

export type Recipe = {
  id: number;
  owner_id: number | null;
  title: string;
  description: string | null;
  prep_time: number | null;
  cook_time: number | null;
  servings: number | null;
  source_url: string | null;
  is_locked: boolean;
  created_at: string;
  last_cooked: string | null;
  ingredients: Ingredient[];
  steps: Step[];
  images: Image[];
  tags: Tag[];
};

export type RecipeListResponse = {
  items: Recipe[];
  total: number;
  page: number;
  limit: number;
};

export type RecipeListSort = "name" | "date" | "prep_time" | "last_cooked";

export type RecipeListParams = {
  q?: string;
  tag?: string[];
  sort?: RecipeListSort;
  page?: number;
  limit?: number;
};

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    ...init,
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export function fetchRecipes(params: RecipeListParams = {}): Promise<RecipeListResponse> {
  const query = new URLSearchParams();

  if (params.sort) query.set("sort", params.sort);
  if (params.page) query.set("page", String(params.page));
  if (params.limit) query.set("limit", String(params.limit));
  if (params.q) query.set("q", params.q);

  for (const tag of params.tag ?? []) {
    query.append("tag", tag);
  }

  const qs = query.toString();
  return apiFetch<RecipeListResponse>(`/api/recipes${qs ? `?${qs}` : ""}`);
}

export function fetchTags(): Promise<Tag[]> {
  return apiFetch<Tag[]>(`/api/tags`);
}

export function fetchRecipe(id: number): Promise<Recipe> {
  return apiFetch<Recipe>(`/api/recipes/${id}`);
}

export type IngredientInput = {
  name: string;
  quantity: number | null;
  unit: string | null;
  notes: string | null;
};

export type StepInput = { instruction: string };

export type RecipeCreateInput = {
  title: string;
  description: string | null;
  prep_time: number | null;
  cook_time: number | null;
  servings: number | null;
  source_url: string | null;
  ingredients: IngredientInput[];
  steps: StepInput[];
  tags: string[];
};

export function createRecipe(payload: RecipeCreateInput): Promise<Recipe> {
  return apiFetch<Recipe>(`/api/recipes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function updateRecipe(id: number, payload: RecipeCreateInput): Promise<Recipe> {
  return apiFetch<Recipe>(`/api/recipes/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}