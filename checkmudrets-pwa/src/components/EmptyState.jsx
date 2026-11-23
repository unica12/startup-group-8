import { PackageOpen } from 'lucide-react';

export default function EmptyState({ icon: Icon = PackageOpen, title, text }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-8 text-center gap-3">
      <Icon size={48} className="text-text-secondary/40" strokeWidth={1.5} />
      <h3 className="text-lg font-semibold text-text">{title}</h3>
      {text && <p className="text-text-secondary text-sm">{text}</p>}
    </div>
  );
}
