import { useEffect, useRef, useState } from 'react';
import {
  ArrowLeft, ChevronRight, Download, FileDown, FileText, Info, KeyRound, LogOut, Pencil, ShieldCheck, Trash2, User,
} from 'lucide-react';
import { version } from '../../package.json';
import { useAuth } from '../auth/context';
import { PROFILE_DOCUMENTS } from '../auth/documents';
import ErrorState from '../components/ErrorState';
import Loader from '../components/Loader';
import Logo from '../components/Logo';
import { DeleteAccountForm, NameForm, PasswordForm } from '../components/ProfileForms';
import { Button, Card } from '../components/ui';
import { exportProfile, getProfileStats } from '../services/api';
import { formatExactMoney } from '../utils/format';

const months = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long' });
const countFormat = new Intl.NumberFormat('ru-RU');

function initials(name) {
  return name?.trim().split(/\s+/u).filter(Boolean).slice(0, 2)
    .map((word) => Array.from(word)[0].toLocaleUpperCase('ru-RU')).join('');
}

function memberSince(value) {
  const date = new Date(value);
  if (!value || Number.isNaN(date.valueOf())) return '';
  const month = months.formatToParts(date).find(({ type }) => type === 'month').value;
  return `С нами с ${month} ${date.getFullYear()}`;
}

function Setting({ icon: Icon, children, onClick, disabled, danger }) {
  return (
    <button type="button" disabled={disabled} onClick={onClick}
      className={`w-full flex items-center gap-3 px-2 py-3 min-h-12 text-left rounded-input font-bold text-sm
        cursor-pointer hover:bg-bg disabled:opacity-60 disabled:cursor-default ${danger ? 'text-danger hover:bg-white/60' : ''}`}>
      <Icon size={19} className={`shrink-0 ${danger ? '' : 'text-brand'}`} aria-hidden="true" />
      <span className="flex-1 min-w-0 wrap-anywhere">{children}</span>
      <ChevronRight size={16} className="text-text-muted shrink-0" aria-hidden="true" />
    </button>
  );
}

function Settings({ title, children }) {
  return (
    <Card as="section" padding="p-4">
      <h2 className="text-lg px-2">{title}</h2>
      <div className="mt-2 divide-y divide-line">{children}</div>
    </Card>
  );
}

function Achievements({ userId }) {
  const [data, setData] = useState(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    getProfileStats(userId, controller.signal).then((stats) => {
      if (!controller.signal.aborted) setData(stats);
    }).catch(() => {
      if (!controller.signal.aborted) setFailed(true);
    });
    return () => controller.abort();
  }, [userId, attempt]);

  function retry() {
    setFailed(false);
    setAttempt((value) => value + 1);
  }

  return (
    <Card as="section" padding="p-4">
      <h2 className="text-lg">Мои достижения</h2>
      {failed ? <div className="mt-3"><ErrorState message="Не удалось загрузить статистику." onRetry={retry} /></div>
        : !data ? <Loader text="Считаем покупки…" />
          : data.receipts_count === 0 ? <p className="mt-2 text-sm text-text-soft">Пока нет сохранённых чеков. Здесь появятся расходы и покупки за всё время.</p>
            : <dl className="mt-3 grid grid-cols-2 gap-2">
              {[
                ['Сохранено чеков', countFormat.format(data.receipts_count)],
                ['Учтено расходов', formatExactMoney(data.total_spent)],
                ['Товарных позиций', countFormat.format(data.items_count)],
                ['Больше всего потрачено', data.top_category || '—'],
              ].map(([label, value]) => (
                <div key={label} className="rounded-input bg-bg p-3 min-w-0">
                  <dt className="text-xs text-text-soft">{label}</dt>
                  <dd className="num mt-0.5 font-extrabold text-sm wrap-anywhere">{value}</dd>
                </div>
              ))}
            </dl>}
    </Card>
  );
}

function Install({ installation }) {
  if (installation.installed) return (
    <p className="flex items-center gap-3 px-2 py-3 text-sm font-bold text-brand"><ShieldCheck size={19} aria-hidden="true" /> Приложение установлено</p>
  );
  if (installation.available) return <Setting icon={Download} onClick={installation.request}>Установить приложение</Setting>;
  if (installation.ios) return (
    <div className="px-2 py-3 text-sm">
      <p className="font-bold">Установить приложение</p>
      <p className="mt-0.5 text-text-soft">В Safari нажми «Поделиться» → «На экран Домой».</p>
    </div>
  );
  const messages = {
    accepted: 'Браузер начал установку.',
    dismissed: 'Установка отменена.',
    error: 'Не удалось открыть окно установки.',
  };
  return <p className="px-2 py-3 text-sm text-text-soft" role="status">{messages[installation.outcome] || 'Установка доступна через меню поддерживаемого браузера.'}</p>;
}

function About() {
  return (
    <Card className="grid gap-3">
      <Logo />
      <p className="text-sm text-text-soft">ЧекМудрец — помощник для учёта личных расходов по фотографиям чеков.</p>
      <ul className="list-disc pl-5 grid gap-1 text-sm">
        <li>Распознавай и сверяй чеки перед сохранением.</li>
        <li>Смотри историю и расходы по категориям.</li>
        <li>Сравнивай цены по своим покупкам.</li>
      </ul>
      <p className="text-sm font-bold">Учебный стартап-проект РТУ МИРЭА, команда №8</p>
      <p className="text-xs text-text-soft">Версия {version}</p>
    </Card>
  );
}

