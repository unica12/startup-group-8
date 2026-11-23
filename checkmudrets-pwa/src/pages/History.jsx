import { useState, useEffect } from 'react';
import { getReceipts } from '../services/api';
import { Receipt, ChevronDown, ChevronUp, ShoppingBag } from 'lucide-react';
import Loader from '../components/Loader';
import EmptyState from '../components/EmptyState';

function formatMoney(n) {
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(n) + ' ₽';
}

function ReceiptCard({ receipt }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="bg-card rounded-xl border border-border shadow-sm overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full px-4 py-3.5 flex items-center gap-3 text-left">
        <div className="w-10 h-10 rounded-full bg-accent/10 flex items-center justify-center shrink-0">
          <Receipt size={18} className="text-accent" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm truncate">{receipt.store_name || 'Чек'}</p>
          <p className="text-xs text-text-secondary">
            {receipt.date || '—'} · {receipt.items?.length || 0} поз.
          </p>
        </div>
        <span className="text-sm font-semibold text-primary whitespace-nowrap mr-1">
          {formatMoney(receipt.total)}
        </span>
        {open ? <ChevronUp size={16} className="text-text-secondary" /> : <ChevronDown size={16} className="text-text-secondary" />}
      </button>
      {open && receipt.items?.length > 0 && (
        <div className="border-t border-border divide-y divide-border">
          {receipt.items.map((item, i) => (
            <div key={i} className="px-4 py-2 flex items-center justify-between text-sm">
              <div className="flex-1 min-w-0 mr-2">
                <span className="truncate block">{item.name}</span>
                <span className="text-xs text-text-secondary">{item.category}</span>
              </div>
              <span className="font-medium whitespace-nowrap">{formatMoney(item.total)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function History() {
  const [receipts, setReceipts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getReceipts(50)
      .then((data) => setReceipts(data.receipts || []))
      .catch(() => setReceipts([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader text="Загружаем историю..." />;

  return (
    <div className="px-4 pt-6 pb-4 max-w-lg mx-auto space-y-3">
      <h1 className="text-2xl font-bold text-primary">История чеков</h1>
      {receipts.length === 0 ? (
        <EmptyState icon={ShoppingBag} title="Нет чеков" text="Отсканируй первый чек, и он появится здесь" />
      ) : (
        receipts.map((r) => <ReceiptCard key={r.id} receipt={r} />)
      )}
    </div>
  );
}
