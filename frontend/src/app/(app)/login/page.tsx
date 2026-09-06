import Link from "next/link";
import { AuthForm } from "@/components/auth-form";

export default function LoginPage() {
  return (
    <div className="auth-page">
      <div className="auth-page__aside">
        <p className="eyebrow">Welcome back</p>
        <h1>Pick up where the good stuff left off.</h1>
        <p className="auth-page__aside-copy">
          Your recipes, your rhythm, and the little details that make dinner feel like yours.
        </p>
        <span className="auth-page__aside-note">A shared shelf for the people at your table.</span>
      </div>
      <div className="auth-card">
        <div className="auth-card__heading">
          <p className="eyebrow">Sign in</p>
          <h2>Welcome to Skillet</h2>
          <p>Log in to browse your household cookbook.</p>
        </div>
        <AuthForm mode="login" />
        <p className="auth-card__footer">
          New to the shelf? <Link href="/register">Create an account</Link>
        </p>
      </div>
    </div>
  );
}
