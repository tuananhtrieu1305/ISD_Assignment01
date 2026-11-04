type FormFieldProps = {
  id: string;
  label: string;
  value: string;
  error?: string;
  min?: number;
  step?: string;
  onChange: (value: string) => void;
};

export default function FormField({
  id,
  label,
  value,
  error,
  min,
  step = "any",
  onChange,
}: FormFieldProps) {
  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        name={id}
        type="number"
        min={min}
        step={step}
        value={value}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : undefined}
        onChange={(event) => onChange(event.target.value)}
      />
      <p className="field-feedback" id={`${id}-error`}>
        {error ?? " "}
      </p>
    </div>
  );
}
