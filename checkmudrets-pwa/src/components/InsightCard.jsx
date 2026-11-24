import { Lightbulb } from 'lucide-react';
import { formatDecimal } from '../utils/format';
import Mascot from './Mascot';
import { Card } from './ui';

export function InsightCard({ insight }) {
  const { title, metric, observation, evidence, recommendation } = insight;
  const financial = metric.unit.startsWith('₽');
  const note = insight.type === 'forecast' ? 'Прогноз зависит от полноты истории.'
    : insight.type === 'savings' || insight.type === 'store_comparison' || insight.type === 'unit_price'
      ? 'Цены из истории покупок.' : null;
  return (
    <Card as="article" padding="p-4" className="min-w-0">
      <div className="flex items-start gap-2.5">
        <span className="rounded-xl bg-pill text-brand p-2 shrink-0"><Lightbulb size={17} aria-hidden="true" /></span>
        <div className="min-w-0">
          <h3 className="text-base wrap-anywhere">{title}</h3>
          <p className="text-xs text-text-muted mt-0.5">{metric.label}</p>
        </div>
      </div>
      <p className={`num inline-block rounded-full px-3 py-1 mt-3 text-sm font-extrabold wrap-anywhere ${financial ? 'bg-coin/40 text-coin-text' : 'bg-pill text-text'}`}>
        {formatDecimal(metric.value)} {metric.unit}
      </p>
      <p className="mt-2 text-sm leading-snug wrap-anywhere">{observation}</p>
      <ul className="mt-2 grid gap-1 text-xs text-text-soft wrap-anywhere">
        {evidence.map((line, index) => <li key={index}>{line}</li>)}
      </ul>
      {note && <p className="mt-2 text-xs text-text-muted">{note}</p>}
      <p className="mt-3 text-sm font-bold leading-snug text-brand wrap-anywhere">{recommendation}</p>
    </Card>
  );
}

export default function InsightList({ data, limit }) {
  if (!data.insights.length) {
    return (
      <Card className="flex gap-3 items-center" padding="p-4">
        <Mascot size={45} withLines={false} className="shrink-0" />
        <p className="text-sm text-text-soft">{data.empty_message}</p>
      </Card>
    );
  }
  return <div className="grid gap-3">{data.insights.slice(0, limit).map((insight) => <InsightCard key={insight.type} insight={insight} />)}</div>;
}
