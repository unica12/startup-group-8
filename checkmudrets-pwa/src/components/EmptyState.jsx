import Mascot from './Mascot';

export default function EmptyState({ title, text, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-6 text-center gap-3">
      <Mascot size={88} className="mb-1" />
      <h3 className="text-lg">{title}</h3>
      {text && <p className="text-text-soft text-sm max-w-[260px]">{text}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
