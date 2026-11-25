import { useId, useState } from 'react';
import { Plus, RefreshCw, Trash2 } from 'lucide-react';
import { formatExactMoney } from '../utils/format';
import { cents } from '../utils/receiptEditor';
import ErrorState from './ErrorState';
import { Button, Card, Input } from './ui';

const UNITS = [['шт', 'Штуки'], ['кг', 'Килограммы'], ['г', 'Граммы'], ['л', 'Литры'], ['мл', 'Миллилитры']];

function Select({ label, value, onChange, options, placeholder }) {
  const id = useId();
  return (
    <div className="grid gap-1.5 min-w-0">
      <label htmlFor={id} className="text-[13.5px] font-extrabold">{label}</label>
      <select id={id} value={value ?? ''} onChange={(event) => onChange(event.target.value)} className="w-full min-w-0 rounded-input bg-bg border-2 border-bg px-3 py-3.5 text-base focus:border-green">
        <option value="">{placeholder}</option>
        {options.map(([key, name]) => <option key={key} value={key}>{name}</option>)}
      </select>
    </div>
  );
}

function ItemEditor({ item, index, categories, onEdit, onRemove }) {
  const [initiallyOpen] = useState(() => index === 0 || !item.name);
  const field = (key) => ({
    value: item[key] ?? '',
    onChange: (event) => onEdit({ ...item, [key]: event.target.value }),
  });
  return (
    <Card as="details" open={initiallyOpen || undefined} padding="p-4" className="min-w-0">
      <summary className="cursor-pointer text-sm font-extrabold wrap-anywhere">
        {item.name || `Позиция ${index + 1}`}
        {cents(item.total) !== null && <span className="text-brand ml-2">{formatExactMoney(cents(item.total) / 100)}</span>}
      </summary>
      <div className="grid gap-3 mt-3">
        {item.raw_name && item.raw_name !== item.name && <p className="text-xs text-text-muted wrap-anywhere">На чеке «{item.raw_name}»</p>}
        <Input label="Название товара" maxLength={256} {...field('name')} />
        <div className="grid grid-cols-2 gap-2 min-w-0">
          <Input label="Количество" inputMode="decimal" {...field('quantity')} />
          <Select label="Единица" value={item.unit} onChange={(unit) => onEdit({ ...item, unit })} options={UNITS} placeholder="Неизвестно" />
          <Input label="Цена за единицу, ₽" inputMode="decimal" {...field('price')} />
          <Input label="Оплачено, ₽" inputMode="decimal" {...field('total')} />
        </div>
        <Select label="Категория" value={item.category} onChange={(category) => onEdit({ ...item, category })}
          options={categories.map((category) => [category, category])} placeholder="Выбери категорию" />
        <details className="rounded-input border border-line px-3 py-2">
          <summary className="cursor-pointer text-sm font-bold">Бренд, упаковка и скидка</summary>
          <div className="grid gap-2 mt-3">
            <Input label="Бренд" maxLength={128} {...field('brand')} />
            <div className="grid grid-cols-2 gap-2">
              <Input label="Размер упаковки" inputMode="decimal" {...field('package_size')} />
              <Select label="Единица упаковки" value={item.package_unit}
                onChange={(package_unit) => onEdit({ ...item, package_unit })} options={UNITS.slice(1)} placeholder="Неизвестно" />
            </div>
            <Input label="Скидка на позицию, ₽" inputMode="decimal" {...field('discount')} />
          </div>
        </details>
        <Button variant="secondary" size="sm" onClick={onRemove} className="justify-self-start text-danger">
          <Trash2 size={16} aria-hidden="true" /> Удалить позицию
        </Button>
      </div>
    </Card>
  );
}

