import { Home, Camera, Clock, BarChart3, User } from 'lucide-react';

const tabs = [
  { id: 'home', label: 'Главная', icon: Home },
  { id: 'history', label: 'История', icon: Clock },
  { id: 'scan', label: 'Скан', icon: Camera, accent: true },
  { id: 'stats', label: 'Статистика', icon: BarChart3 },
  { id: 'profile', label: 'Профиль', icon: User },
];

export default function BottomNav({ current, onChange }) {
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-border safe-bottom z-50">
      <div className="flex justify-around items-center h-16 max-w-lg mx-auto">
        {tabs.map(({ id, label, icon: Icon, accent }) => {
          const active = current === id;
          if (accent) {
            return (
              <button
                key={id}
                onClick={() => onChange(id)}
                className="flex flex-col items-center justify-center -mt-6"
              >
                <div className={`w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-all ${
                  active ? 'bg-accent scale-110' : 'bg-accent'
                }`}>
                  <Icon size={26} className="text-white" strokeWidth={2.5} />
                </div>
                <span className="text-[10px] mt-0.5 text-accent font-semibold">{label}</span>
              </button>
            );
          }
          return (
            <button
              key={id}
              onClick={() => onChange(id)}
              className="flex flex-col items-center justify-center gap-0.5 py-1 px-3 transition-colors"
            >
              <Icon
                size={22}
                className={active ? 'text-accent' : 'text-text-secondary'}
                strokeWidth={active ? 2.5 : 1.8}
              />
              <span className={`text-[10px] ${active ? 'text-accent font-semibold' : 'text-text-secondary'}`}>
                {label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
