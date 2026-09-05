import Link from "next/link";

export default function Home() {
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
            <Link className="button" href="/recipes/new">
              Add your first recipe <span aria-hidden="true">↗</span>
            </Link>
            <span className="browse-hero__hint">A quiet place for recipes that matter.</span>
          </div>
        </div>
        <div className="browse-hero__stamp" aria-label="Recipe collection status">
          <span className="browse-hero__stamp-number">0</span>
          <span className="browse-hero__stamp-label">recipes<br />on the shelf</span>
        </div>
      </section>

      <section className="browse-content" aria-labelledby="collection-heading">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Your collection</p>
            <h2 id="collection-heading">The shelf is waiting</h2>
          </div>
          <button className="filter-button" type="button" disabled>
            <span aria-hidden="true">⌕</span> Search recipes
          </button>
        </div>
        <div className="empty-state">
          <div className="empty-state__illustration" aria-hidden="true">
            <span>✦</span>
          </div>
          <div>
            <h3>Start with something you love</h3>
            <p>Add a recipe from memory, a family notebook, or the back of a well-used card.</p>
            <Link className="text-link text-link--accent" href="/recipes/new">
              Create a recipe <span aria-hidden="true">→</span>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
