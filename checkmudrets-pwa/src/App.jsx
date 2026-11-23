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
  const [userName, setUserName] = useState(getUserName());

  useEffect(() => {
    const name = getUserName();
    if (name) setUserName(name);
  }, [page]);

  const renderPage = () => {
    switch (page) {
      case 'home': return <Home onNavigate={setPage} userName={userName} />;
      case 'scan': return <Scan onNavigate={setPage} />;
      case 'history': return <History />;
      case 'stats': return <Stats />;
      case 'profile': return <Profile userName={userName} setUserName={setUserName} />;
      default: return <Home onNavigate={setPage} userName={userName} />;
    }
  };

  return (
    <div className="flex flex-col h-full bg-bg">
      <main className="flex-1 overflow-y-auto pb-20">
        {renderPage()}
      </main>
      <BottomNav current={page} onChange={setPage} />
    </div>
  );
}
