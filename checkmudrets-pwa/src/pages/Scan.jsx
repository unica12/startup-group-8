import { useState, useRef } from 'react';
import { uploadReceipt } from '../services/api';
import { Camera, Image as ImageIcon, Upload, Check, AlertCircle, Lightbulb } from 'lucide-react';
import Loader from '../components/Loader';

export default function Scan({ onNavigate }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileRef = useRef(null);
  const cameraRef = useRef(null);

  const handleFile = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const res = await uploadReceipt(file);
      if (res.success) {
        setResult(res);
      } else {
        setError(res.error || 'Не удалось распознать чек');
      }
    } catch (err) {
      setError('Ошибка соединения с сервером');
    } finally {
      setUploading(false);
    }
  };

  const reset = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
  };

  function formatMoney(n) {
    return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 }).format(n) + ' ₽';
  }

  return (
    <div className="px-4 pt-6 pb-4 max-w-lg mx-auto space-y-5">
      <h1 className="text-2xl font-bold text-primary">Сканировать чек</h1>

      {!result && !uploading && (
        <>
          {/* Upload area */}
          {!preview ? (
            <div className="border-2 border-dashed border-accent/40 rounded-2xl p-8 text-center bg-accent/5">
              <Camera size={48} className="mx-auto text-accent mb-3" strokeWidth={1.5} />
              <p className="font-medium text-text mb-1">Сфотографируй или выбери чек</p>
              <p className="text-text-secondary text-sm mb-5">Поддерживаются JPEG, PNG, WebP</p>
              <div className="flex gap-3 justify-center">
                <button
                  onClick={() => cameraRef.current?.click()}
                  className="bg-accent text-white font-semibold py-2.5 px-5 rounded-full flex items-center gap-2 hover:bg-accent-dark transition-colors"
                >
                  <Camera size={18} /> Камера
                </button>
                <button
                  onClick={() => fileRef.current?.click()}
                  className="bg-white text-primary font-semibold py-2.5 px-5 rounded-full flex items-center gap-2 border border-border hover:border-accent transition-colors"
                >
                  <ImageIcon size={18} /> Галерея
                </button>
              </div>
              <input ref={cameraRef} type="file" accept="image/*" capture="environment" onChange={handleFile} className="hidden" />
              <input ref={fileRef} type="file" accept="image/*" onChange={handleFile} className="hidden" />
            </div>
          ) : (
            <div className="space-y-4">
              <div className="rounded-2xl overflow-hidden border border-border shadow-sm">
                <img src={preview} alt="Чек" className="w-full max-h-80 object-contain bg-gray-50" />
              </div>
              <div className="flex gap-3">
                <button onClick={reset} className="flex-1 py-2.5 rounded-full border border-border font-medium hover:bg-gray-50 transition-colors">
                  Выбрать другой
                </button>
                <button onClick={handleUpload} className="flex-1 py-2.5 rounded-full bg-accent text-white font-semibold flex items-center justify-center gap-2 hover:bg-accent-dark transition-colors">
                  <Upload size={18} /> Распознать
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {uploading && <Loader text="Распознаём чек с помощью ИИ..." />}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-start gap-3">
          <AlertCircle size={20} className="text-danger mt-0.5 shrink-0" />
          <div>
            <p className="font-medium text-danger">Ошибка</p>
            <p className="text-sm text-text-secondary mt-0.5">{error}</p>
            <button onClick={reset} className="mt-2 text-sm text-accent font-medium">Попробовать снова</button>
          </div>
        </div>
      )}

      {result && result.success && (
        <div className="space-y-4">
          {/* Success header */}
          <div className="bg-accent/10 rounded-2xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-accent flex items-center justify-center">
              <Check size={22} className="text-white" />
            </div>
            <div>
              <p className="font-semibold text-accent">Чек распознан!</p>
              <p className="text-sm text-text-secondary">
                {result.receipt?.store_name || 'Магазин'} · {formatMoney(result.receipt?.total || 0)}
              </p>
            </div>
          </div>

          {/* Items */}
          <div className="bg-card rounded-2xl border border-border shadow-sm overflow-hidden">
            <div className="px-4 py-3 bg-gray-50 border-b border-border">
              <span className="text-sm font-medium text-text-secondary">
                Позиции ({result.receipt?.items?.length || 0})
              </span>
            </div>
            <div className="divide-y divide-border max-h-64 overflow-y-auto">
              {result.receipt?.items?.map((item, i) => (
                <div key={i} className="px-4 py-2.5 flex items-center justify-between">
                  <div className="flex-1 min-w-0 mr-2">
                    <p className="text-sm truncate">{item.name}</p>
                    <p className="text-xs text-text-secondary">{item.category} · {item.quantity} шт.</p>
                  </div>
                  <span className="text-sm font-medium whitespace-nowrap">{formatMoney(item.total)}</span>
                </div>
              ))}
            </div>
            <div className="px-4 py-3 bg-gray-50 border-t border-border flex justify-between">
              <span className="font-semibold">Итого</span>
              <span className="font-bold text-primary">{formatMoney(result.receipt?.total || 0)}</span>
            </div>
          </div>

          {/* Mini advice */}
          {result.mini_advice && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-4 flex items-start gap-3">
              <Lightbulb size={20} className="text-warning mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-medium text-warning">Совет</p>
                <p className="text-sm text-text mt-0.5">{result.mini_advice}</p>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button onClick={reset} className="flex-1 py-2.5 rounded-full bg-accent text-white font-semibold hover:bg-accent-dark transition-colors">
              Сканировать ещё
            </button>
            <button onClick={() => onNavigate('history')} className="flex-1 py-2.5 rounded-full border border-border font-medium hover:bg-gray-50 transition-colors">
              К истории
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
