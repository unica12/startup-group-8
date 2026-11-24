/**
 * Маскот ЧекМудрец — чек-свиток с лицом и колпаком мудреца (SVG из лендинга).
 * withLines — зелёные «строки» чека под улыбкой (как в шапке лендинга).
 */
export default function Mascot({ size = 96, hat = '#58CC02', withLines = true, className = '', title }) {
  return (
    <svg
      width={size}
      height={size * (146 / 132)}
      viewBox="-6 -14 132 146"
      className={className}
      role={title ? 'img' : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
    >
      <path d="M 40 18 Q 60 -12 80 18 Z" fill={hat} />
      <path
        d="M 34 18 H 86 A 14 14 0 0 1 100 32 V 108 l -10 10 l -10 -10 l -10 10 l -10 -10 l -10 10 l -10 -10 l -10 10 l -10 -10 V 32 A 14 14 0 0 1 34 18 Z"
        fill="#FFFFFF"
        stroke="#2E7D32"
        strokeWidth="7"
        strokeLinejoin="round"
      />
      <rect x="34" y="12" width="52" height="11" rx="5.5" fill="#2E7D32" />
      <circle cx="48" cy="56" r="6" fill="#2E7D32" />
      <circle cx="72" cy="56" r="6" fill="#2E7D32" />
      <path d="M 50 76 Q 60 86 70 76" fill="none" stroke="#2E7D32" strokeWidth="5" strokeLinecap="round" />
      {withLines && (
        <>
          <rect x="38" y="92" width="40" height="6" rx="3" fill="#8BE04E" />
          <rect x="38" y="103" width="26" height="6" rx="3" fill="#8BE04E" />
        </>
      )}
    </svg>
  );
}
