import { Home, Camera, Clock, PieChart, User } from 'lucide-react';

const tabs = [
  { id: 'home', label: 'Главная', icon: Home },
  { id: 'history', label: 'История', icon: Clock },
  { id: 'scan', label: 'Скан', icon: Camera, accent: true },
  { id: 'stats', label: 'Статистика', icon: PieChart },
  { id: 'profile', label: 'Профиль', icon: User },
];

export default function BottomNav({ current, onChange }) {
  return (
    <nav aria-label="Основная навигация" className="relative shrink-0 bg-surface border-t border-line safe-bottom">
      <div className="grid grid-cols-5 grid-rows-1 items-end h-14 max-w-lg mx-auto px-1">
        {tabs.map(({ id, label, icon: Icon, accent }) => {
          const active = current === id;
          if (accent) {
            return (
              <button
                key={id}
                type="button"
                onClick={() => onChange(id)}
                aria-label="Скан — сфоткать чек"
                aria-current={active ? 'page' : undefined}
                className="flex flex-col items-center justify-end pb-0.5 mx-auto rounded-full cursor-pointer"
              >
                <span
                  className="w-[58px] h-[58px] rounded-full bg-green flex items-center justify-center
                    shadow-[0_5px_0_#46A302] transition-transform duration-100
                    active:translate-y-[3px] active:shadow-[0_2px_0_#46A302]"
                >
                  <Icon size={26} className="text-text" strokeWidth={2.5} aria-hidden="true" />
                </span>
                <span className={`text-[10px] mt-1.5 font-extrabold ${active ? 'text-brand' : 'text-text-muted'}`}>
                  {label}
                </span>
              </button>
            );
          }
          return (
            <button
              key={id}
              type="button"
              onClick={() => onChange(id)}
              aria-current={active ? 'page' : undefined}
              className="flex min-h-11 flex-col items-center justify-center gap-0.5 rounded-btn cursor-pointer"
            >
              <Icon size={22} className={active ? 'text-brand' : 'text-text-muted'} strokeWidth={active ? 2.5 : 1.9} aria-hidden="true" />
              <span className={`text-[10px] ${active ? 'text-brand font-extrabold' : 'text-text-muted font-semibold'}`}>
                {label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
