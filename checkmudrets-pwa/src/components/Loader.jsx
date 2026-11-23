export default function Loader({ text = 'Загрузка...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3">
      <div className="w-10 h-10 border-4 border-accent/30 border-t-accent rounded-full animate-spin" />
      <span className="text-text-secondary text-sm">{text}</span>
    </div>
  );
}
