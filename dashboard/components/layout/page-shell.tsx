import type { ReactNode } from "react";

type PageShellProps = {
  children: ReactNode;
  className?: string;
  wide?: boolean;
  prose?: boolean;
  immersive?: boolean;
};

export function PageShell({
  children,
  className = "",
  wide = false,
  prose = true,
  immersive = false,
}: PageShellProps) {
  const shellClass = [
    "page-shell",
    immersive ? "page-shell--immersive" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const contentClass = [
    "page-content",
    "container",
    wide ? "container--wide" : "",
    prose ? "prose" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <section className={shellClass}>
      <div className={contentClass}>{children}</div>
    </section>
  );
}
