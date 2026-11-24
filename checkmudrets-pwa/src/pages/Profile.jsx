import { useState } from 'react';
import { Download, LogOut, User } from 'lucide-react';
import { useAuth } from '../auth/context';
import ErrorState from '../components/ErrorState';
import Logo from '../components/Logo';
import { Button, Card, Tag } from '../components/ui';

function initials(name) {
  return (
    name
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((w) => w[0]?.toUpperCase())
      .join('') || '?'
  );
}

export default function Profile({ profile, onInstall }) {
  const { signOut } = useAuth();
  const [leaving, setLeaving] = useState(false);
  const [logoutError, setLogoutError] = useState(false);
  const [installError, setInstallError] = useState(false);

  async function handleSignOut() {
    setLeaving(true);
    setLogoutError(false);
    try {
      await signOut();
    } catch {
      setLogoutError(true);
    } finally {
      setLeaving(false);
    }
  }

  async function handleInstall() {
    setInstallError(false);
    try {
      await onInstall();
    } catch {
      setInstallError(true);
    }
  }

  return (
    <div className="px-4 pt-5 pb-6 max-w-lg mx-auto flex flex-col gap-4">
      <h1 className="text-[28px]">Профиль</h1>

      <Card>
        <div className="flex items-center gap-4">
          <span className="w-14 h-14 rounded-full bg-brand text-white flex items-center justify-center text-xl font-extrabold shrink-0">
            {profile.name ? initials(profile.name) : <User size={24} aria-hidden="true" />}
          </span>
          <div className="min-w-0">
            <p className="font-extrabold text-[17px] wrap-anywhere">{profile.name || 'Пользователь'}</p>
            {profile.email && <p className="text-xs text-text-muted wrap-anywhere">{profile.email}</p>}
          </div>
        </div>

        <div className="flex flex-col gap-3 mt-5">
          {logoutError && <ErrorState message="Не удалось выйти. Попробуй ещё раз." />}
          <Button variant="secondary" full disabled={leaving} onClick={handleSignOut}>
            <LogOut size={18} aria-hidden="true" /> {leaving ? 'Выходим…' : 'Выйти из аккаунта'}
          </Button>
        </div>
      </Card>

      {onInstall && (
        <button
          type="button"
          onClick={handleInstall}
          className="w-full rounded-card bg-text text-white p-5 flex items-center gap-4 text-left transition-transform hover:-translate-y-0.5"
        >
          <span className="w-11 h-11 rounded-[14px] bg-white/15 flex items-center justify-center shrink-0">
            <Download size={22} />
          </span>
          <span>
            <span className="block font-extrabold">Установить приложение</span>
            <span className="block text-[13px] text-on-dark leading-snug">Добавь на экран «Домой» для быстрого доступа</span>
          </span>
        </button>
      )}
      {installError && <ErrorState message="Не удалось открыть окно установки приложения." />}

      <Card>
        <Tag>О приложении</Tag>
        <div className="mt-4">
          <Logo size="sm" />
        </div>
        <dl className="mt-4 text-[13px] text-text-soft flex flex-col gap-1.5">
          <div className="flex justify-between gap-3">
            <dt>Версия</dt>
            <dd className="font-bold text-text">1.0 · PWA</dd>
          </div>
        </dl>
        <div className="mt-4 pt-4 border-t border-line text-[12px] text-text-muted leading-relaxed">
          <p>Команда: Земсков А.В., Викторов А.Д., Демидов И.С.</p>
          <p>Группа ЭФБО-06-23, РТУ МИРЭА</p>
        </div>
      </Card>
    </div>
  );
}
