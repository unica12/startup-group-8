import { useId } from 'react';

export default function Input({ label, error, className = '', id, ...props }) {
  const autoId = useId();
  const inputId = id || autoId;
  const errorId = `${inputId}-error`;
  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      {label && (
        <label htmlFor={inputId} className="text-[13.5px] font-extrabold text-text">
          {label}
        </label>
      )}
      <input
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={`w-full rounded-input bg-bg border-2 px-4 py-3.5 text-base text-text
          placeholder:text-text-muted transition-colors
          focus:bg-white focus:border-green
          ${error ? 'border-danger' : 'border-bg'}`}
        {...props}
      />
      {error && <span id={errorId} role="alert" className="text-[12.5px] text-danger font-semibold">{error}</span>}
    </div>
  );
}
