import { useState, useEffect } from 'react';
import { getUserName } from './services/api';
import BottomNav from './components/BottomNav';
import Home from './pages/Home';
import Scan from './pages/Scan';
import History from './pages/History';
import Stats from './pages/Stats';
import Profile from './pages/Profile';

export default function App() {
  const [page, setPage] = useState('home');
  const [userName, setUserName] = useState(getUserName);
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

  const renderPage = () => {
    switch (page) {
      case 'home': return <Home onNavigate={setPage} userName={userName} />;
      case 'scan': return <Scan onNavigate={setPage} />;
      case 'history': return <History onNavigate={setPage} />;
      case 'stats': return <Stats onNavigate={setPage} />;
      case 'profile': return <Profile userName={userName} setUserName={setUserName} onInstall={installPrompt ? installApp : undefined} />;
      default: return <Home onNavigate={setPage} userName={userName} />;
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
