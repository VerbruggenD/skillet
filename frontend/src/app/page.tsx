"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/components/auth-provider";
import { RecipeCard } from "@/components/recipe-card";
import { SAMPLE_RECIPES } from "@/lib/sample-recipes";
import {
  fetchRecipes,
  fetchTags,
  type Recipe,
  type RecipeListSort,
  type Tag,
} from "@/lib/api";

function GridIcon() {
  return (
    <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
      <rect x="1" y="1" width="6" height="6" rx="1" fill="currentColor" />
      <rect x="9" y="1" width="6" height="6" rx="1" fill="currentColor" />
      <rect x="1" y="9" width="6" height="6" rx="1" fill="currentColor" />
      <rect x="9" y="9" width="6" height="6" rx="1" fill="currentColor" />
    </svg>
  );
}

function ListIcon() {
  return (
    <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
      <rect x="1" y="2" width="4" height="3" rx="0.6" fill="currentColor" />
      <rect x="7" y="2.8" width="8" height="1.4" rx="0.7" fill="currentColor" />
      <rect x="1" y="7" width="4" height="3" rx="0.6" fill="currentColor" />
      <rect x="7" y="7.8" width="8" height="1.4" rx="0.7" fill="currentColor" />
      <rect x="1" y="12" width="4" height="3" rx="0.6" fill="currentColor" />
      <rect x="7" y="12.8" width="8" height="1.4" rx="0.7" fill="currentColor" />
    </svg>
  );
}

export default function Home() {
  const { user } = useAuth();
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [total, setTotal] = useState(0);
  const [allTags, setAllTags] = useState<Tag[]>([]);
  const [sort, setSort] = useState<RecipeListSort>("date");
  const [view, setView] = useState<"grid" | "list">("grid");
  const [searchInput, setSearchInput] = useState("");
  const [query, setQuery] = useState("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [reloadKey, setReloadKey] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const data = await fetchTags();
        if (!cancelled) {
          setAllTags(data);
        }
      } catch {
        // tags are a browse nicety; ignore failures silently
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const data = await fetchRecipes({
          sort,
          limit: 24,
          q: query || undefined,
          tag: selectedTags.length ? selectedTags : undefined,
        });
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
  }, [sort, query, reloadKey, selectedTags]);

  function handleSortChange(nextSort: RecipeListSort) {
    setSort(nextSort);
    setError(null);
    setIsLoading(true);
  }

  function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setQuery(searchInput.trim().toLowerCase());
    setError(null);
    setIsLoading(true);
  }

  function handleClearSearch() {
    setSearchInput("");
    setQuery("");
    setError(null);
    setIsLoading(true);
  }

  function handleTagToggle(tagName: string) {
    setSelectedTags((current) =>
      current.includes(tagName) ? current.filter((name) => name !== tagName) : [...current, tagName],
    );
    setError(null);
    setIsLoading(true);
  }

  function handleClearFilters() {
    setSearchInput("");
    setQuery("");
    setSelectedTags([]);
    setError(null);
    setIsLoading(true);
  }

  function handleRetry() {
    setReloadKey((key) => key + 1);
    setError(null);
    setIsLoading(true);
  }

  const isFresh = total > 0;
  const hasActiveFilters = query.trim().length > 0 || selectedTags.length > 0;
  const gridClass = view === "list" ? " recipe-grid--list" : "";

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

        <div className="browse-filters">
          <form className="browse-search" role="search" onSubmit={handleSearch}>
            <span className="browse-search__icon" aria-hidden="true">
              ⌕
            </span>
            <input
              type="search"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Search recipes by name or ingredient..."
              aria-label="Search recipes"
            />
            {searchInput ? (
              <button
                className="browse-search__clear"
                type="button"
                onClick={handleClearSearch}
                aria-label="Clear search"
              >
                ✕
              </button>
            ) : null}
          </form>

          <div className="view-toggle" role="group" aria-label="Choose layout">
            <button
              type="button"
              className={`view-toggle__button${view === "grid" ? " view-toggle__button--active" : ""}`}
              aria-pressed={view === "grid"}
              onClick={() => setView("grid")}
              title="Grid view"
            >
              <GridIcon />
            </button>
            <button
              type="button"
              className={`view-toggle__button${view === "list" ? " view-toggle__button--active" : ""}`}
              aria-pressed={view === "list"}
              onClick={() => setView("list")}
              title="List view"
            >
              <ListIcon />
            </button>
          </div>
        </div>

        {allTags.length ? (
          <div className="browse-tags">
            <span className="sort-label">Filter by tag</span>
            <ul className="browse-tags__chips">
              {allTags.map((tag) => {
                const active = selectedTags.includes(tag.name);
                return (
                  <li key={tag.id}>
                    <button
                      type="button"
                      className={`tag-filter-chip${active ? " tag-filter-chip--active" : ""}`}
                      aria-pressed={active}
                      onClick={() => handleTagToggle(tag.name)}
                    >
                      {tag.name}
                    </button>
                  </li>
                );
              })}
            </ul>
            {hasActiveFilters ? (
              <button
                className="tag-filter-clear"
                type="button"
                onClick={handleClearFilters}
              >
                Clear filters
              </button>
            ) : null}
          </div>
        ) : null}

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
          <div className={`recipe-grid${gridClass}`}>
            {recipes.map((recipe) => (
              <RecipeCard key={recipe.id} recipe={recipe} />
            ))}
          </div>
        ) : hasActiveFilters ? (
          <div className="empty-state">
            <div className="empty-state__illustration" aria-hidden="true">
              <span>⌕</span>
            </div>
            <div>
              <h3>Nothing under those filters</h3>
              <p>Try a different search term, or clear the tags to see the whole shelf.</p>
              <button className="text-link text-link--accent" type="button" onClick={handleClearFilters}>
                Clear filters <span aria-hidden="true">→</span>
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className={`recipe-grid${gridClass}`}>
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