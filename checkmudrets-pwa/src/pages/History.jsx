import { useState, useEffect, useRef } from 'react';
import { ChevronDown } from 'lucide-react';
import { deleteReceipt, getReceipts, updateReceipt } from '../services/api';
import { formatExactMoney, formatDateShort, plural } from '../utils/format';
import Loader from '../components/Loader';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import ReceiptEditor from '../components/ReceiptEditor';
import { editorPayload, editSavedReceipt } from '../utils/receiptEditor';
import { Button, Card } from '../components/ui';

const PAGE_SIZE = 30;

function ReceiptCard({ receipt, userId, onEdit, onChanged }) {
  const [open, setOpen] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const deleting = useRef(false);
  const count = receipt.items?.length || 0;
  const date = receipt.date && formatDateShort(receipt.date);
  const scanDate = receipt.accounting_date !== receipt.date && receipt.accounting_date;

  async function remove() {
    if (deleting.current) return;
    deleting.current = true;
    setBusy(true);
    setError(null);
    try {
      await deleteReceipt(receipt.id, userId);
      onChanged('Чек удалён.');
    } catch (failure) {
      if (failure.status === 404) onChanged('Чек уже удалён.');
      else setError('Не удалось удалить чек. Попробуй ещё раз.');
    } finally {
      deleting.current = false;
      setBusy(false);
    }
  }

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
          {scanDate && <p className="text-xs text-text-muted">Учтён {formatDateShort(scanDate)}</p>}
        </div>
        <span className="num text-[15px] font-extrabold text-right wrap-anywhere">{formatExactMoney(receipt.total)}</span>
        <ChevronDown size={18} aria-hidden="true" className={`shrink-0 text-text-muted transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && count > 0 && (
        <ul className="border-t border-line divide-y divide-line px-4 bg-bg/60 rounded-b-card">
          {receipt.items.map((item) => (
            <li key={item.id ?? item.name} className="py-2.5 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-[14px] font-bold wrap-anywhere">{item.name}</p>
                <p className="text-[12px] text-text-muted">{item.category}{item.quantity != null && item.unit && ` · ${String(item.quantity).replace('.', ',')} ${item.unit}`}</p>
              </div>
              <span className="num text-[14px] font-bold text-right wrap-anywhere">{formatExactMoney(item.total)}</span>
            </li>
          ))}
        </ul>
      )}
      {open && count === 0 && <p className="px-4 pb-3 text-sm text-text-muted">В чеке нет распознанных позиций.</p>}
      {open && <div className="border-t border-line px-4 py-3 grid gap-2">
        {confirming ? (
          <>
            <p className="text-sm text-text-soft">Удалить чек и его позиции из истории?</p>
            {error && <ErrorState message={error} />}
            <div className="flex flex-wrap gap-2">
              <Button size="sm" variant="danger" disabled={busy} onClick={remove}>{busy ? 'Удаляем…' : 'Удалить чек'}</Button>
              <Button size="sm" variant="secondary" disabled={busy} onClick={() => { setConfirming(false); setError(null); }}>Отмена</Button>
            </div>
          </>
        ) : (
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="secondary" onClick={() => onEdit(receipt)}>Редактировать</Button>
            <Button size="sm" variant="ghost" className="text-danger" onClick={() => setConfirming(true)}>Удалить</Button>
          </div>
        )}
      </div>}
    </Card>
  );
}

function SavedReceiptEditor({ original, categories, userId, onCancel, onChanged }) {
  const [receipt, setReceipt] = useState(() => editSavedReceipt(original));
  const [warnings, setWarnings] = useState([]);
  const [acceptedWarnings, setAcceptedWarnings] = useState(false);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const saving = useRef(false);
  const nextKey = useRef(0);
  const start = useRef(null);

  useEffect(() => start.current?.focus(), []);

  function edit(next) {
    setReceipt(next);
    setAcceptedWarnings(false);
    setError(null);
  }

  async function save() {
    if (saving.current) return;
    saving.current = true;
    setBusy(true);
    setError(null);
    try {
      await updateReceipt(original.id, editorPayload(receipt), acceptedWarnings, userId);
      onChanged('Изменения сохранены.');
    } catch (failure) {
      if (failure.status === 404) {
        onChanged('Чек больше недоступен.');
        return;
      }
      const detail = failure.detail;
      if (Array.isArray(detail?.warnings)) {
        setWarnings(detail.warnings);
        setAcceptedWarnings(false);
      }
      setError(detail?.message || (failure.status === 422 ? 'Проверь формат сумм, количества и даты.' : 'Не удалось сохранить изменения. Попробуй ещё раз.'));
    } finally {
      saving.current = false;
      setBusy(false);
    }
  }

  return (
    <div ref={start} tabIndex={-1} className="min-w-0 outline-none">
      {original.accounting_date && original.date !== original.accounting_date && (
        <p className="mb-2 text-xs text-text-soft">Дата учёта этого чека · {formatDateShort(original.accounting_date)}</p>
      )}
      <ReceiptEditor receipt={receipt} categories={categories} warnings={warnings} acceptedWarnings={acceptedWarnings}
        onAcceptWarnings={setAcceptedWarnings} busy={busy} error={error} onEdit={edit} onConfirm={save} onReset={onCancel}
        onAdd={() => edit({ ...receipt, items: [...receipt.items, { editorKey: `new-${nextKey.current++}` }] })} />
    </div>
  );
}

function ReceiptHistory({ onNavigate, userId, onChanged }) {
  const [result, setResult] = useState(null);
  const [attempt, setAttempt] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    getReceipts(PAGE_SIZE, controller.signal, offset)
      .then(({ receipts, total_count, categories }) => {
        if (!controller.signal.aborted) {
          setResult((previous) => ({
            receipts: offset ? [...new Map([...previous.receipts, ...receipts].map((receipt) => [receipt.id, receipt])).values()] : receipts,
            total: total_count,
            next: receipts.length < PAGE_SIZE ? total_count : offset + receipts.length,
            categories: categories || [],
          }));
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) setFailed(true);
      }).finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [attempt, offset]);

  function retry() {
    setFailed(false);
    setLoading(true);
    setAttempt((value) => value + 1);
  }

  if (selected) {
    return <SavedReceiptEditor original={selected} categories={result.categories} userId={userId}
      onCancel={() => setSelected(null)} onChanged={onChanged} />;
  }

  return (
    <>
      {result && <p className="text-sm text-text-soft">За всё время · {result.total} {plural(result.total, ['чек', 'чека', 'чеков'])}</p>}
      {result?.receipts.length === 0 && (
        <EmptyState
          title="Чеков пока нет"
          text="Сфоткай первый чек — он появится здесь"
          action={<Button onClick={() => onNavigate('scan')}>Сфоткать чек</Button>}
        />
      )}
      {result?.receipts.map((receipt) => (
        <ReceiptCard key={receipt.id} userId={userId} receipt={receipt} onEdit={setSelected} onChanged={onChanged} />
      ))}
      {failed && <ErrorState message="Не удалось загрузить историю чеков." onRetry={retry} />}
      {loading && <Loader text="Загружаем историю..." />}
      {result && result.next < result.total && !loading && !failed && (
        <Button variant="secondary" onClick={() => { setLoading(true); setOffset(result.next); }}>Показать ещё</Button>
      )}
    </>
  );
}

export default function History({ onNavigate, userId, receiptsRevision, onReceiptsChanged }) {
  const [notice, setNotice] = useState('');
  function changed(message) {
    setNotice(message);
    onReceiptsChanged();
  }

  return (
    <div className="px-4 pt-5 pb-6 max-w-lg mx-auto flex flex-col gap-3">
      <h1 className="text-[28px] mb-1">История чеков</h1>
      {notice && <p className="rounded-input bg-pill px-3 py-2 text-sm font-bold text-brand" role="status">{notice}</p>}
      <ReceiptHistory key={receiptsRevision} userId={userId} onNavigate={onNavigate} onChanged={changed} />
    </div>
  );
}
