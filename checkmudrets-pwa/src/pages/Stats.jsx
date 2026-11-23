import { useState, useEffect } from 'react';
import { getStats, getAdvice } from '../services/api';
import { BarChart3, TrendingUp, Award, Lightbulb, ChevronLeft, ChevronRight } from 'lucide-react';
import Loader from '../components/Loader';
import EmptyState from '../components/EmptyState';

function formatMoney(n) {
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(n) + ' ₽';
}

const MONTHS_RU = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];

export default function Stats() {
  const [stats, setStats] = useState(null);
  const [advice, setAdvice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [adviceLoading, setAdviceLoading] = useState(false);
  const [showAdvice, setShowAdvice] = useState(false);

  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);

  const monthStr = `${year}-${String(month).padStart(2, '0')}`;

  useEffect(() => {
    setLoading(true);
    getStats(monthStr)
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, [monthStr]);

  const prevMonth = () => {
    if (month === 1) { setMonth(12); setYear(year - 1); }
    else setMonth(month - 1);
  };
  const nextMonth = () => {
    if (month === 12) { setMonth(1); setYear(year + 1); }
    else setMonth(month + 1);
  };

  const loadAdvice = async () => {
    setShowAdvice(true);
    setAdviceLoading(true);
    try {
      const res = await getAdvice();
      setAdvice(res.advice);
    } catch {
      setAdvice('Не удалось загрузить советы');
    } finally {
      setAdviceLoading(false);
    }
  };

  if (loading) return <Loader text="Загружаем статистику..." />;

  const hasData = stats && stats.total_spent > 0;
  const maxCat = stats?.by_category?.[0]?.amount || 1;

  return (
    <div className="px-4 pt-6 pb-4 max-w-lg mx-auto space-y-5">
      <h1 className="text-2xl font-bold text-primary">Статистика</h1>

      {/* Month selector */}
      <div className="flex items-center justify-between bg-card rounded-xl p-3 border border-border shadow-sm">
        <button onClick={prevMonth} className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors">
          <ChevronLeft size={20} className="text-text-secondary" />
        </button>
        <span className="font-semibold text-text">{MONTHS_RU[month - 1]} {year}</span>
        <button onClick={nextMonth} className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors">
          <ChevronRight size={20} className="text-text-secondary" />
        </button>
      </div>

      {!hasData ? (
        <EmptyState icon={BarChart3} title="Нет данных за этот месяц" text="Отсканируй чеки, чтобы увидеть статистику" />
      ) : (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-card rounded-xl p-3 border border-border shadow-sm text-center">
              <p className="text-xs text-text-secondary">Потрачено</p>
              <p className="text-lg font-bold text-primary mt-1">{formatMoney(stats.total_spent)}</p>
            </div>
            <div className="bg-card rounded-xl p-3 border border-border shadow-sm text-center">
              <p className="text-xs text-text-secondary">Чеков</p>
              <p className="text-lg font-bold text-primary mt-1">{stats.receipts_count}</p>
            </div>
            <div className="bg-card rounded-xl p-3 border border-border shadow-sm text-center">
              <p className="text-xs text-text-secondary">Ср. чек</p>
              <p className="text-lg font-bold text-primary mt-1">{formatMoney(stats.average_receipt)}</p>
            </div>
          </div>

          {/* Categories */}
          <div className="bg-card rounded-2xl border border-border shadow-sm p-4 space-y-3">
            <h3 className="font-semibold flex items-center gap-2">
              <BarChart3 size={18} className="text-accent" /> Расходы по категориям
            </h3>
            {stats.by_category?.map((cat, i) => (
              <div key={i} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>{cat.emoji} {cat.category}</span>
                  <span className="font-medium">{formatMoney(cat.amount)} <span className="text-text-secondary">({cat.percent}%)</span></span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent rounded-full transition-all duration-500"
                    style={{ width: `${(cat.amount / maxCat) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Largest purchase */}
          {stats.largest_purchase && (
            <div className="bg-card rounded-xl border border-border shadow-sm p-4 flex items-center gap-3">
              <Award size={24} className="text-warning shrink-0" />
              <div>
                <p className="text-xs text-text-secondary">Самая дорогая покупка</p>
                <p className="font-medium text-sm">{stats.largest_purchase.name}</p>
                <p className="text-sm text-primary font-semibold">{formatMoney(stats.largest_purchase.amount)}</p>
              </div>
            </div>
          )}

          {/* AI Advice */}
          {!showAdvice ? (
            <button
              onClick={loadAdvice}
              className="w-full bg-accent/10 hover:bg-accent/20 text-accent font-semibold py-3 rounded-xl flex items-center justify-center gap-2 transition-colors"
            >
              <Lightbulb size={18} /> Получить советы по экономии
            </button>
          ) : (
            <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Lightbulb size={18} className="text-warning" />
                <span className="font-semibold text-sm">ИИ-советы по экономии</span>
              </div>
              {adviceLoading ? (
                <Loader text="Генерируем советы..." />
              ) : (
                <p className="text-sm text-text whitespace-pre-line">{advice}</p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
