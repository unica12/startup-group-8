import { useState, useRef, useEffect } from 'react';
import { Camera, Image as ImageIcon, Check } from 'lucide-react';
import { uploadReceipt } from '../services/api';
import { formatMoney, plural } from '../utils/format';
import Loader from '../components/Loader';
import ErrorState from '../components/ErrorState';
import Mascot from '../components/Mascot';
import { Button, Card, Tag } from '../components/ui';

export default function Scan({ onNavigate }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [previewError, setPreviewError] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileRef = useRef(null);
  const cameraRef = useRef(null);

  useEffect(() => () => preview && URL.revokeObjectURL(preview), [preview]);

  const handleFile = (e) => {
    const f = e.target.files?.[0];
    e.target.value = '';
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setPreviewError(false);
    setResult(null);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file || uploading) return;
    setUploading(true);
    setError(null);
    try {
      const res = await uploadReceipt(file);
      if (res.success && res.receipt) setResult(res);
      else setError(res.error || 'Не удалось распознать чек. Попробуй сфотографировать ровнее и при хорошем свете.');
    } catch (requestError) {
      setError(requestError.status === 400
        ? 'Файл пустой или его формат не поддерживается. Попробуй другое фото.'
        : 'Не удалось отправить чек. Проверь соединение и попробуй ещё раз.');
    } finally {
      setUploading(false);
    }
  };

  const reset = () => {
    setFile(null);
    setPreview(null);
    setPreviewError(false);
    setResult(null);
    setError(null);
  };

  const receipt = result?.receipt;
  const itemsCount = receipt?.items?.length || 0;

  return (
    <div className="px-4 pt-5 pb-6 max-w-lg mx-auto flex flex-col gap-4">
      <h1 className="text-[28px]">Сканировать чек</h1>

      <input ref={cameraRef} type="file" accept="image/*" capture="environment" onChange={handleFile} className="hidden" />
      <input ref={fileRef} type="file" accept="image/*" onChange={handleFile} className="hidden" />

      {/* Выбор фото */}
      {!result && !uploading && !preview && (
        <Card padding="p-6" className="text-center flex flex-col items-center">
          <Mascot size={84} />
          <h2 className="text-xl mt-4">Сфотографируй чек</h2>
          <p className="text-text-soft text-sm mt-1 max-w-[280px]">
            Положи чек на ровную поверхность, чтобы были видны все строки и итог.
          </p>
          <div className="flex flex-col gap-2.5 w-full mt-5">
            <Button full onClick={() => cameraRef.current?.click()}>
              <Camera size={18} /> Сфоткать
            </Button>
            <Button full variant="secondary" onClick={() => fileRef.current?.click()}>
              <ImageIcon size={18} /> Выбрать из галереи
            </Button>
          </div>
          <p className="text-text-muted text-xs mt-4">JPEG, PNG, WebP, HEIC</p>
        </Card>
      )}

      {/* Превью */}
      {!result && !uploading && preview && (
        <div className="flex flex-col gap-3">
          <Card padding="p-2" className="overflow-hidden">
            {previewError ? (
              <p className="p-3 text-sm text-text-soft wrap-anywhere">Фото «{file.name}» выбрано. Предпросмотр недоступен.</p>
            ) : (
              <img key={preview} src={preview} alt="Фото чека" onError={() => setPreviewError(true)} className="w-full max-h-[52vh] object-contain rounded-input bg-bg" />
            )}
          </Card>
          {error && <ErrorState message={error} />}
          <div className="flex gap-2.5">
            <Button variant="secondary" className="flex-1" onClick={reset}>
              Другое фото
            </Button>
            <Button className="flex-1" onClick={handleUpload}>
              {error ? 'Повторить' : 'Распознать'}
            </Button>
          </div>
        </div>
      )}

      {uploading && (
        <Loader mascot text="Мудрец читает чек..." hint="Обычно это занимает 5–15 секунд" />
      )}

      {/* Результат */}
      {result?.success && receipt && (
        <div className="flex flex-col gap-4">
          <section className="rounded-card bg-green p-5 shadow-[0_5px_0_#46A302] flex items-center gap-4" role="status">
            <span className="w-11 h-11 rounded-full bg-white/22 flex items-center justify-center shrink-0">
              <Check size={24} strokeWidth={3} />
            </span>
            <div className="min-w-0">
              <p className="text-[13px] font-bold wrap-anywhere">Чек распознан{receipt.store_name && ` · ${receipt.store_name}`}</p>
              <p className="num text-[28px] font-extrabold tracking-[-0.045em] leading-tight wrap-anywhere">{formatMoney(receipt.total)}</p>
            </div>
          </section>

          <Card padding="p-0" className="overflow-hidden">
            <div className="px-5 pt-4 pb-2">
              <Tag>
                {itemsCount} {plural(itemsCount, ['позиция', 'позиции', 'позиций'])}
              </Tag>
            </div>
            <ul className="divide-y divide-line max-h-72 overflow-y-auto px-5">
              {receipt.items?.map((item, index) => (
                <li key={item.id > 0 ? `item:${item.id}` : `position:${index}`} className="py-2.5 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-[14px] font-bold wrap-anywhere">{item.name}</p>
                    <p className="text-[12px] text-text-muted num">
                      {item.category} · {item.quantity} шт.
                    </p>
                  </div>
                  <span className="num text-[14px] font-extrabold text-right wrap-anywhere">{formatMoney(item.total)}</span>
                </li>
              ))}
            </ul>
            <div className="px-5 py-3.5 bg-bg border-t border-line flex justify-between gap-3">
              <span className="font-extrabold">Итого</span>
              <span className="num font-extrabold text-brand text-right wrap-anywhere">{formatMoney(receipt.total)}</span>
            </div>
          </Card>

          {result.mini_advice && (
            <section className="rounded-input bg-pill p-4 flex items-center gap-3">
              <Mascot size={44} withLines={false} className="shrink-0" />
              <p className="text-[13.5px] font-extrabold text-green-shadow leading-snug whitespace-pre-line wrap-anywhere">{result.mini_advice}</p>
            </section>
          )}

          <div className="flex gap-2.5">
            <Button className="flex-1" onClick={reset}>
              Ещё чек
            </Button>
            <Button variant="secondary" className="flex-1" onClick={() => onNavigate('history')}>
              К истории
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
