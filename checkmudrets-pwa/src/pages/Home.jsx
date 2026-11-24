import { useState, useEffect } from 'react';
import { ChevronRight } from 'lucide-react';
import { getStats, getReceipts, getReport, getAdvice } from '../services/api';
import { formatMoney, monthAccusative, formatDateShort, plural, toChartSegments } from '../utils/format';
import Loader from '../components/Loader';
import ErrorState from '../components/ErrorState';
import Mascot from '../components/Mascot';
import Logo from '../components/Logo';
import InsightList from '../components/InsightCard';
import DonutChart, { ChartLegend } from '../components/DonutChart';
import { Button, Card, Tag } from '../components/ui';

function currentMonth() {
  const d = new Date();
  return { str: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`, index: d.getMonth() };
}

export default function Home({ onNavigate, userName }) {
  const [{ str: month, index: monthIndex }] = useState(currentMonth);
  const [data, setData] = useState(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const { signal } = controller;
    Promise.allSettled([getStats(month, signal), getReceipts(3, signal), getReport(signal), getAdvice({ signal })])
      .then(([stats, receipts, report, advice]) => {
        if (!signal.aborted) {
          setData({ stats: stats.value, receipts: receipts.value?.receipts, report: report.value, advice: advice.value });
        }
      });
    return () => controller.abort();
  }, [month, attempt]);

  function retry() {
    setData(null);
    setAttempt((value) => value + 1);
  }

  const { stats, receipts, report, advice } = data || {};
  const segments = stats ? toChartSegments(stats.by_category, 4) : [];
  const weekSummary = report?.receipts_count > 0
    ? `За неделю потрачено ${formatMoney(report.total_spent)}.${report.change_pct ? ` ${report.change_text}` : ''}`
    : '';
  const failedSections = [
    !stats && 'расходы за месяц',
    !receipts && 'последние чеки',
    !report && 'сводку за неделю',
    !advice && 'финансовые инсайты',
  ].filter(Boolean);

  return (
    <div className="px-4 pt-5 pb-6 max-w-lg mx-auto flex flex-col gap-4">
      <header className="flex items-center justify-between">
        <Logo size="sm" />
        {userName && <span className="text-[13px] font-bold text-text-muted truncate max-w-[45%]">Привет, {userName}!</span>}
      </header>
      <h1 className="text-[28px] mt-1">Мой бюджет</h1>

      {!data && <Loader text="Загружаем бюджет..." />}
      {data && failedSections.length > 0 && (
        <ErrorState message={`Не удалось загрузить ${failedSections.join(', ')}.`} onRetry={retry} />
      )}

      {stats && (
        <section className="rounded-card bg-green p-5 shadow-[0_5px_0_#46A302]">
          <h2 className="text-sm tracking-normal">Расходы за {monthAccusative(monthIndex)}</h2>
          <p className="num text-[36px] font-extrabold tracking-[-0.045em] leading-tight mt-1 wrap-anywhere">
            {formatMoney(stats.total_spent)}
          </p>
          <span className="num inline-block mt-3 rounded-full bg-white/30 px-3 py-1 text-xs font-extrabold">
            {stats.receipts_count > 0
              ? `${stats.receipts_count} ${plural(stats.receipts_count, ['чек', 'чека', 'чеков'])} · средний чек ${formatMoney(stats.average_receipt)}`
              : 'В этом месяце чеков пока нет'}
          </span>
        </section>
      )}

      {segments.length > 0 && (
        <Card as="section">
          <div className="flex items-center justify-between gap-2 mb-3">
            <h2><Tag>По категориям</Tag></h2>
            <Button size="sm" variant="ghost" onClick={() => onNavigate('stats')} aria-label="Открыть статистику по категориям">
              <ChevronRight size={16} aria-hidden="true" />
            </Button>
          </div>
          <div className="flex items-center gap-4">
            <DonutChart segments={segments} size={112} stroke={20} />
            <ChartLegend segments={segments} />
          </div>
        </Card>
      )}
      {stats && segments.length === 0 && (
        <Card className="flex items-center gap-4">
          <Mascot size={56} className="shrink-0" />
          <div>
            <h2 className="text-[15px] leading-snug">Пока нет расходов по категориям</h2>
            <p className="text-text-soft text-[13px] leading-snug mt-1">Сфоткай чек, чтобы увидеть, куда уходят деньги.</p>
          </div>
        </Card>
      )}

      {receipts && (
        <Card as="section">
          <div className="flex items-center justify-between mb-2">
            <h2><Tag>Последние чеки</Tag></h2>
            {receipts.length > 0 && (
              <Button size="sm" variant="ghost" onClick={() => onNavigate('history')}>
                Все <ChevronRight size={16} aria-hidden="true" />
              </Button>
            )}
          </div>
          {receipts.length > 0 ? (
            <ul className="divide-y divide-line">
              {receipts.map((receipt) => (
                <li key={receipt.id} className="flex items-center justify-between gap-3 py-2.5">
                  <div className="min-w-0">
                    <p className="text-[15px] font-bold truncate">{receipt.store_name || 'Чек'}</p>
                    {receipt.date && <p className="text-xs text-text-muted">{formatDateShort(receipt.date)}</p>}
                  </div>
                  <span className="num text-[15px] font-extrabold text-right wrap-anywhere">{formatMoney(receipt.total)}</span>
                </li>
              ))}
            </ul>
          ) : <p className="text-sm text-text-soft">Чеков пока нет.</p>}
        </Card>
      )}

      {weekSummary && (
        <section aria-label="Сводка за неделю" className="rounded-input bg-pill p-4 flex items-center gap-3">
          <Mascot size={44} withLines={false} className="shrink-0" />
          <p className="text-[13.5px] font-extrabold text-brand leading-snug wrap-anywhere">{weekSummary}</p>
        </section>
      )}
      {advice && (
        <section className="grid gap-3">
          <h2 className="text-xl">Финансовые инсайты</h2>
          <InsightList data={advice} limit={2} />
          {advice.insights.length > 0 && <Button variant="ghost" onClick={() => onNavigate('stats')}>К статистике</Button>}
        </section>
      )}
    </div>
  );
}
