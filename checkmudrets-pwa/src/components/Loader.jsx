import Mascot from './Mascot';

/** mascot — анимированный маскот (для долгих операций вроде распознавания чека) */
export default function Loader({ text = 'Загрузка...', mascot = false, hint }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-4 text-center" role="status" aria-live="polite">
      {mascot ? (
        <Mascot size={96} className="mascot-bob" />
      ) : (
        <div className="w-10 h-10 border-4 border-pill border-t-green rounded-full animate-spin" />
      )}
      <span className="text-text font-bold text-[15px]">{text}</span>
      {hint && <span className="text-text-muted text-[13px] -mt-2 max-w-[260px]">{hint}</span>}
    </div>
  );
}
