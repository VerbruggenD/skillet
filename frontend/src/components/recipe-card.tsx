import Link from "next/link";
import type { Recipe } from "@/lib/api";
import { formatMinutes, totalTimeMinutes } from "@/lib/format";
import { SkilletMark } from "@/components/skillet-mark";

export function RecipeCard({
  recipe,
  sample = false,
}: {
  recipe: Recipe;
  sample?: boolean;
}) {
  const total = totalTimeMinutes(recipe);
  const timeLabel = formatMinutes(total);

  const body = (
    <>
      <div className="recipe-card__media">
        {sample ? (
          <span className="recipe-card__sample-mark">Sample</span>
        ) : null}
        <span className="recipe-card__media-icon" aria-hidden="true">
          <SkilletMark />
        </span>
      </div>
      <div className="recipe-card__body">
        <h3>{recipe.title}</h3>
        {recipe.tags.length ? (
          <ul className="recipe-card__tags">
            {recipe.tags.map((tag) => (
              <li key={tag.id}>
                <span className="tag-pill">{tag.name}</span>
              </li>
            ))}
          </ul>
        ) : null}
        {timeLabel ? (
          <p className="recipe-card__meta">{timeLabel} total</p>
        ) : null}
      </div>
    </>
  );

  if (sample) {
    return (
      <article
        className="recipe-card recipe-card--sample"
        aria-label={`${recipe.title} — sample, not a real recipe`}
      >
        {body}
      </article>
    );
  }

  return (
    <article className="recipe-card">
      <Link className="recipe-card__link" href={`/recipes/${recipe.id}`}>
        {body}
      </Link>
    </article>
  );
}