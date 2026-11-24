export default function Tag({ className = '', children }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full bg-pill text-text-muted
        text-[10px] font-extrabold uppercase tracking-[0.14em] px-3.5 py-1.5 leading-none ${className}`}
    >
      {children}
    </span>
  );
}
