"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { fetchRecipe, type Ingredient, type Recipe } from "@/lib/api";
import { formatMinutes } from "@/lib/format";
import { SkilletMark } from "@/components/skillet-mark";
import { useAuth } from "@/components/auth-provider";

function quantityLabel(ingredient: Ingredient): string {
  const parts = [ingredient.quantity, ingredient.unit].filter(
    (value): value is string | number => value != null && value !== "",
  );
  return parts.join(" ") || "—";
}

function MetaItem({ label, value }: { label: string; value: string | null }) {
  if (!value) return null;
  return (
    <span className="recipe-detail__meta-item">
      <span className="recipe-detail__meta-label">{label}</span>
      <span className="recipe-detail__meta-value">{value}</span>
    </span>
  );
}

export default function RecipeDetailPage() {
  const params = useParams<{ id: string }>();
  const { user } = useAuth();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setIsLoading(true);
      setError(null);
      setRecipe(null);
      try {
        const data = await fetchRecipe(Number(params.id));
        if (!cancelled) {
          setRecipe(data);
        }
      } catch {
        if (!cancelled) {
          setError("This recipe could not be found, or you don't have access to it.");
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
  }, [params.id]);

  if (isLoading) {
    return (
      <div className="recipe-detail">
        <div className="recipe-detail__skeleton">
          <div className="recipe-detail__skeleton-hero" />
          <div className="recipe-detail__skeleton-line" />
          <div className="recipe-detail__skeleton-line recipe-detail__skeleton-line--short" />
          <div className="recipe-detail__skeleton-cols">
            <div className="recipe-detail__skeleton-col" />
            <div className="recipe-detail__skeleton-col" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !recipe) {
    return (
      <div className="recipe-detail">
        <div className="browse-error" role="alert">
          <h3>Recipe not found</h3>
          <p>{error}</p>
          <Link className="text-link text-link--accent" href="/">
            Back to the shelf <span aria-hidden="true">→</span>
          </Link>
        </div>
      </div>
    );
  }

  const canEdit = user !== null && (user.id === recipe.owner_id || user.is_superuser);
  const prepLabel = formatMinutes(recipe.prep_time);
  const cookLabel = formatMinutes(recipe.cook_time);

  return (
    <div className="recipe-detail">
      <Link className="recipe-detail__back" href="/">
        <span aria-hidden="true">←</span> Back to the shelf
      </Link>

      <header className="recipe-detail__hero">
        <div className="recipe-detail__hero-body">
          <p className="eyebrow">From the shelf</p>
          <h1>{recipe.title}</h1>
          {recipe.description ? (
            <p className="recipe-detail__description">{recipe.description}</p>
          ) : null}

          <div className="recipe-detail__meta">
            <MetaItem label="Prep" value={prepLabel} />
            <MetaItem label="Cook" value={cookLabel} />
            {recipe.servings ? (
              <MetaItem label="Serves" value={`${recipe.servings}`} />
            ) : null}
          </div>

          {recipe.tags.length ? (
            <ul className="recipe-detail__tags">
              {recipe.tags.map((tag) => (
                <li key={tag.id}>
                  <span className="tag-pill">{tag.name}</span>
                </li>
              ))}
            </ul>
          ) : null}
        </div>

        <div className="recipe-detail__hero-media" aria-hidden="true">
          <SkilletMark />
        </div>
      </header>

      <div className="recipe-detail__actions">
        <button className="button" type="button" disabled title="Cook mode is on its way">
          Start cooking <span aria-hidden="true">↗</span>
        </button>
        <button
          className="button button--ghost"
          type="button"
          disabled
          title="Shopping list is on its way"
        >
          Add to shopping list
        </button>
        {canEdit ? (
          <span className="recipe-detail__owner-actions">
            <button className="text-link" type="button" disabled title="Recipe editor is on its way">
              Edit
            </button>
            <button className="text-link" type="button" disabled title="Recipe editor is on its way">
              Delete
            </button>
          </span>
        ) : null}
      </div>

      <div className="recipe-detail__grid">
        <section className="recipe-detail__section" aria-labelledby="ingredients-heading">
          <h2 id="ingredients-heading">Ingredients</h2>
          {recipe.ingredients.length ? (
            <ul className="ingredient-list">
              {recipe.ingredients.map((ingredient) => (
                <li className="ingredient-row" key={ingredient.id}>
                  <span className="ingredient-row__qty">{quantityLabel(ingredient)}</span>
                  <span className="ingredient-row__name">
                    {ingredient.name}
                    {ingredient.notes ? (
                      <em className="ingredient-row__notes"> · {ingredient.notes}</em>
                    ) : null}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="recipe-detail__empty-hint">No ingredients listed.</p>
          )}
        </section>

        <section className="recipe-detail__section" aria-labelledby="method-heading">
          <h2 id="method-heading">Method</h2>
          {recipe.steps.length ? (
            <ol className="step-list">
              {[...recipe.steps]
                .sort((a, b) => a.order - b.order)
                .map((step) => (
                  <li className="step-item" key={step.id}>
                    <span className="step-item__number" aria-hidden="true">
                      {step.order}
                    </span>
                    <p className="step-item__text">{step.instruction}</p>
                  </li>
                ))}
            </ol>
          ) : (
            <p className="recipe-detail__empty-hint">No method listed.</p>
          )}
        </section>
      </div>
    </div>
  );
}