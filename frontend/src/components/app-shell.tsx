import Link from "next/link";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <header className="site-header">
        <Link className="brand-mark" href="/" aria-label="Skillet home">
          <span className="brand-mark__icon" aria-hidden="true">
            S
          </span>
          <span>
            <span className="brand-mark__name">Skillet</span>
            <span className="brand-mark__tagline">your shared recipe shelf</span>
          </span>
        </Link>

        <nav className="site-nav" aria-label="Primary navigation">
          <Link className="site-nav__link site-nav__link--active" href="/">
            Browse
          </Link>
          <Link className="site-nav__link" href="/recipes/new">
            Add recipe
          </Link>
        </nav>

        <div className="site-header__actions">
          <Link className="text-link" href="/login">
            Log in
          </Link>
          <Link className="button button--small" href="/register">
            Join the shelf
          </Link>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
