import { useState, useEffect } from 'react';
import { getReport, getReceipts } from '../services/api';
import { TrendingUp, TrendingDown, Receipt, Sparkles, ArrowRight, Camera } from 'lucide-react';
import Loader from '../components/Loader';

const CATEGORY_EMOJI = {
  'Продукты': '🍞', 'Молочные': '🥛', 'Мясо': '🥩', 'Овощи/Фрукты': '🥬',
  'Хлеб': '🍞', 'Напитки': '🧃', 'Алкоголь': '🍷', 'Кофе': '☕',
  'Сладости': '🍬', 'Снеки': '🍿', 'Готовая еда': '🥡', 'Бытовая химия': '🧹',
  'Гигиена': '🧴', 'Одежда': '👕', 'Электроника': '📱', 'Лекарства': '💊',
  'Транспорт': '🚗', 'Топливо': '⛽', 'Другое': '📦',
};

function formatMoney(n) {
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(n) + ' ₽';
}

export default function Home({ onNavigate, userName }) {
  const [report, setReport] = useState(null);
  const [lastReceipts, setLastReceipts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getReport().catch(() => null),
      getReceipts(3).catch(() => ({ receipts: [] })),
    ]).then(([rep, rec]) => {
      setReport(rep);
      setLastReceipts(rec?.receipts || []);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader text="Загружаем данные..." />;

  const greeting = userName ? `Привет, ${userName}!` : 'Привет!';
  const hasData = report && report.receipts_count > 0;

  return (
    <div className="px-4 pt-6 pb-4 max-w-lg mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-primary">{greeting}</h1>
          <p className="text-text-secondary text-sm mt-0.5">
            {hasData ? report.period?.label || 'Эта неделя' : 'Начни сканировать чеки'}
          </p>
        </div>
        <div className="w-10 h-10 rounded-full bg-accent/10 flex items-center justify-center">
          <Sparkles size={20} className="text-accent" />
        </div>
      </div>

      {/* Weekly summary card */}
      {hasData ? (
        <div className="bg-primary rounded-2xl p-5 text-white shadow-lg">
          <p className="text-sm opacity-80">Расходы за неделю</p>
          <p className="text-3xl font-bold mt-1">{formatMoney(report.total_spent)}</p>
          <div className="flex items-center gap-2 mt-2">
            {report.change_pct > 0 ? (
              <TrendingUp size={16} className="text-red-300" />
            ) : (
              <TrendingDown size={16} className="text-green-300" />
            )}
            <span className="text-sm opacity-90">{report.change_text}</span>
          </div>
          <div className="flex gap-2 mt-4 flex-wrap">
            {report.top_categories?.slice(0, 3).map((cat, i) => (
              <span key={i} className="bg-white/15 rounded-full px-3 py-1 text-xs">
                {cat.emoji} {cat.category}
              </span>
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-primary rounded-2xl p-6 text-white text-center shadow-lg">
          <Camera size={40} className="mx-auto mb-3 opacity-80" />
          <p className="font-semibold text-lg">Отсканируй первый чек</p>
          <p className="text-sm opacity-80 mt-1">И мы начнём анализировать расходы</p>
          <button
            onClick={() => onNavigate('scan')}
            className="mt-4 bg-accent hover:bg-accent-dark text-white font-semibold py-2.5 px-6 rounded-full transition-colors"
          >
            Сканировать чек
          </button>
        </div>
      )}

      {/* Quick actions */}
      <div className="grid grid-cols-2 gap-3">
        <button onClick={() => onNavigate('scan')} className="bg-card rounded-xl p-4 text-left shadow-sm border border-border hover:border-accent/40 transition-colors">
          <Camera size={22} className="text-accent mb-2" />
          <span className="text-sm font-medium">Сканировать чек</span>
        </button>
        <button onClick={() => onNavigate('stats')} className="bg-card rounded-xl p-4 text-left shadow-sm border border-border hover:border-accent/40 transition-colors">
          <TrendingUp size={22} className="text-accent mb-2" />
          <span className="text-sm font-medium">Статистика</span>
        </button>
      </div>

      {/* Last receipts */}
      {lastReceipts.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-text">Последние чеки</h2>
            <button onClick={() => onNavigate('history')} className="text-accent text-sm flex items-center gap-1">
              Все <ArrowRight size={14} />
            </button>
          </div>
          <div className="space-y-2">
            {lastReceipts.map((r) => (
              <div key={r.id} className="bg-card rounded-xl p-3.5 flex items-center gap-3 shadow-sm border border-border">
                <div className="w-10 h-10 rounded-full bg-accent/10 flex items-center justify-center shrink-0">
                  <Receipt size={18} className="text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{r.store_name || 'Чек'}</p>
                  <p className="text-xs text-text-secondary">
                    {r.items?.length || 0} поз. · {r.date || '—'}
                  </p>
                </div>
                <span className="text-sm font-semibold text-primary whitespace-nowrap">{formatMoney(r.total)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
