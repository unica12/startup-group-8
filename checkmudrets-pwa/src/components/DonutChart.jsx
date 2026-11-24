/**
 * Кольцевая диаграмма на чистом SVG (stroke-dasharray), без библиотек.
 * segments: [{ label, amount, percent, color }]
 */
export default function DonutChart({ segments, size = 120, stroke = 22, children }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const total = segments.reduce((s, x) => s + x.amount, 0) || 1;
  const gap = segments.length > 1 ? 1.5 : 0;

  const arcs = [];
  let offset = 0;
  for (const segment of segments) {
    const length = (segment.amount / total) * c;
    arcs.push({ ...segment, dash: Math.max(length - gap, length / 2), offset });
    offset += length;
  }

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90" aria-hidden="true">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#EEF5EA" strokeWidth={stroke} />
        {arcs.map((a) => (
          <circle
            key={a.key}
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={a.color}
            strokeWidth={stroke}
            strokeDasharray={`${a.dash} ${c}`}
            strokeDashoffset={-a.offset}
          />
        ))}
      </svg>
      {children && (
        <div className="absolute flex flex-col items-center justify-center text-center wrap-anywhere" style={{ inset: stroke }}>{children}</div>
      )}
    </div>
  );
}

export function ChartLegend({ segments, showAmount = false, formatMoney }) {
  return (
    <ul className="flex flex-col gap-2 min-w-0 flex-1">
      {segments.map((s) => (
        <li key={s.key} className="flex items-center gap-2 text-[13px] font-bold text-text-soft min-w-0">
          <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: s.color }} />
          <span className="wrap-anywhere">{s.label}</span>
          <span className="ml-auto num text-text text-right shrink-0">
            {showAmount && formatMoney ? `${formatMoney(s.amount)} · ` : ''}
            {s.percent}%
          </span>
        </li>
      ))}
    </ul>
  );
}