function downloadExport(data) {
  const date = new Date(data.exported_at);
  const day = [date.getFullYear(), date.getMonth() + 1, date.getDate()].map((part) => String(part).padStart(2, '0')).join('-');
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = `checkmudrets-export-${day}.json`;
  link.hidden = true;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30_000);
}

export default function Profile({ profile, userId, installation }) {
  const { signOut } = useAuth();
  const [screen, setScreen] = useState('');
  const [notice, setNotice] = useState('');
  const [failure, setFailure] = useState('');
  const [loading, setLoading] = useState('');
  const heading = useRef(null);
  const exportRequest = useRef(null);
  const leaving = useRef(false);

  useEffect(() => { heading.current?.focus(); }, [screen]);
  useEffect(() => () => exportRequest.current?.abort(), []);

  function open(next) {
    setNotice('');
    setScreen(next);
  }

  function saved(message) {
    setScreen('');
    setNotice(message);
  }

  async function download() {
    if (exportRequest.current) return;
    const request = new AbortController();
    exportRequest.current = request;
    setLoading('export');
    setFailure('');
    try {
      const data = await exportProfile(userId, request.signal);
      if (!request.signal.aborted) downloadExport(data);
    } catch {
      if (!request.signal.aborted) setFailure('Не удалось экспортировать данные. Попробуй ещё раз.');
    } finally {
      exportRequest.current = null;
      if (!request.signal.aborted) setLoading('');
    }
  }

  async function leave() {
    if (leaving.current) return;
    leaving.current = true;
    exportRequest.current?.abort();
    setLoading('logout');
    setFailure('');
    try { await signOut(); }
    catch {
      setFailure('Не удалось выйти. Попробуй ещё раз.');
      setLoading('');
    } finally { leaving.current = false; }
  }

  const document = PROFILE_DOCUMENTS.find(({ id }) => id === screen);
  const title = document?.title || ({
    name: 'Редактировать имя', password: 'Изменить пароль', delete: 'Удаление аккаунта', about: 'О проекте',
  })[screen] || 'Профиль';

  return (
    <div className="px-4 pt-5 pb-6 max-w-lg mx-auto flex flex-col gap-4">
      {screen && <Button size="sm" variant="ghost" className="self-start" onClick={() => setScreen('')}>
        <ArrowLeft size={16} aria-hidden="true" /> К профилю
      </Button>}
      <h1 ref={heading} tabIndex={-1} className="text-[28px] wrap-anywhere focus:outline-none">{title}</h1>
      {screen === 'name' && <NameForm initialName={profile.name} onSaved={saved} />}
      {screen === 'password' && <PasswordForm onSaved={saved} />}
      {screen === 'delete' && <DeleteAccountForm />}
      {screen === 'about' && <About />}
      {document && <Card className="grid gap-2">
        <p className="text-sm font-extrabold text-brand">Предварительный документ учебного проекта</p>
        <p className="text-sm text-text-soft">{document.text}</p>
        {document.version && <p className="text-xs text-text-muted">Версия {document.version}</p>}
      </Card>}
      {!screen && <>
        {notice && <p role="status" className="rounded-input bg-pill px-4 py-3 text-sm font-bold text-brand">{notice}</p>}
        <Card>
          <div className="flex items-center gap-4">
            <span aria-hidden="true" className="size-14 rounded-full bg-green text-text flex items-center justify-center text-xl font-extrabold shrink-0">
              {initials(profile.name) || <User size={24} />}
            </span>
            <div className="min-w-0">
              <p className="font-extrabold text-[17px] wrap-anywhere">{profile.name || 'Пользователь'}</p>
              {profile.email && <p className="text-xs text-text-soft wrap-anywhere">{profile.email}</p>}
              <p className="mt-1 text-xs text-text-muted">{memberSince(profile.created_at)}</p>
            </div>
          </div>
          <Button className="mt-4" variant="ghost" size="sm" onClick={() => open('name')}>
            <Pencil size={16} aria-hidden="true" /> Редактировать профиль
          </Button>
        </Card>

        <Achievements userId={userId} />
        <Settings title="Настройки аккаунта">
          <Setting icon={Pencil} onClick={() => open('name')}>Редактировать имя</Setting>
          <Setting icon={KeyRound} onClick={() => open('password')}>Изменить пароль</Setting>
        </Settings>
        <Settings title="Приложение">
          <Install installation={installation} />
          <Setting icon={Info} onClick={() => open('about')}>О проекте</Setting>
        </Settings>
        <Settings title="Данные и конфиденциальность">
          <Setting icon={FileDown} disabled={Boolean(loading)} onClick={download}>
            {loading === 'export' ? 'Готовим файл…' : 'Экспортировать мои данные'}
          </Setting>
          {PROFILE_DOCUMENTS.map(({ id, title: name }) => (
            <Setting key={id} icon={FileText} onClick={() => open(id)}>{name}</Setting>
          ))}
        </Settings>

        <section className="rounded-card border border-danger/25 bg-danger-bg px-4 py-1">
          <Setting icon={Trash2} danger onClick={() => open('delete')}>Удалить аккаунт</Setting>
        </section>
        {failure && <ErrorState message={failure} />}
        <Button variant="secondary" full disabled={loading === 'logout'} onClick={leave}>
          <LogOut size={18} aria-hidden="true" /> {loading === 'logout' ? 'Выходим…' : 'Выйти из аккаунта'}
        </Button>
        <p className="text-center text-xs text-text-muted">ЧекМудрец · {version}</p>
      </>}
    </div>
  );
}
