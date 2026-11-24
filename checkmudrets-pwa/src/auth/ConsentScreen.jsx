import { useState } from 'react';
import { Button } from '../components/ui';
import ErrorState from '../components/ErrorState';
import AuthLayout from './AuthLayout';
import ConsentFields from './ConsentFields';
import { useAuth } from './context';
import { allConsentsChecked } from './documents';

export default function ConsentScreen() {
  const { confirmConsents, signOut } = useAuth();
  const [checked, setChecked] = useState({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function confirm(event) {
    event.preventDefault();
    if (busy || !allConsentsChecked(checked)) return;
    setBusy(true);
    setError('');
    try {
      await confirmConsents();
    } catch (failure) {
      setError(failure.status === 422
        ? 'Документы обновились. Обнови приложение и попробуй снова.'
        : 'Не удалось сохранить согласия. Проверь соединение.');
    } finally {
      setBusy(false);
    }
  }

  async function leave() {
    try { await signOut(); } catch { setError('Не удалось выйти. Попробуй ещё раз.'); }
  }

  return (
    <AuthLayout title="Подтверди согласия" intro="Прими документы, чтобы открыть приложение.">
      <form className="grid gap-3" onSubmit={confirm}>
        <ConsentFields checked={checked} onChange={setChecked} disabled={busy} />
        {error && <ErrorState message={error} />}
        <Button type="submit" disabled={busy || !allConsentsChecked(checked)}>{busy ? 'Сохраняем…' : 'Подтвердить и продолжить'}</Button>
        <Button variant="ghost" onClick={leave} disabled={busy}>Выйти</Button>
      </form>
    </AuthLayout>
  );
}
