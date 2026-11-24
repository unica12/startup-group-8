import Mascot from './Mascot';

export default function Logo({ size = 'md' }) {
  const small = size === 'sm';
  return (
    <span className="inline-flex items-center gap-2">
      <span
        className={`inline-flex items-center justify-center rounded-[12px] bg-green shadow-[0_3px_0_#46A302] ${small ? 'w-8 h-8' : 'w-10 h-10'}`}
      >
        <Mascot size={small ? 20 : 24} hat="#2E7D32" />
      </span>
      <span className={`font-extrabold tracking-[-0.04em] ${small ? 'text-base' : 'text-lg'}`}>
        <span className="text-text">Чек</span>
        <span className="text-green">Мудрец</span>
      </span>
    </span>
  );
}
