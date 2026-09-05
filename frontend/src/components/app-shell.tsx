"use client";

import Link from "next/link";
import { useAuth } from "@/components/auth-provider";
import { SkilletMark } from "@/components/skillet-mark";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, isLoading, logout } = useAuth();

  const showAuthenticated = !isLoading && user !== null;

  return (
    <div className="app-shell">
      <header className="site-header">
        <Link className="brand-mark" href="/" aria-label="Skillet home">
          <span className="brand-mark__icon" aria-hidden="true">
            <SkilletMark />
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
          {showAuthenticated ? (
            <Link className="site-nav__link" href="/recipes/new">
              Add recipe
            </Link>
          ) : null}
        </nav>

        <div className="site-header__actions">
          {showAuthenticated ? (
            <>
              {user.is_superuser ? (
                <Link className="site-nav__link" href="/admin/users">
                  Admin
                </Link>
              ) : null}
              <Link className="text-link" href="/account">
                Account
              </Link>
              <span className="site-header__user" title={user.email}>
                {user.email}
              </span>
              <button className="text-link site-header__logout" type="button" onClick={() => void logout()}>
                Log out
              </button>
            </>
          ) : (
            <>
              <Link className="text-link" href="/login">
                Log in
              </Link>
              <Link className="button button--small" href="/register">
                Join the shelf
              </Link>
            </>
          )}
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
