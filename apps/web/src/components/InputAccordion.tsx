import { PropsWithChildren, useState } from "react";

type InputAccordionProps = PropsWithChildren<{
  title: string;
  defaultOpen?: boolean;
}>;

export default function InputAccordion({
  title,
  defaultOpen = false,
  children,
}: InputAccordionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <section className={`input-accordion ${open ? "open" : ""}`}>
      <button
        type="button"
        className="input-accordion-trigger"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <span>{title}</span>
        <span className="input-accordion-chevron" aria-hidden="true">
          v
        </span>
      </button>
      <div className="input-accordion-shell" aria-hidden={!open}>
        <div className="input-accordion-content">{children}</div>
      </div>
    </section>
  );
}
