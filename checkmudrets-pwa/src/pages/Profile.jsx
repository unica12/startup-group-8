import { useState, useEffect } from 'react';
import { register, getUserName, setUserName as saveUserName, getDeviceId, API_BASE } from '../services/api';
import { User, Save, Smartphone, Server, Info, Download } from 'lucide-react';

export default function Profile({ userName, setUserName }) {
  const [name, setName] = useState(userName || '');
  const [saved, setSaved] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState(null);

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
    };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleSave = async () => {
    if (!name.trim()) return;
    try {
      await register(name.trim());
      setUserName(name.trim());
      saveUserName(name.trim());
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error('Ошибка сохранения:', err);
    }
  };

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    setDeferredPrompt(null);
  };

  return (
    <div className="px-4 pt-6 pb-4 max-w-lg mx-auto space-y-5">
      <h1 className="text-2xl font-bold text-primary">Профиль</h1>

      {/* Name */}
      <div className="bg-card rounded-2xl border border-border shadow-sm p-5 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center">
            <User size={24} className="text-white" />
          </div>
          <div>
            <p className="font-semibold text-text">{userName || 'Пользователь'}</p>
            <p className="text-xs text-text-secondary">ID: {getDeviceId().slice(0, 12)}...</p>
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-text-secondary">Имя</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Введи имя"
              className="flex-1 px-4 py-2.5 rounded-xl border border-border focus:border-accent focus:ring-1 focus:ring-accent outline-none text-sm transition-colors"
            />
            <button
              onClick={handleSave}
              className={`px-4 py-2.5 rounded-xl font-medium text-sm flex items-center gap-1.5 transition-colors ${
                saved ? 'bg-accent/10 text-accent' : 'bg-accent text-white hover:bg-accent-dark'
              }`}
            >
              {saved ? 'Сохранено ✓' : <><Save size={16} /> Сохранить</>}
            </button>
          </div>
        </div>
      </div>

      {/* Install PWA */}
      {deferredPrompt && (
        <button
          onClick={handleInstall}
          className="w-full bg-primary text-white rounded-2xl p-4 flex items-center gap-3 shadow-lg hover:bg-primary-light transition-colors"
        >
          <Download size={24} />
          <div className="text-left">
            <p className="font-semibold">Установить приложение</p>
            <p className="text-sm opacity-80">Добавь на рабочий стол для быстрого доступа</p>
          </div>
        </button>
      )}

      {/* Info */}
      <div className="bg-card rounded-2xl border border-border shadow-sm p-5 space-y-4">
        <h3 className="font-semibold flex items-center gap-2">
          <Info size={18} className="text-accent" /> О приложении
        </h3>

        <div className="space-y-3 text-sm">
          <div className="flex items-center gap-3 text-text-secondary">
            <Smartphone size={16} className="shrink-0" />
            <span>ЧекМудрец v1.0 — PWA</span>
          </div>
          <div className="flex items-center gap-3 text-text-secondary">
            <Server size={16} className="shrink-0" />
            <span className="break-all">{API_BASE}</span>
          </div>
        </div>

        <div className="pt-3 border-t border-border text-xs text-text-secondary space-y-1">
          <p>Сканирование чеков: GPT-4o-mini Vision</p>
          <p>Разработка: ООО «ЧекМудрец»</p>
          <p>Команда: Земсков А.В., Викторов А.Д., Демидов И.С.</p>
          <p>Группа ЭФБО-06-23, РТУ МИРЭА</p>
        </div>
      </div>
    </div>
  );
}
