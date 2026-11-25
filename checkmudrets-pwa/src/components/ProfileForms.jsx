import { useRef, useState } from 'react';
import { useAuth } from '../auth/context';
import ErrorState from './ErrorState';
import { Button, Card, Input } from './ui';

export function NameForm({ initialName, onSaved }) {
  const { saveName } = useAuth();
  const [name, setName] = useState(initialName || '');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    const cleaned = name.trim().replace(/\s+/g, ' ');
    if (!cleaned || Array.from(cleaned).length > 50) {
      setError('Введи имя длиной от 1 до 50 символов.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await saveName(cleaned);
      onSaved('Имя обновлено.');
    } catch (failure) {
      setError(failure.status === 422 ? 'Проверь имя. В нём могут быть только видимые символы.' : 'Не удалось сохранить имя. Попробуй ещё раз.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <form noValidate onSubmit={submit} className="grid gap-4" aria-busy={busy}>
        <Input autoComplete="name" label="Имя" value={name} maxLength={80} disabled={busy} error={error}
          onChange={(event) => { setName(event.target.value); setError(''); }} />
        <Button type="submit" disabled={busy}>{busy ? 'Сохраняем…' : 'Сохранить имя'}</Button>
      </form>
    </Card>
  );
}

export function PasswordForm({ onSaved }) {
  const { changePassword } = useAuth();
  const [current, setCurrent] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    if (!current) return setError('Введи текущий пароль.');
    if (password.length < 6) return setError('Новый пароль должен содержать минимум 6 символов.');
    if (password !== confirmation) return setError('Новые пароли должны совпадать.');
    if (password === current) return setError('Выбери пароль, который отличается от текущего.');
    setBusy(true);
    setError('');
    try {
      await changePassword(current, password);
      onSaved('Пароль изменён.');
    } catch (failure) {
      const messages = {
        invalid_credentials: 'Текущий пароль неверный.',
        invalid_current_password: 'Текущий пароль неверный.',
        same_password: 'Выбери пароль, который отличается от текущего.',
        weak_password: 'Новый пароль не соответствует настройкам безопасности Supabase.',
      };
      setError(messages[failure.code] || 'Не удалось изменить пароль. Попробуй ещё раз.');
    } finally {
      setBusy(false);
    }
  }

  const type = show ? 'text' : 'password';
  return (
    <Card>
      <form noValidate className="grid gap-3" aria-busy={busy} onSubmit={submit}>
        <Input label="Текущий пароль" autoComplete="current-password" type={type} value={current} disabled={busy} onChange={(event) => setCurrent(event.target.value)} />
        <Input label="Новый пароль" autoComplete="new-password" type={type} value={password} disabled={busy} onChange={(event) => setPassword(event.target.value)} />
        <Input label="Повтори новый пароль" autoComplete="new-password" type={type} value={confirmation} disabled={busy} onChange={(event) => setConfirmation(event.target.value)} />
        <Button size="sm" variant="ghost" className="justify-self-start" aria-pressed={show} onClick={() => setShow((value) => !value)}>
          {show ? 'Скрыть пароли' : 'Показать пароли'}
        </Button>
        {error && <ErrorState message={error} />}
        <Button type="submit" disabled={busy}>{busy ? 'Меняем пароль…' : 'Сохранить пароль'}</Button>
      </form>
    </Card>
  );
}

export function DeleteAccountForm() {
  const { deleteAccount } = useAuth();
  const [password, setPassword] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const running = useRef(false);

  async function submit(event) {
    event.preventDefault();
    if (running.current || !password || !confirmed) return;
    running.current = true;
    setBusy(true);
    setError('');
    try {
      await deleteAccount(password);
    } catch (failure) {
      setError(failure.code === 'invalid_credentials' ? 'Текущий пароль неверный.'
        : typeof failure.detail === 'string' ? failure.detail
          : failure.detail?.message || 'Запрос на удаление не завершён. Попробуй ещё раз.');
    } finally {
      running.current = false;
      setBusy(false);
    }
  }

  return (
    <section className="rounded-card border border-danger/25 bg-danger-bg p-5">
      <p className="text-sm font-bold text-danger">Удаление необратимо.</p>
      <p className="mt-1 text-sm text-text-soft">Будут удалены профиль, чеки и товары, согласия, черновики, сохранённые инсайты и учётная запись Supabase.</p>
      <form noValidate className="mt-4 grid gap-4" aria-busy={busy} onSubmit={submit}>
        <Input label="Текущий пароль" autoComplete="current-password" type="password" value={password} disabled={busy} onChange={(event) => setPassword(event.target.value)} />
        <label className="flex items-start gap-2 text-sm font-bold cursor-pointer">
          <input type="checkbox" className="mt-0.5 size-4 shrink-0 accent-danger" checked={confirmed} disabled={busy} onChange={(event) => setConfirmed(event.target.checked)} />
          Подтверждаю удаление аккаунта и данных
        </label>
        {error && <ErrorState message={error} />}
        <Button variant="danger" type="submit" disabled={busy || !confirmed || !password}>{busy ? 'Удаляем…' : 'Удалить аккаунт навсегда'}</Button>
      </form>
    </section>
  );
}
