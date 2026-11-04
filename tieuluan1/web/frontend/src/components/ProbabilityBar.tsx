type ProbabilityBarProps = {
  label: string;
  probability: number;
  tone: "negative" | "positive";
};

function formatPercent(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}

export default function ProbabilityBar({
  label,
  probability,
  tone,
}: ProbabilityBarProps) {
  const safeProbability = Math.min(Math.max(probability, 0), 1);

  return (
    <div className="probability-block">
      <div className="probability-meter">
        <div className="probability-meter-label">
          <span>{label}</span>
          <strong>{formatPercent(safeProbability)}</strong>
        </div>
        <div className="probability-track" aria-hidden="true">
          <span
            className={`probability-fill ${tone}`}
            style={{ width: `${safeProbability * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}
