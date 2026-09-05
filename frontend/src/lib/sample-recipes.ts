import type { Recipe } from "@/lib/api";

function sampleRecipe(
  id: number,
  title: string,
  tagNames: string[],
  prepTime: number,
  cookTime: number,
): Recipe {
  return {
    id,
    owner_id: null,
    title,
    description: null,
    prep_time: prepTime,
    cook_time: cookTime,
    servings: 4,
    source_url: null,
    is_locked: false,
    created_at: "2025-01-01T00:00:00Z",
    last_cooked: null,
    ingredients: [],
    steps: [],
    images: [],
    tags: tagNames.map((name, index) => ({ id: index + 1, name })),
  };
}

export const SAMPLE_RECIPES: Recipe[] = [
  sampleRecipe(-1, "One-Pan Tomato Butter Pasta", ["dinner", "weeknight"], 10, 25),
  sampleRecipe(-2, "Sunday No-Knead Bread", ["baking"], 15, 45),
  sampleRecipe(-3, "Weeknight Fried Rice", ["dinner", "leftovers"], 15, 15),
];