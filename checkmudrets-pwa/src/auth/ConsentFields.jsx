import { CONSENT_DOCUMENTS } from './documents';

export default function ConsentFields({ checked, onChange, disabled }) {
  return (
    <fieldset className="min-w-0 rounded-input border border-line px-3 pb-3" disabled={disabled}>
      <legend className="px-1 text-sm font-extrabold">Обязательные согласия</legend>
      <p className="mt-1 text-xs text-text-soft">Предварительные документы учебного прототипа</p>
      {CONSENT_DOCUMENTS.map(({ id, label, title, text, version }) => (
        <div className="mt-3" key={id}>
          <label className="flex min-h-7 cursor-pointer items-start gap-2 text-[13px] font-bold leading-snug">
            <input
              type="checkbox" required checked={Boolean(checked[id])}
              onChange={(event) => onChange({ ...checked, [id]: event.target.checked })}
              className="mt-0.5 size-4 shrink-0 accent-brand"
            />
            {label}
          </label>
          <details className="ml-6 text-xs text-text-soft">
            <summary className="cursor-pointer rounded text-brand font-bold">{title}</summary>
            <p className="mt-1 leading-relaxed">{text}</p>
            <p className="mt-1">Версия документа {version}</p>
          </details>
        </div>
      ))}
    </fieldset>
  );
}
