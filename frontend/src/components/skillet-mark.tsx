export function SkilletMark() {
  return (
    <svg
      className="skillet-mark"
      viewBox="0 0 48 48"
      aria-hidden="true"
      focusable="false"
    >
      <rect x="2" y="21.5" width="14" height="9" rx="4.5" fill="var(--char)" />
      <circle cx="7" cy="26" r="2" fill="var(--paper)" />
      <circle cx="30" cy="26" r="15" fill="var(--char)" />
      <circle cx="30" cy="26" r="12.2" fill="var(--ember)" />
      <path
        d="M30 14.4c3 0 4.9 1.8 6.6 3.5 1.6-.3 3.2.3 4.3 1.7 1.1 1.5 1 3.4-.2 4.9-1 1.1-1 2.4-.3 3.5.9 1.6.3 3.4-1.1 4.2-1.3.8-2.9.5-4.2-.3-1.4-.9-3.1-1-4.5-.3-1.8.9-3.9.9-5.6-.1-1.6-1-2.8-2.6-2.8-4.4 0-1.8 1-3.4 2.7-4.5 1.2-.8 2.3-1.7 3.9-2.4z"
        fill="var(--surface)"
      />
      <circle cx="30" cy="25.4" r="4.7" fill="var(--honey)" />
      <circle cx="28.4" cy="23.6" r="1.1" fill="var(--paper)" opacity="0.9" />
      <circle cx="40" cy="12.5" r="0.9" fill="var(--honey)" />
      <circle cx="21.5" cy="12.5" r="0.8" fill="var(--flame)" />
    </svg>
  );
}