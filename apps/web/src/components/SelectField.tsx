type SelectOption = {
  value: string;
  label: string;
};

type SelectFieldProps = {
  id: string;
  label: string;
  value: string;
  options: SelectOption[];
  fullWidth?: boolean;
  onChange: (value: string) => void;
};

export default function SelectField({
  id,
  label,
  value,
  options,
  fullWidth = true,
  onChange,
}: SelectFieldProps) {
  return (
    <div className={`form-field${fullWidth ? " full-width" : ""}`}>
      <label htmlFor={id}>{label}</label>
      <select
        id={id}
        name={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <p className="field-feedback"> </p>
    </div>
  );
}
