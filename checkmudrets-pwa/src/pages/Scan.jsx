import { useEffect, useRef, useState } from 'react';
import { Camera, Check, Image as ImageIcon } from 'lucide-react';
import { confirmReceipt, recognizeReceipt } from '../services/api';
import { formatExactMoney, plural } from '../utils/format';
import ErrorState from '../components/ErrorState';
import { InsightCard } from '../components/InsightCard';
import Loader from '../components/Loader';
import Mascot from '../components/Mascot';
import ReceiptEditor from '../components/ReceiptEditor';
import { editorPayload } from '../utils/receiptEditor';
import { Button, Card } from '../components/ui';

export default function Scan({ onNavigate, userId }) {
  const [photo, setPhoto] = useState(null);
  const [previewError, setPreviewError] = useState(false);
  const [phase, setPhase] = useState(null);
  const [result, setResult] = useState(null);
  const [draft, setDraft] = useState(null);
  const [acceptedWarnings, setAcceptedWarnings] = useState(false);
  const [error, setError] = useState(null);
  const fileRef = useRef(null);
  const cameraRef = useRef(null);
  const active = useRef(false);
  const nextKey = useRef(0);

  useEffect(() => () => photo && URL.revokeObjectURL(photo.url), [photo]);

  function reset() {
    setPhoto(null);
    setPreviewError(false);
    setResult(null);
    setDraft(null);
    setAcceptedWarnings(false);
    setError(null);
  }

  function handleFile(event) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    reset();
    setPhoto({ file, url: URL.createObjectURL(file) });
  }

  function edit(receipt) {
    setAcceptedWarnings(false);
    setError(null);
    setDraft((current) => ({ ...current, receipt }));
  }

  async function recognize() {
    if (!photo || active.current) return;
    active.current = true;
    setPhase('recognizing');
    setError(null);
    try {
      const response = await recognizeReceipt(photo.file, userId);
      if (!response.success || !response.draft_id || !response.receipt) {
        setError(response.error || 'Не удалось распознать чек.');
        return;
      }
      const items = response.receipt.items.map((item) => ({ ...item, editorKey: nextKey.current++ }));
      setDraft({ ...response, receipt: { ...response.receipt, items } });
      setAcceptedWarnings(false);
    } catch (failure) {
      setError(typeof failure.detail === 'string' ? failure.detail : 'Не удалось распознать чек. Проверь соединение и попробуй снова.');
    } finally {
      setPhase(null);
      active.current = false;
    }
  }

  async function save() {
    if (!draft || active.current) return;
    active.current = true;
    setPhase('saving');
    setError(null);
    try {
      const response = await confirmReceipt(draft.draft_id, editorPayload(draft.receipt), acceptedWarnings, userId);
      setResult(response);
      setDraft(null);
      setPhoto(null);
    } catch (failure) {
      const detail = failure.detail;
      if (Array.isArray(detail?.warnings)) {
        setDraft((current) => ({ ...current, warnings: detail.warnings }));
        setAcceptedWarnings(false);
      }
      setError(detail?.message || (typeof detail === 'string' ? detail
        : failure.status === 422 ? 'Проверь формат сумм, количества и даты.'
          : 'Не удалось подтвердить сохранение. Попробуй ещё раз, черновик сохранится один раз.'));
    } finally {
      setPhase(null);
      active.current = false;
    }
  }

  const preview = photo && (
    previewError
      ? <p className="p-3 text-sm text-text-soft wrap-anywhere">Фото выбрано. Предпросмотр недоступен.</p>
      : <img src={photo.url} alt="Фото чека" onError={() => setPreviewError(true)} className="w-full max-h-[52vh] object-contain rounded-input bg-bg" />
  );

  return (
    <div className="px-4 pt-5 pb-6 max-w-lg mx-auto flex flex-col gap-4">
      <h1 className="text-[28px]">Сканировать чек</h1>
      <input ref={cameraRef} type="file" accept="image/*" capture="environment" onChange={handleFile} className="hidden" />
      <input ref={fileRef} type="file" accept="image/*" onChange={handleFile} className="hidden" />

      {!photo && !result && (
        <Card padding="p-6" className="text-center flex flex-col items-center">
          <Mascot size={84} />
          <h2 className="text-xl mt-4">Сфотографируй чек</h2>
          <p className="text-text-soft text-sm mt-1 max-w-[280px]">Положи чек на ровную поверхность, чтобы были видны все строки и итог.</p>
          <div className="flex flex-col gap-2.5 w-full mt-5">
            <Button full onClick={() => cameraRef.current?.click()}><Camera size={18} /> Сфоткать</Button>
            <Button full variant="secondary" onClick={() => fileRef.current?.click()}><ImageIcon size={18} /> Выбрать из галереи</Button>
          </div>
          <p className="text-text-muted text-xs mt-4">JPEG, PNG, WebP, HEIC</p>
        </Card>
      )}
      {phase === 'recognizing' && <Loader mascot text="Мудрец читает чек..." />}
      {photo && !draft && !result && phase !== 'recognizing' && (
        <>
          <Card padding="p-2">{preview}</Card>
          {error && <ErrorState message={error} />}
          <div className="grid grid-cols-2 gap-2">
            <Button variant="secondary" onClick={reset}>Другое фото</Button>
            <Button onClick={recognize}>Распознать</Button>
          </div>
        </>
      )}
      {draft && phase !== 'recognizing' && (
        <ReceiptEditor {...draft} busy={phase === 'saving'} error={error} photo={preview}
          acceptedWarnings={acceptedWarnings} onAcceptWarnings={setAcceptedWarnings} onEdit={edit}
          onAdd={() => edit({ ...draft.receipt, items: [...draft.receipt.items, { editorKey: nextKey.current++ }] })}
          onRepeat={recognize} onReset={reset} onConfirm={save} />
      )}
      {result && (
        <>
          <section className="rounded-card bg-green p-5 shadow-[0_5px_0_#46A302] flex items-center gap-4" role="status">
            <Check size={24} className="shrink-0" aria-hidden="true" />
            <div className="min-w-0">
              <h2 className="text-xl">Чек сохранён</h2>
              {result.receipt.store_name && <p className="text-sm wrap-anywhere">{result.receipt.store_name}</p>}
              <p className="num text-[26px] font-extrabold wrap-anywhere">{formatExactMoney(result.receipt.total)}</p>
              <p className="text-xs">{result.receipt.items.length} {plural(result.receipt.items.length, ['позиция', 'позиции', 'позиций'])}</p>
            </div>
          </section>
          {result.mini_advice && <InsightCard insight={result.mini_advice} />}
          <div className="grid grid-cols-2 gap-2">
            <Button onClick={reset}>Ещё чек</Button>
            <Button variant="secondary" onClick={() => onNavigate('history')}>К истории</Button>
          </div>
        </>
      )}
    </div>
  );
}
