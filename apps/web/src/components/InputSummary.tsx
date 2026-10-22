type SummaryItem = {
  label: string;
  value: string | number;
};

type InputSummaryProps = {
  title: string;
  items: SummaryItem[];
};

export default function InputSummary({ title, items }: InputSummaryProps) {
  return (
    <section className="result-section">
      <h3>{title}</h3>
      <dl className="input-summary">
        {items.map((item) => (
          <div key={item.label}>
            <dt>{item.label}</dt>
            <dd>{item.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
