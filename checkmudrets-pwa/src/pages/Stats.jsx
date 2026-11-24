import { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Lightbulb } from 'lucide-react';
import { getStats, getAdvice } from '../services/api';
import { formatMoney, MONTHS_NOMINATIVE, toChartSegments } from '../utils/format';
import Loader from '../components/Loader';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import Mascot from '../components/Mascot';
import InsightList from '../components/InsightCard';
import DonutChart, { ChartLegend } from '../components/DonutChart';
import { Button, Card, Tag } from '../components/ui';

function Metric({ label, value }) {
  return (
    <Card padding="p-3.5" className="text-center">
      <p className="text-[11px] font-bold text-text-muted">{label}</p>
      <p className="num text-[17px] font-extrabold tracking-[-0.03em] mt-0.5 leading-tight wrap-anywhere">{value}</p>
    </Card>
  );
}

export default function Stats({ onNavigate }) {
  const [currentMonth] = useState(() => {
    const now = new Date();
    return now.getFullYear() * 12 + now.getMonth();
  });
  const [selectedMonth, setSelectedMonth] = useState(currentMonth);
  const [result, setResult] = useState(null);
  const [attempt, setAttempt] = useState(0);
  const [advice, setAdvice] = useState(null);
  const year = Math.floor(selectedMonth / 12);
  const month = selectedMonth % 12;
  const monthStr = `${year}-${String(month + 1).padStart(2, '0')}`;
  const isCurrentMonth = selectedMonth === currentMonth;

  useEffect(() => {
    const controller = new AbortController();
    getStats(monthStr, controller.signal)
      .then((stats) => {
        if (!controller.signal.aborted) setResult({ stats });
      })
      .catch(() => {
        if (!controller.signal.aborted) setResult({ error: true });
      });
    return () => controller.abort();
  }, [monthStr, attempt]);

  function changeMonth(delta) {
    setResult(null);
    setSelectedMonth((value) => value + delta);
  }

  function retry() {
    setResult(null);
    setAttempt((value) => value + 1);
  }

  const loadAdvice = async () => {
    setAdvice({ loading: true });
    try {
      setAdvice({ data: await getAdvice({ personalize: true }) });
    } catch {
      setAdvice({ error: true });
    }
  };

  const stats = result?.stats;
  const segments = stats ? toChartSegments(stats.by_category, 6) : [];

  return (
    <div className="px-4 pt-5 pb-6 max-w-lg mx-auto flex flex-col gap-4">
      <h1 className="text-[28px]">Статистика</h1>

      <Card padding="p-1.5" className="flex items-center justify-between">
        <Button size="sm" variant="ghost" onClick={() => changeMonth(-1)} aria-label="Предыдущий месяц">
          <ChevronLeft size={20} aria-hidden="true" />
        </Button>
        <span className="font-extrabold" aria-live="polite">{MONTHS_NOMINATIVE[month]} {year}</span>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => changeMonth(1)}
          disabled={isCurrentMonth}
          aria-label="Следующий месяц"
        >
          <ChevronRight size={20} aria-hidden="true" />
        </Button>
      </Card>

      {!result ? (
        <Loader text="Загружаем статистику..." />
      ) : result.error ? (
        <ErrorState message="Не удалось загрузить статистику за этот месяц." onRetry={retry} />
      ) : stats.receipts_count === 0 ? (
        <EmptyState
          title="Нет данных за этот месяц"
          text="Сфоткай чеки, чтобы увидеть, куда уходят деньги"
          action={isCurrentMonth && <Button onClick={() => onNavigate('scan')}>Сфоткать чек</Button>}
        />
      ) : (
        <>
          <div className="grid grid-cols-3 gap-2.5">
            <Metric label="Потрачено" value={formatMoney(stats.total_spent)} />
            <Metric label="Чеков" value={stats.receipts_count} />
            <Metric label="Средний чек" value={formatMoney(stats.average_receipt)} />
          </div>

          <Card as="section">
            <h2><Tag>Структура расходов</Tag></h2>
            {segments.length ? (
              <div className="flex flex-col items-center gap-5 mt-4">
                <DonutChart segments={segments} size={176} stroke={28}>
                  <span className="text-[11px] font-bold text-text-muted">Всего</span>
                  <span className="num max-w-full text-[19px] font-extrabold tracking-[-0.04em]">{formatMoney(stats.total_spent)}</span>
                </DonutChart>
                <div className="w-full">
                  <ChartLegend segments={segments} showAmount formatMoney={formatMoney} />
                </div>
              </div>
            ) : <p className="mt-3 text-sm text-text-soft">Пока нет расходов по категориям.</p>}
          </Card>

          {stats.by_category.length > segments.length && (
            <Card as="section">
              <h2><Tag>Все категории</Tag></h2>
              <ul className="divide-y divide-line mt-3 text-sm">
                {stats.by_category.map(({ category, emoji, amount }) => (
                  <li key={category} className="flex items-center justify-between gap-3 py-2">
                    <span className="font-bold wrap-anywhere"><span aria-hidden="true">{emoji}</span> {category}</span>
                    <span className="num font-extrabold text-right wrap-anywhere">{formatMoney(amount)}</span>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {stats.largest_purchase && (
            <Card className="flex items-center gap-4">
              <span className="w-11 h-11 rounded-[14px] bg-coin/40 flex items-center justify-center shrink-0 text-lg" aria-hidden="true">🏆</span>
              <div className="min-w-0">
                <p className="text-[12px] font-bold text-text-muted">Самая дорогая покупка</p>
                <p className="font-extrabold text-[15px] wrap-anywhere">{stats.largest_purchase.name}</p>
              </div>
              <span className="num ml-auto font-extrabold text-right wrap-anywhere">{formatMoney(stats.largest_purchase.amount)}</span>
            </Card>
          )}

        </>
      )}
      <section className="grid gap-3">
        <div className="flex items-center gap-2">
          <Mascot size={40} withLines={false} className="shrink-0" />
          <div>
            <h2 className="text-xl">Финансовые инсайты</h2>
            <p className="text-xs text-text-soft">По истории покупок до сегодняшнего дня</p>
          </div>
        </div>
        {!advice && <Button variant="ghost" onClick={loadAdvice}><Lightbulb size={18} /> Открыть финансовые инсайты</Button>}
        {advice?.loading && <Loader text="Подбираем рекомендации..." />}
        {advice?.error && <ErrorState message="Не удалось загрузить инсайты." onRetry={loadAdvice} />}
        {advice?.data && <InsightList data={advice.data} />}
      </section>
    </div>
  );
}
