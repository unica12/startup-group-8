import { useState, useEffect } from 'react';
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
import History from './pages/History';
import Stats from './pages/Stats';
import Profile from './pages/Profile';

export default function App() {
  return <AuthProvider><AppGate /></AuthProvider>;
}

function AppGate() {
  const { session, account, reloadProfile, signOut } = useAuth();
  const [signOutError, setSignOutError] = useState(false);
  const [installPrompt, setInstallPrompt] = useState(null);

  useEffect(() => {
    function captureInstallPrompt(event) {
      event.preventDefault();
      setInstallPrompt(event);
    }
    const clearInstallPrompt = () => setInstallPrompt(null);
    window.addEventListener('beforeinstallprompt', captureInstallPrompt);
    window.addEventListener('appinstalled', clearInstallPrompt);
    return () => {
      window.removeEventListener('beforeinstallprompt', captureInstallPrompt);
      window.removeEventListener('appinstalled', clearInstallPrompt);
    };
  }, []);

  async function installApp() {
    setInstallPrompt(null);
    await installPrompt.prompt();
  }

  if (session === undefined || (session && !account)) {
    return <main className="grid h-full place-items-center px-4"><Loader mascot text="Проверяем сессию…" /></main>;
  }
  if (!session) return <AuthScreen />;
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
  return <BudgetApp key={session.user.id} userId={session.user.id} profile={account.profile} onInstall={installPrompt ? installApp : undefined} />;
}

function BudgetApp({ userId, profile, onInstall }) {
  const [page, setPage] = useState('home');

  const renderPage = () => {
    switch (page) {
      case 'scan': return <Scan onNavigate={setPage} />;
      case 'history': return <History onNavigate={setPage} />;
      case 'stats': return <Stats onNavigate={setPage} />;
      case 'profile': return <Profile profile={profile} onInstall={onInstall} />;
      default: return <Home onNavigate={setPage} userName={profile.name} userId={userId} />;
    }
  };

  return (
    <div className="flex flex-col h-full bg-bg">
      <main key={page} className="flex-1 min-h-0 overflow-y-auto pt-[env(safe-area-inset-top,0px)]">
        {renderPage()}
      </main>
      <BottomNav current={page} onChange={setPage} />
    </div>
  );
}
