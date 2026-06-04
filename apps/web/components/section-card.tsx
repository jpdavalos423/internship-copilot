import type { ReactNode } from "react";

type SectionCardProps = {
  title: string;
  description?: string;
  children?: ReactNode;
};

export function SectionCard({ title, description, children }: SectionCardProps) {
  return (
    <section className="card">
      <h2 className="card__title">{title}</h2>
      {description ? <p className="card__description">{description}</p> : null}
      {children ? <div style={{ marginTop: "1rem" }}>{children}</div> : null}
    </section>
  );
}
