import { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Lightbulb } from 'lucide-react';
import { getStats, getAdvice } from '../services/api';
import { currentMonthIndex, formatExactMoney, MONTHS_NOMINATIVE, toChartSegments } from '../utils/format';
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

export default function Stats({ onNavigate, period, onPeriodChange, receiptsRevision, adviceOpened, onOpenAdvice }) {
  const currentMonth = currentMonthIndex();
  const selectedMonth = period?.month ?? currentMonth;
  const allTime = period?.allTime ?? false;
  const [statsResult, setStatsResult] = useState(null);
  const [attempt, setAttempt] = useState(0);
  const [adviceResult, setAdviceResult] = useState(null);
  const [adviceAttempt, setAdviceAttempt] = useState(0);
  const year = Math.floor(selectedMonth / 12);
  const month = selectedMonth % 12;
  const monthStr = `${year}-${String(month + 1).padStart(2, '0')}`;
  const requestedPeriod = allTime ? 'all' : monthStr;
  const isCurrentMonth = selectedMonth === currentMonth;
  const statsKey = `${requestedPeriod}:${attempt}:${receiptsRevision}`;
  const adviceKey = `${adviceAttempt}:${receiptsRevision}`;
  const result = statsResult?.key === statsKey ? statsResult : null;
  const advice = adviceResult?.key === adviceKey ? adviceResult : null;

  useEffect(() => {
    const controller = new AbortController();
    getStats(requestedPeriod, controller.signal)
      .then((stats) => {
        if (!controller.signal.aborted) setStatsResult({ key: statsKey, stats });
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatsResult({ key: statsKey, error: true });
      });
    return () => controller.abort();
  }, [requestedPeriod, statsKey]);

  useEffect(() => {
    if (!adviceOpened) return;
    const controller = new AbortController();
    const { signal } = controller;
    getAdvice({ personalize: true, signal }).then((data) => {
      if (!signal.aborted) setAdviceResult({ key: adviceKey, data });
    }).catch(() => {
      if (!signal.aborted) setAdviceResult({ key: adviceKey, error: true });
    });
    return () => controller.abort();
  }, [adviceOpened, adviceKey]);

  function retry() {
    setAttempt((value) => value + 1);
  }

  const stats = result?.stats;
  const segments = stats ? toChartSegments(stats.by_category, 6) : [];

  return (
    <div className="px-4 pt-5 pb-6 max-w-lg mx-auto flex flex-col gap-4">
      <h1 className="text-[28px]">Статистика</h1>

      <div className="grid grid-cols-2 gap-2" role="group" aria-label="Период статистики">
        <Button size="sm" variant={allTime ? 'secondary' : 'ghost'} aria-pressed={!allTime}
          onClick={() => onPeriodChange({ month: selectedMonth, allTime: false })}>По месяцам</Button>
        <Button size="sm" variant={allTime ? 'ghost' : 'secondary'} aria-pressed={allTime}
          onClick={() => onPeriodChange({ month: selectedMonth, allTime: true })}>За всё время</Button>
      </div>
      {!allTime && <Card padding="p-1.5" className="flex items-center justify-between">
        <Button size="sm" variant="ghost" onClick={() => onPeriodChange({ month: selectedMonth - 1, allTime: false })} aria-label="Предыдущий месяц">
          <ChevronLeft size={20} aria-hidden="true" />
        </Button>
        <span className="font-extrabold" aria-live="polite">{MONTHS_NOMINATIVE[month]} {year}</span>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => onPeriodChange({ month: selectedMonth + 1, allTime: false })}
          disabled={isCurrentMonth}
          aria-label="Следующий месяц"
        >
          <ChevronRight size={20} aria-hidden="true" />
        </Button>
      </Card>}

      {!result ? (
        <Loader text="Загружаем статистику..." />
      ) : result.error ? (
        <ErrorState message="Не удалось загрузить статистику за выбранный период." onRetry={retry} />
      ) : stats.receipts_count === 0 ? (
        <EmptyState
          title={allTime ? 'Чеков пока нет' : 'Нет данных за этот месяц'}
          text="Сфоткай чеки, чтобы увидеть, куда уходят деньги"
          action={isCurrentMonth && <Button onClick={() => onNavigate('scan')}>Сфоткать чек</Button>}
        />
      ) : (
        <>
          <div className="grid grid-cols-3 gap-2.5">
            <Metric label="Потрачено" value={formatExactMoney(stats.total_spent)} />
            <Metric label="Чеков" value={stats.receipts_count} />
            <Metric label="Средний чек" value={formatExactMoney(stats.average_receipt)} />
          </div>

          <Card as="section">
            <h2><Tag>Структура расходов</Tag></h2>
            {segments.length ? (
              <div className="flex flex-col items-center gap-5 mt-4">
                <DonutChart segments={segments} size={176} stroke={28}>
                  <span className="text-[11px] font-bold text-text-muted">Всего</span>
                  <span className="num max-w-full text-[19px] font-extrabold tracking-[-0.04em]">{formatExactMoney(stats.total_spent)}</span>
                </DonutChart>
                <div className="w-full">
                  <ChartLegend segments={segments} showAmount formatMoney={formatExactMoney} />
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
                    <span className="num font-extrabold text-right wrap-anywhere">{formatExactMoney(amount)}</span>
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
              <span className="num ml-auto font-extrabold text-right wrap-anywhere">{formatExactMoney(stats.largest_purchase.amount)}</span>
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
        {!adviceOpened && <Button variant="ghost" onClick={onOpenAdvice}><Lightbulb size={18} /> Открыть финансовые инсайты</Button>}
        {adviceOpened && !advice && <Loader text="Подбираем рекомендации..." />}
        {advice?.error && <ErrorState message="Не удалось загрузить инсайты." onRetry={() => setAdviceAttempt((value) => value + 1)} />}
        {advice?.data && <InsightList data={advice.data} />}
      </section>
    </div>
  );
}
