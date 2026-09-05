"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/components/auth-provider";
import { RecipeCard } from "@/components/recipe-card";
import { SAMPLE_RECIPES } from "@/lib/sample-recipes";
import {
  fetchRecipes,
  type Recipe,
  type RecipeListSort,
} from "@/lib/api";

export default function Home() {
  const { user } = useAuth();
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [total, setTotal] = useState(0);
  const [sort, setSort] = useState<RecipeListSort>("date");
  const [reloadKey, setReloadKey] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const data = await fetchRecipes({ sort, limit: 24 });
        if (!cancelled) {
          setRecipes(data.items);
          setTotal(data.total);
        }
      } catch {
        if (!cancelled) {
          setError("The shelf couldn't be reached right now.");
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
  }, [sort, reloadKey]);

  function handleSortChange(nextSort: RecipeListSort) {
    setSort(nextSort);
    setError(null);
    setIsLoading(true);
  }

  function handleRetry() {
    setReloadKey((key) => key + 1);
    setError(null);
    setIsLoading(true);
  }

  const isFresh = total > 0;

  return (
    <div className="browse-page">
      <section className="browse-hero" aria-labelledby="browse-heading">
        <div className="browse-hero__copy">
          <p className="eyebrow">The good stuff, kept close</p>
          <h1 id="browse-heading">What are we cooking?</h1>
          <p className="browse-hero__intro">
            Your household cookbook for weeknight staples, ambitious projects, and the recipes
            nobody wants to lose.
          </p>
          <div className="browse-hero__actions">
            {user ? (
              <Link className="button" href="/recipes/new">
                Add a recipe <span aria-hidden="true">↗</span>
              </Link>
            ) : (
              <Link className="button" href="/login">
                Log in to add a recipe <span aria-hidden="true">↗</span>
              </Link>
            )}
            <span className="browse-hero__hint">
              {isFresh
                ? "Everything on the shelf, gathered in one warm place."
                : "A quiet place for recipes that matter."}
            </span>
          </div>
        </div>
        <div className="browse-hero__stamp" aria-label="Recipe collection status">
          <span className="browse-hero__stamp-number">{isLoading ? "…" : total}</span>
          <span className="browse-hero__stamp-label">
            {total === 1 ? "recipe" : "recipes"}
            <br />
            on the shelf
          </span>
        </div>
      </section>

      <section className="browse-content" aria-labelledby="collection-heading">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Your collection</p>
            <h2 id="collection-heading">{isFresh ? "Ready when you are" : "The shelf is waiting"}</h2>
          </div>
          <div className="browse-toolbar">
            <label className="sort-label" htmlFor="sort">
              Sort by
            </label>
            <select
              id="sort"
              className="sort-select"
              value={sort}
              onChange={(event) => handleSortChange(event.target.value as RecipeListSort)}
            >
              <option value="date">Newest</option>
              <option value="name">Name</option>
              <option value="prep_time">Prep time</option>
              <option value="last_cooked">Last cooked</option>
            </select>
          </div>
        </div>

        {isLoading ? (
          <div className="recipe-grid" aria-label="Loading recipes">
            {Array.from({ length: 6 }).map((_, index) => (
              <div className="recipe-skeleton" key={index}>
                <div className="recipe-skeleton__media" />
                <div className="recipe-skeleton__body">
                  <div className="recipe-skeleton__title" />
                  <div className="recipe-skeleton__line" />
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="browse-error" role="alert">
            <h3>Something went wrong</h3>
            <p>{error}</p>
            <button className="button button--small" type="button" onClick={handleRetry}>
              Try again
            </button>
          </div>
        ) : recipes.length ? (
          <div className="recipe-grid">
            {recipes.map((recipe) => (
              <RecipeCard key={recipe.id} recipe={recipe} />
            ))}
          </div>
        ) : (
          <>
            <div className="recipe-grid">
              {SAMPLE_RECIPES.map((recipe) => (
                <RecipeCard key={recipe.id} recipe={recipe} sample />
              ))}
            </div>
            <p className="browse-samples-note">
              Sample cards shown while the shelf is empty — your own recipes will take their
              place.
            </p>
            <div className="empty-state">
              <div className="empty-state__illustration" aria-hidden="true">
                <span>✦</span>
              </div>
              <div>
                <h3>Start with something you love</h3>
                <p>Add a recipe from memory, a family notebook, or the back of a well-used card.</p>
                <Link className="text-link text-link--accent" href={user ? "/recipes/new" : "/login"}>
                  {user ? "Create a recipe" : "Log in to create one"}{" "}
                  <span aria-hidden="true">→</span>
                </Link>
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  );
}