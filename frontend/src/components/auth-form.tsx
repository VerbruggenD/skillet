"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

type AuthMode = "login" | "register";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function AuthForm({ mode }: { mode: AuthMode }) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [keepPrivate, setKeepPrivate] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRegistered, setIsRegistered] = useState(false);

  const isLogin = mode === "login";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await fetch(`${API_URL}/api/auth/${isLogin ? "cookie/login" : "register"}`, {
        method: "POST",
        credentials: "include",
        headers: isLogin
          ? { "Content-Type": "application/x-www-form-urlencoded" }
          : { "Content-Type": "application/json" },
        body: isLogin
          ? new URLSearchParams({ username: email, password })
          : JSON.stringify({
              email,
              password,
              default_recipe_locked: keepPrivate,
            }),
      });

      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(body?.detail ?? "Something went wrong. Please try again.");
      }

      if (isLogin) {
        router.push("/");
        router.refresh();
      } else {
        const loginResponse = await fetch(`${API_URL}/api/auth/cookie/login`, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({ username: email, password }),
        });

        if (loginResponse.ok) {
          router.push("/");
          router.refresh();
        } else {
          setIsRegistered(true);
        }
      }
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "The kitchen is having trouble connecting. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isRegistered) {
    return (
      <div className="auth-success" role="status">
        <span className="auth-success__mark" aria-hidden="true">
          ✓
        </span>
        <h2>You&apos;re on the shelf.</h2>
        <p>Your account is ready. Log in to start collecting recipes.</p>
        <Link className="button auth-form__submit" href="/login">
          Continue to log in <span aria-hidden="true">→</span>
        </Link>
      </div>
    );
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <div className="auth-form__field">
        <label htmlFor={`${mode}-email`}>Email address</label>
        <input
          id={`${mode}-email`}
          name="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@example.com"
        />
      </div>
      <div className="auth-form__field">
        <div className="auth-form__label-row">
          <label htmlFor={`${mode}-password`}>Password</label>
          {isLogin ? <span className="auth-form__helper">At least 8 characters</span> : null}
        </div>
        <input
          id={`${mode}-password`}
          name="password"
          type="password"
          autoComplete={isLogin ? "current-password" : "new-password"}
          minLength={8}
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="••••••••"
        />
      </div>
      {!isLogin ? (
        <label className="auth-form__check">
          <input
            type="checkbox"
            checked={keepPrivate}
            onChange={(event) => setKeepPrivate(event.target.checked)}
          />
          <span>Keep new recipes private by default</span>
        </label>
      ) : null}
      {error ? (
        <p className="auth-form__error" role="alert">
          {error}
        </p>
      ) : null}
      <button className="button auth-form__submit" type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Working..." : isLogin ? "Log in to Skillet" : "Create my shelf"}
        {!isSubmitting ? <span aria-hidden="true">↗</span> : null}
      </button>
    </form>
  );
}
