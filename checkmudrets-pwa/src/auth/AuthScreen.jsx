import { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { Button, Input } from '../components/ui';
import ErrorState from '../components/ErrorState';
import AuthLayout from './AuthLayout';
import ConsentFields from './ConsentFields';
import { useAuth } from './context';
import { allConsentsChecked } from './documents';

const MESSAGES = {
  invalid_credentials: 'Проверь email и пароль.',
  email_not_confirmed: 'Подтверди email по ссылке из письма, затем войди.',
  user_already_exists: 'Этот email уже используется. Попробуй войти.',
  email_exists: 'Этот email уже используется. Попробуй войти.',
  email_address_invalid: 'Проверь адрес электронной почты.',
  email_address_not_authorized: 'Сервис не может отправить письмо на этот адрес. Обратись к команде проекта.',
  weak_password: 'Выбери более надёжный пароль.',
  signup_disabled: 'Регистрация временно закрыта.',
  over_email_send_rate_limit: 'Подожди немного перед повторной отправкой письма.',
  over_request_rate_limit: 'Слишком много попыток. Попробуй чуть позже.',
};

function readConfirmationError() {
  const hash = new URLSearchParams(window.location.hash.slice(1));
  return hash.has('error_code') || hash.has('error');
}

export default function AuthScreen() {
  const auth = useAuth();
  const [registering, setRegistering] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [checked, setChecked] = useState({});
  const [errors, setErrors] = useState({});
  const [error, setError] = useState(() => readConfirmationError() ? 'Ссылка подтверждения недействительна или истекла.' : '');
  const [waiting, setWaiting] = useState(false);
  const [canResend, setCanResend] = useState(false);
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  function editField(field, setter) {
    return (event) => {
      setter(event.target.value);
      if (errors[field]) setErrors((current) => ({ ...current, [field]: undefined }));
    };
  }

  function changeMode(next) {
    setRegistering(next);
    setPassword('');
    setConfirmation('');
    setShowPassword(false);
    setChecked({});
    setErrors({});
    setError('');
    setWaiting(false);
    setCanResend(false);
    setSent(false);
  }

  async function submit(event) {
    event.preventDefault();
    if (busy || !auth.configured || (registering && !allConsentsChecked(checked))) return;
    const formErrors = {};
    if (registering && !name.trim()) formErrors.name = 'Введи имя.';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) formErrors.email = 'Введи корректный email.';
    if (!password) formErrors.password = 'Введи пароль.';
    else if (registering && password.length < 6) formErrors.password = 'Используй минимум 6 символов.';
    if (registering && (!confirmation || password !== confirmation)) formErrors.confirmation = 'Пароли должны совпадать.';
    setErrors(formErrors);
    setError('');
    setCanResend(false);
    setSent(false);
    if (Object.keys(formErrors).length) return;

    setBusy(true);
    try {
      if (registering) {
        const signedIn = await auth.signUp({ name: name.trim(), email: email.trim(), password });
        if (!signedIn) {
          setPassword('');
          setConfirmation('');
          setWaiting(true);
        }
      } else {
        await auth.signIn(email.trim(), password);
      }
    } catch (failure) {
      setError(MESSAGES[failure.code] || 'Не удалось продолжить. Проверь соединение и попробуй ещё раз.');
      setCanResend(failure.code === 'email_not_confirmed');
    } finally {
      setBusy(false);
    }
  }

  async function resend() {
    setBusy(true);
    setError('');
    try {
      await auth.resendEmail(email.trim());
      setSent(true);
    } catch (failure) {
      setError(MESSAGES[failure.code] || 'Не удалось повторно отправить письмо. Попробуй позже.');
    } finally {
      setBusy(false);
    }
  }

  if (waiting) {
    return (
      <AuthLayout title="Подтверди email" intro="Открой ссылку из письма, чтобы закончить регистрацию.">
        <div className="grid gap-3">
          <p className="text-sm wrap-anywhere">Адрес для подтверждения <strong>{email.trim()}</strong></p>
          {error && <ErrorState message={error} />}
          {sent && <p className="text-sm text-brand" role="status">Запрос на повторную отправку принят.</p>}
          <Button variant="secondary" disabled={busy} onClick={resend}>Отправить письмо ещё раз</Button>
          <Button variant="ghost" disabled={busy} onClick={() => changeMode(false)}>Ко входу</Button>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title={registering ? 'Регистрация' : 'Вход'} intro={registering ? 'Создай аккаунт для учёта расходов.' : 'Войди, чтобы увидеть чеки и расходы.'}>
      {!auth.configured && <ErrorState message="Для входа нужно настроить адрес API и Supabase." />}
      <form noValidate className="flex flex-col gap-3" onSubmit={submit}>
        {registering && <Input label="Имя" autoComplete="given-name" required maxLength={50} value={name} onChange={editField('name', setName)} error={errors.name} readOnly={busy} />}
        <Input label="Электронная почта" type="email" autoComplete="email" required maxLength={254} value={email} onChange={editField('email', setEmail)} error={errors.email} readOnly={busy} />
        <Input label="Пароль" type={showPassword ? 'text' : 'password'} autoComplete={registering ? 'new-password' : 'current-password'} required value={password} onChange={editField('password', setPassword)} error={errors.password} readOnly={busy} />
        {registering && <Input label="Повтори пароль" type={showPassword ? 'text' : 'password'} autoComplete="new-password" required value={confirmation} onChange={editField('confirmation', setConfirmation)} error={errors.confirmation} readOnly={busy} />}
        <Button variant="ghost" size="sm" className="self-start" aria-pressed={showPassword} onClick={() => setShowPassword((value) => !value)}>
          {showPassword ? <EyeOff size={16} aria-hidden="true" /> : <Eye size={16} aria-hidden="true" />}
          {showPassword ? 'Скрыть пароль' : 'Показать пароль'}
        </Button>
        {registering && <ConsentFields checked={checked} onChange={setChecked} disabled={busy} />}
        {error && <ErrorState message={error} />}
        {sent && <p role="status" className="text-sm text-brand">Запрос на повторную отправку принят.</p>}
        <Button type="submit" full disabled={busy || !auth.configured || (registering && !allConsentsChecked(checked))}>
          {busy ? 'Подожди…' : registering ? 'Зарегистрироваться' : 'Войти'}
        </Button>
        {canResend && <Button variant="secondary" disabled={busy} onClick={resend}>Отправить письмо ещё раз</Button>}
      </form>
      <Button variant="ghost" full className="mt-3" disabled={busy} onClick={() => changeMode(!registering)}>
        {registering ? 'У меня уже есть аккаунт' : 'Создать аккаунт'}
      </Button>
    </AuthLayout>
  );
}
