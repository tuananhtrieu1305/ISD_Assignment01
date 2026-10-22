import { ReactNode } from "react";

type ResultCardProps = {
  title: string;
  children: ReactNode;
};

export default function ResultCard({ title, children }: ResultCardProps) {
  return (
    <section className="result-card" aria-live="polite">
      <h2>{title}</h2>
      {children}
    </section>
  );
}
