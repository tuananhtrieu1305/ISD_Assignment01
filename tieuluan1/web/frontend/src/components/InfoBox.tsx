import { ReactNode } from "react";

type InfoBoxProps = {
  title: string;
  children: ReactNode;
  tone?: "neutral" | "warning";
};

export default function InfoBox({
  title,
  children,
  tone = "neutral",
}: InfoBoxProps) {
  return (
    <section className={`info-box ${tone}`}>
      <h3>{title}</h3>
      <p>{children}</p>
    </section>
  );
}
