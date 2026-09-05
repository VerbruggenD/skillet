import Link from "next/link";
import { AuthForm } from "@/components/auth-form";

export default function RegisterPage() {
  return (
    <div className="auth-page">
      <div className="auth-page__aside auth-page__aside--register">
        <p className="eyebrow">Make room at the table</p>
        <h1>Keep the recipes worth passing on.</h1>
        <p className="auth-page__aside-copy">
          Start a shared shelf for family favorites, experiments, and the weeknight saves you make
          on repeat.
        </p>
        <span className="auth-page__aside-note">No perfect handwriting required.</span>
      </div>
      <div className="auth-card">
        <div className="auth-card__heading">
          <p className="eyebrow">Create your shelf</p>
          <h2>Join Skillet</h2>
          <p>One account for the recipes your household wants to remember.</p>
        </div>
        <AuthForm mode="register" />
        <p className="auth-card__footer">
          Already have an account? <Link href="/login">Log in</Link>
        </p>
      </div>
    </div>
  );
}
