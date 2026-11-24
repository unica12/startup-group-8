import { useState, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';
import { getReceipts } from '../services/api';
import { formatMoney, formatDateShort, plural } from '../utils/format';
import Loader from '../components/Loader';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import { Button, Card } from '../components/ui';

function ReceiptCard({ receipt }) {
  const [open, setOpen] = useState(false);
  const count = receipt.items?.length || 0;
  const date = receipt.date && formatDateShort(receipt.date);

  return (
    <Card padding="p-0">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="w-full px-4 py-3.5 flex items-center gap-3 text-left rounded-card cursor-pointer focus-visible:-outline-offset-4"
      >
        <span className="w-11 h-11 rounded-[14px] bg-pill flex items-center justify-center shrink-0 text-lg" aria-hidden="true">
          🧾
        </span>
        <div className="flex-1 min-w-0">
          <p className="font-extrabold text-[15px] leading-snug wrap-anywhere">{receipt.store_name || 'Чек'}</p>
          <p className="text-[12px] text-text-muted num">
            {date && `${date} · `}{count} {plural(count, ['позиция', 'позиции', 'позиций'])}
          </p>
        </div>
        <span className="num text-[15px] font-extrabold text-right wrap-anywhere">{formatMoney(receipt.total)}</span>
        <ChevronDown size={18} aria-hidden="true" className={`shrink-0 text-text-muted transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && count > 0 && (
        <ul className="border-t border-line divide-y divide-line px-4 bg-bg/60 rounded-b-card">
          {receipt.items.map((item) => (
            <li key={item.id ?? item.name} className="py-2.5 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-[14px] font-bold wrap-anywhere">{item.name}</p>
                <p className="text-[12px] text-text-muted">{item.category}</p>
              </div>
              <span className="num text-[14px] font-bold text-right wrap-anywhere">{formatMoney(item.total)}</span>
            </li>
          ))}
        </ul>
      )}
      {open && count === 0 && <p className="px-4 pb-3 text-sm text-text-muted">В чеке нет распознанных позиций.</p>}
    </Card>
  );
}

export default function History({ onNavigate }) {
  const [result, setResult] = useState(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    getReceipts(50, controller.signal)
      .then(({ receipts }) => setResult({ receipts }))
      .catch(() => {
        if (!controller.signal.aborted) setResult({ error: true });
      });
    return () => controller.abort();
  }, [attempt]);

  function retry() {
    setResult(null);
    setAttempt((value) => value + 1);
  }

  return (
    <div className="px-4 pt-5 pb-6 max-w-lg mx-auto flex flex-col gap-3">
      <h1 className="text-[28px] mb-1">История чеков</h1>
      {!result ? (
        <Loader text="Загружаем историю..." />
      ) : result.error ? (
        <ErrorState message="Не удалось загрузить историю чеков." onRetry={retry} />
      ) : result.receipts.length === 0 ? (
        <EmptyState
          title="Чеков пока нет"
          text="Сфоткай первый чек — он появится здесь"
          action={<Button onClick={() => onNavigate('scan')}>Сфоткать чек</Button>}
        />
      ) : (
        result.receipts.map((receipt) => <ReceiptCard key={receipt.id} receipt={receipt} />)
      )}
    </div>
  );
}