// При редактировании форма остаётся доступной, пока сервер сверяет итог на подтверждении.
export default function ReceiptEditor({
  receipt, categories, warnings, retried, error, busy, onEdit, onAdd, onRepeat, onReset, onConfirm,
  acceptedWarnings, onAcceptWarnings, photo,
}) {
  const amounts = receipt.items.map((line) => cents(line.total));
  const subtotal = amounts.length && amounts.every((amount) => amount !== null)
    ? amounts.reduce((sum, amount) => sum + amount, 0) : null;
  const printed = cents(receipt.total);
  const discount = cents(receipt.discount) ?? 0;
  const difference = subtotal !== null && printed !== null ? subtotal - discount - printed : null;
  return (
    <form className="grid gap-4 min-w-0" noValidate onSubmit={(event) => { event.preventDefault(); onConfirm(); }}>
      <Card padding="p-4">
        <h2 className="text-xl">{onRepeat ? 'Проверь чек' : 'Редактирование чека'}</h2>
        {onRepeat && <p className="text-sm text-text-soft mt-1">Сверь поля с фото. Чек появится в истории после сохранения.</p>}
        {retried && <p className="text-xs text-text-muted mt-2">Распознавание автоматически повторилось для проверки.</p>}
        {photo && <details className="mt-3"><summary className="cursor-pointer text-sm font-bold text-brand">Посмотреть фото</summary>{photo}</details>}
        <fieldset disabled={busy} className="grid gap-3 mt-4 min-w-0">
          <Input label="Магазин" maxLength={256} value={receipt.store_name ?? ''} onChange={(e) => onEdit({ ...receipt, store_name: e.target.value })} />
          <Input label="Дата покупки" type="date" lang="ru" value={receipt.date ?? ''} onChange={(e) => onEdit({ ...receipt, date: e.target.value })} />
          <Input label="Итог к оплате, ₽" inputMode="decimal" value={receipt.total ?? ''} onChange={(e) => onEdit({ ...receipt, total: e.target.value })} />
          <details>
            <summary className="cursor-pointer text-sm font-bold">Общая скидка на чек</summary>
            <Input className="mt-2" label="Скидка, ещё не учтённая в позициях, ₽" inputMode="decimal"
              value={receipt.discount ?? ''} onChange={(e) => onEdit({ ...receipt, discount: e.target.value })} />
          </details>
          {subtotal !== null && <p className="text-sm font-bold num">По позициям после общей скидки · {formatExactMoney((subtotal - discount) / 100)}</p>}
          {difference !== null && Math.abs(difference) > 1 && (
            <p role="status" className="rounded-input bg-coin/35 px-3 py-2 text-sm text-coin-text">Расхождение с итогом · {formatExactMoney(Math.abs(difference) / 100)}</p>
          )}
        </fieldset>
      </Card>

      {warnings.length > 0 && (
        <section aria-label="Что сверить" className="rounded-input bg-coin/30 p-4 text-coin-text">
          <h2 className="text-base">Что сверить</h2>
          <ul className="mt-2 grid gap-1 text-sm list-disc pl-4">
            {warnings.map(({ message }, index) => <li key={index}>{message}</li>)}
          </ul>
          {warnings.some(({ blocking }) => !blocking) && (
            <label className="mt-3 flex items-start gap-2 text-sm font-bold cursor-pointer">
              <input type="checkbox" className="accent-brand size-4 shrink-0 mt-0.5" checked={acceptedWarnings}
                onChange={(e) => onAcceptWarnings(e.target.checked)} />
              Я сверил чек и подтверждаю введённые суммы
            </label>
          )}
        </section>
      )}

      <fieldset disabled={busy} className="grid gap-3 min-w-0">
        <legend className="text-base font-extrabold mb-2">Позиции чека</legend>
        {receipt.items.map((item, index) => (
          <ItemEditor key={item.editorKey} item={item} index={index} categories={categories}
            onEdit={(value) => onEdit({ ...receipt, items: receipt.items.map((line) => line.editorKey === item.editorKey ? value : line) })}
            onRemove={() => onEdit({ ...receipt, items: receipt.items.filter((line) => line.editorKey !== item.editorKey) })} />
        ))}
        <Button variant="ghost" disabled={receipt.items.length >= 120} onClick={onAdd}>
          <Plus size={18} aria-hidden="true" /> Добавить позицию
        </Button>
      </fieldset>
      {error && <ErrorState message={error} />}
      <Button type="submit" disabled={busy}>{busy ? 'Сохраняем…' : onRepeat ? 'Подтвердить и сохранить' : 'Сохранить изменения'}</Button>
      {onRepeat && <Button variant="secondary" disabled={busy} onClick={onRepeat}>
        <RefreshCw size={17} aria-hidden="true" /> Повторить распознавание
      </Button>}
      <Button variant="ghost" disabled={busy} onClick={onReset}>{onRepeat ? 'Выбрать другое фото' : 'Отмена'}</Button>
    </form>
  );
}
