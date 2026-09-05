"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  createRecipe,
  fetchRecipe,
  updateRecipe,
  type Recipe,
  type RecipeCreateInput,
} from "@/lib/api";

type EditorMode = "create" | "edit";

let keyCounter = 0;
const nextKey = () => {
  keyCounter += 1;
  return keyCounter;
};

type IngredientRow = {
  key: number;
  name: string;
  quantity: string;
  unit: string;
  notes: string;
};

type StepRow = { key: number; instruction: string };

function toMinutes(value: string): number | null {
  const parsed = Number.parseInt(value, 10);
  return Number.isNaN(parsed) || parsed <= 0 ? null : parsed;
}

function toQuantity(value: string): number | null {
  const parsed = Number.parseFloat(value);
  return Number.isNaN(parsed) ? null : parsed;
}

export function RecipeEditor({
  mode,
  recipeId,
}: {
  mode: EditorMode;
  recipeId?: number;
}) {
  const router = useRouter();
  const isEdit = mode === "edit";

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [prepTime, setPrepTime] = useState("");
  const [cookTime, setCookTime] = useState("");
  const [servings, setServings] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [ingredients, setIngredients] = useState<IngredientRow[]>(() => [
    { key: nextKey(), name: "", quantity: "", unit: "", notes: "" },
  ]);
  const [steps, setSteps] = useState<StepRow[]>(() => [
    { key: nextKey(), instruction: "" },
  ]);
  const [tagInput, setTagInput] = useState("");
  const [tags, setTags] = useState<string[]>([]);

  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [isLoading, setIsLoading] = useState(isEdit);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    if (!isEdit || recipeId == null) {
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        const data = await fetchRecipe(recipeId);
        if (!cancelled) {
          setRecipe(data);
          setTitle(data.title);
          setDescription(data.description ?? "");
          setPrepTime(data.prep_time != null ? String(data.prep_time) : "");
          setCookTime(data.cook_time != null ? String(data.cook_time) : "");
          setServings(data.servings != null ? String(data.servings) : "");
          setSourceUrl(data.source_url ?? "");
          setTags(data.tags.map((tag) => tag.name));
          setIngredients(
            data.ingredients.length
              ? data.ingredients.map((ingredient) => ({
                  key: nextKey(),
                  name: ingredient.name,
                  quantity: ingredient.quantity != null ? String(ingredient.quantity) : "",
                  unit: ingredient.unit ?? "",
                  notes: ingredient.notes ?? "",
                }))
              : [{ key: nextKey(), name: "", quantity: "", unit: "", notes: "" }],
          );
          setSteps(
            [...data.steps]
              .sort((a, b) => a.order - b.order)
              .map((step) => ({ key: nextKey(), instruction: step.instruction })),
          );
        }
      } catch {
        if (!cancelled) {
          setLoadError(
            "This recipe couldn't be loaded. You may not have permission to edit it.",
          );
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [isEdit, recipeId]);

  function updateIngredient(key: number, patch: Partial<IngredientRow>) {
    setIngredients((rows) => rows.map((row) => (row.key === key ? { ...row, ...patch } : row)));
  }

  function updateStep(key: number, patch: Partial<StepRow>) {
    setSteps((rows) => rows.map((row) => (row.key === key ? { ...row, ...patch } : row)));
  }

  function addIngredient() {
    setIngredients((rows) => [...rows, { key: nextKey(), name: "", quantity: "", unit: "", notes: "" }]);
  }

  function addStep() {
    setSteps((rows) => [...rows, { key: nextKey(), instruction: "" }]);
  }

  function removeIngredient(key: number) {
    setIngredients((rows) => rows.filter((row) => row.key !== key));
  }

  function removeStep(key: number) {
    setSteps((rows) => rows.filter((row) => row.key !== key));
  }

  function moveIngredient(key: number, direction: -1 | 1) {
    setIngredients((rows) => {
      const index = rows.findIndex((row) => row.key === key);
      const target = index + direction;
      if (index < 0 || target < 0 || target >= rows.length) return rows;
      const copy = [...rows];
      [copy[index], copy[target]] = [copy[target], copy[index]];
      return copy;
    });
  }

  function moveStep(key: number, direction: -1 | 1) {
    setSteps((rows) => {
      const index = rows.findIndex((row) => row.key === key);
      const target = index + direction;
      if (index < 0 || target < 0 || target >= rows.length) return rows;
      const copy = [...rows];
      [copy[index], copy[target]] = [copy[target], copy[index]];
      return copy;
    });
  }

  function commitTags() {
    const name = tagInput.trim().toLowerCase();
    if (name && !tags.includes(name)) {
      setTags((current) => [...current, name]);
    }
    setTagInput("");
  }

  function removeTag(name: string) {
    setTags((current) => current.filter((tag) => tag !== name));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!title.trim()) {
      setError("Give your recipe a title.");
      return;
    }

    const cleanIngredients = ingredients
      .map((row) => ({
        name: row.name.trim(),
        quantity: toQuantity(row.quantity),
        unit: row.unit.trim() || null,
        notes: row.notes.trim() || null,
      }))
      .filter((row) => row.name.length > 0);

    const cleanSteps = steps
      .map((row) => row.instruction.trim())
      .filter((instruction) => instruction.length > 0);

    if (!cleanIngredients.length) {
      setError("Add at least one ingredient.");
      return;
    }
    if (!cleanSteps.length) {
      setError("Add at least one step.");
      return;
    }

    const payload: RecipeCreateInput = {
      title: title.trim(),
      description: description.trim() || null,
      prep_time: toMinutes(prepTime),
      cook_time: toMinutes(cookTime),
      servings: toMinutes(servings),
      source_url: sourceUrl.trim() || null,
      ingredients: cleanIngredients,
      steps: cleanSteps.map((instruction) => ({ instruction })),
      tags,
    };

    setIsSubmitting(true);
    try {
      const saved = isEdit
        ? await updateRecipe(recipeId as number, payload)
        : await createRecipe(payload);
      router.push(`/recipes/${saved.id}`);
      router.refresh();
    } catch {
      setError("The recipe couldn't be saved right now. Please try again.");
      setIsSubmitting(false);
    }
  }

  if (isLoading) {
    return (
      <div className="editor-page">
        <div className="editor-skeleton">
          <div className="editor-skeleton__hero" />
          <div className="editor-skeleton__block" />
          <div className="editor-skeleton__block" />
        </div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="editor-page">
        <div className="browse-error" role="alert">
          <h3>Can&apos;t edit this recipe</h3>
          <p>{loadError}</p>
          {recipeId != null ? (
            <Link className="text-link text-link--accent" href={`/recipes/${recipeId}`}>
              Back to the recipe <span aria-hidden="true">→</span>
            </Link>
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <form className="editor-page" onSubmit={handleSubmit} noValidate>
      <div className="editor-hero">
        <div>
          <p className="eyebrow">{mode === "create" ? "New recipe" : "Edit recipe"}</p>
          <h1>{mode === "create" ? "What are we making?" : (recipe?.title ?? "Edit recipe")}</h1>
        </div>
        <div className="editor-hero__actions">
          <Link
            className="text-link"
            href={isEdit && recipeId != null ? `/recipes/${recipeId}` : "/"}
          >
            {isEdit ? "Cancel" : "Back to the shelf"}
          </Link>
          <button className="button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Saving..." : isEdit ? "Save changes" : "Save recipe"}
            {!isSubmitting ? <span aria-hidden="true">↗</span> : null}
          </button>
        </div>
      </div>

      {error ? (
        <p className="editor-error" role="alert">
          {error}
        </p>
      ) : null}

      <section className="editor-section" aria-labelledby="basics-heading">
        <h2 id="basics-heading">Basics</h2>
        <div className="editor-field">
          <label htmlFor="editor-title">Title</label>
          <input
            id="editor-title"
            type="text"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="e.g. The winter pasta we make every Sunday"
            required
          />
        </div>
        <div className="editor-field">
          <label htmlFor="editor-description">Description</label>
          <textarea
            id="editor-description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="A line or two about where this recipe came from and why it earns its place on the shelf."
            rows={3}
          />
        </div>
        <div className="editor-field-row">
          <div className="editor-field">
            <label htmlFor="editor-prep">Prep time (min)</label>
            <input
              id="editor-prep"
              type="number"
              min={1}
              value={prepTime}
              onChange={(event) => setPrepTime(event.target.value)}
              placeholder="10"
            />
          </div>
          <div className="editor-field">
            <label htmlFor="editor-cook">Cook time (min)</label>
            <input
              id="editor-cook"
              type="number"
              min={1}
              value={cookTime}
              onChange={(event) => setCookTime(event.target.value)}
              placeholder="25"
            />
          </div>
          <div className="editor-field">
            <label htmlFor="editor-servings">Servings</label>
            <input
              id="editor-servings"
              type="number"
              min={1}
              value={servings}
              onChange={(event) => setServings(event.target.value)}
              placeholder="4"
            />
          </div>
        </div>
        <div className="editor-field">
          <label htmlFor="editor-source">Source URL</label>
          <input
            id="editor-source"
            type="url"
            value={sourceUrl}
            onChange={(event) => setSourceUrl(event.target.value)}
            placeholder="https://... (optional)"
          />
        </div>
      </section>

      <section className="editor-section" aria-labelledby="ingredients-heading">
        <div className="editor-section__heading">
          <div>
            <h2 id="ingredients-heading">Ingredients</h2>
            <p className="editor-section__hint">What you&apos;ll need, in the order you&apos;ll use it.</p>
          </div>
          <button className="button button--ghost button--small" type="button" onClick={addIngredient}>
            + Add ingredient
          </button>
        </div>
        {ingredients.map((row, index) => (
          <div className="ingredient-editor-row" key={row.key}>
            <div className="ingredient-editor-row__order">
              <span className="ingredient-editor-row__num">{index + 1}.</span>
              <div className="ingredient-editor-row__move">
                <button
                  type="button"
                  aria-label={`Move ingredient ${index + 1} up`}
                  disabled={index === 0}
                  onClick={() => moveIngredient(row.key, -1)}
                >
                  ↑
                </button>
                <button
                  type="button"
                  aria-label={`Move ingredient ${index + 1} down`}
                  disabled={index === ingredients.length - 1}
                  onClick={() => moveIngredient(row.key, 1)}
                >
                  ↓
                </button>
              </div>
            </div>
            <input
              type="text"
              value={row.name}
              onChange={(event) => updateIngredient(row.key, { name: event.target.value })}
              placeholder="Ingredient"
              aria-label={`Ingredient ${index + 1} name`}
            />
            <input
              type="text"
              value={row.quantity}
              onChange={(event) => updateIngredient(row.key, { quantity: event.target.value })}
              placeholder="2"
              aria-label={`Ingredient ${index + 1} quantity`}
              className="ingredient-editor-row__qty"
            />
            <input
              type="text"
              value={row.unit}
              onChange={(event) => updateIngredient(row.key, { unit: event.target.value })}
              placeholder="cups"
              aria-label={`Ingredient ${index + 1} unit`}
              className="ingredient-editor-row__unit"
            />
            <input
              type="text"
              value={row.notes}
              onChange={(event) => updateIngredient(row.key, { notes: event.target.value })}
              placeholder="chopped, optional"
              aria-label={`Ingredient ${index + 1} notes`}
              className="ingredient-editor-row__notes"
            />
            <button
              className="ingredient-editor-row__remove"
              type="button"
              onClick={() => removeIngredient(row.key)}
              aria-label={`Remove ingredient ${index + 1}`}
            >
              ✕
            </button>
          </div>
        ))}
      </section>

      <section className="editor-section" aria-labelledby="method-heading">
        <div className="editor-section__heading">
          <div>
            <h2 id="method-heading">Method</h2>
            <p className="editor-section__hint">The steps, in the order you do them.</p>
          </div>
          <button className="button button--ghost button--small" type="button" onClick={addStep}>
            + Add step
          </button>
        </div>
        {steps.map((row, index) => (
          <div className="step-editor-row" key={row.key}>
            <div className="step-editor-row__order">
              <span className="step-editor-row__num">{index + 1}.</span>
              <div className="step-editor-row__move">
                <button
                  type="button"
                  aria-label={`Move step ${index + 1} up`}
                  disabled={index === 0}
                  onClick={() => moveStep(row.key, -1)}
                >
                  ↑
                </button>
                <button
                  type="button"
                  aria-label={`Move step ${index + 1} down`}
                  disabled={index === steps.length - 1}
                  onClick={() => moveStep(row.key, 1)}
                >
                  ↓
                </button>
              </div>
            </div>
            <textarea
              value={row.instruction}
              onChange={(event) => updateStep(row.key, { instruction: event.target.value })}
              placeholder="Describe the step..."
              aria-label={`Step ${index + 1}`}
              rows={2}
            />
            <button
              className="step-editor-row__remove"
              type="button"
              onClick={() => removeStep(row.key)}
              aria-label={`Remove step ${index + 1}`}
            >
              ✕
            </button>
          </div>
        ))}
      </section>

      <section className="editor-section" aria-labelledby="tags-heading">
        <h2 id="tags-heading">Tags</h2>
        <p className="editor-section__hint">Press Enter or comma to add a tag.</p>
        <div className="tag-editor">
          <input
            type="text"
            value={tagInput}
            onChange={(event) => setTagInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === ",") {
                event.preventDefault();
                commitTags();
              }
            }}
            placeholder="e.g. dinner, weeknight, baking"
            aria-label="Add a tag"
          />
          <button className="button button--ghost button--small" type="button" onClick={commitTags}>
            + Add
          </button>
        </div>
        {tags.length ? (
          <ul className="editor-tags">
            {tags.map((tag) => (
              <li key={tag}>
                <span className="tag-pill tag-pill--editable">
                  {tag}
                  <button type="button" aria-label={`Remove tag ${tag}`} onClick={() => removeTag(tag)}>
                    ✕
                  </button>
                </span>
              </li>
            ))}
          </ul>
        ) : null}
      </section>
    </form>
  );
}