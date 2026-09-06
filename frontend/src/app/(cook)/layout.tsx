export default function CookLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="cook-shell">
      {children}
    </div>
  );
}