import { lazy, Suspense, useState } from 'react';
import AuthProvider from './auth/AuthProvider';
import { useAuth } from './auth/context';
import AuthLayout from './auth/AuthLayout';
import AuthScreen from './auth/AuthScreen';
import ConsentScreen from './auth/ConsentScreen';
import BottomNav from './components/BottomNav';
import ErrorState from './components/ErrorState';
import Loader from './components/Loader';
import { Button } from './components/ui';
import Home from './pages/Home';
import Scan from './pages/Scan';
import usePwaInstall from './utils/usePwaInstall';

const Profile = lazy(() => import('./pages/Profile'));
const Stats = lazy(() => import('./pages/Stats'));
const History = lazy(() => import('./pages/History'));

export default function App() {
  return <AuthProvider><AppGate /></AuthProvider>;
}

function AppGate() {
  const { session, account, configured, reloadProfile, signOut } = useAuth();
  const [signOutError, setSignOutError] = useState(false);
  const installation = usePwaInstall();

  if (!configured) return <AuthScreen />;
  if (session === undefined || (session && !account)) {
    return <main className="grid h-full place-items-center px-4"><Loader mascot text="Проверяем сессию…" /></main>;
  }
  if (!session) return <AuthScreen />;
  if (account.deletionPending) return <DeletionPending key={session.user.id} />;
  if (account.error) {
    return (
      <AuthLayout title="Аккаунт">
        <div className="grid gap-3">
          <ErrorState message={signOutError ? 'Не удалось выйти. Попробуй ещё раз.' : 'Не удалось проверить профиль.'} onRetry={reloadProfile} />
          <Button variant="ghost" onClick={() => signOut().catch(() => setSignOutError(true))}>Выйти</Button>
        </div>
      </AuthLayout>
    );
  }
  if (!account.profile.consents_complete) return <ConsentScreen key={session.user.id} />;
  return <BudgetApp key={session.user.id} userId={session.user.id} profile={account.profile} installation={installation} />;
}

function DeletionPending() {
  const { deleteAccount, signOut } = useAuth();
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState('');

  async function run(action, error) {
    if (busy) return;
    setFailure('');
    setBusy(true);
    try { await action(); } catch { setFailure(error); } finally { setBusy(false); }
  }

  return (
    <AuthLayout title="Удаление аккаунта" intro="Данные ЧекМудреца удалены. Подтверждение от Supabase Auth ещё не получено.">
      <div className="grid gap-3">
        {failure && <ErrorState message={failure} />}
        <Button disabled={busy} onClick={() => run(() => deleteAccount(), 'Завершить удаление пока не удалось. Попробуй позже.')}>
          {busy ? 'Подожди…' : 'Повторить удаление'}
        </Button>
        <Button variant="ghost" disabled={busy} onClick={() => run(signOut, 'Не удалось выйти. Попробуй ещё раз.')}>Выйти</Button>
      </div>
    </AuthLayout>
  );
}

function BudgetApp({ userId, profile, installation }) {
  const [page, setPage] = useState('home');
  const [receiptsRevision, setReceiptsRevision] = useState(0);
  const [statsPeriod, setStatsPeriod] = useState(null);
  const [adviceOpened, setAdviceOpened] = useState(false);

  function refreshReceipts() {
    setReceiptsRevision((revision) => revision + 1);
  }

  function navigate(target, period) {
    if (period) setStatsPeriod(period);
    setPage(target);
  }

  const renderPage = () => {
    switch (page) {
      case 'scan': return <Scan onNavigate={setPage} userId={userId} onReceiptsChanged={refreshReceipts} />;
      case 'history': return <History onNavigate={setPage} userId={userId} receiptsRevision={receiptsRevision} onReceiptsChanged={refreshReceipts} />;
      case 'stats': return <Stats onNavigate={setPage} receiptsRevision={receiptsRevision} period={statsPeriod}
        onPeriodChange={setStatsPeriod} adviceOpened={adviceOpened} onOpenAdvice={() => setAdviceOpened(true)} />;
      case 'profile': return <Profile profile={profile} userId={userId} installation={installation} receiptsRevision={receiptsRevision} />;
      default: return <Home onNavigate={navigate} userName={profile.name} receiptsRevision={receiptsRevision} />;
    }
  };

  return (
    <div className="flex flex-col h-full bg-bg">
      <main key={page} className="flex-1 min-h-0 overflow-y-auto pt-[env(safe-area-inset-top,0px)]">
        <Suspense fallback={<Loader text="Загрузка…" />}>{renderPage()}</Suspense>
      </main>
      <BottomNav current={page} onChange={setPage} />
    </div>
  );
}
