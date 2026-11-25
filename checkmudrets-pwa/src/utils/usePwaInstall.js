import { useEffect, useState } from 'react';

const display = '(display-mode: standalone)';

function standalone() {
  return navigator.standalone === true || window.matchMedia(display).matches;
}

function iosSafari() {
  const agent = navigator.userAgent;
  const ios = /iPhone|iPad|iPod/.test(agent) || (/Macintosh/.test(agent) && navigator.maxTouchPoints > 1);
  return ios && /Safari/.test(agent) && !/CriOS|FxiOS|EdgiOS|OPiOS|GSA/.test(agent);
}

export default function usePwaInstall() {
  const [installed, setInstalled] = useState(standalone);
  const [prompt, setPrompt] = useState(null);
  const [outcome, setOutcome] = useState('');

  useEffect(() => {
    const mode = window.matchMedia(display);
    function capture(event) {
      event.preventDefault();
      setPrompt(event);
      setOutcome('');
    }
    function installedEvent() {
      setInstalled(true);
      setPrompt(null);
    }
    const displayChanged = () => setInstalled(standalone());
    mode.addEventListener('change', displayChanged);
    window.addEventListener('beforeinstallprompt', capture);
    window.addEventListener('appinstalled', installedEvent);
    return () => {
      mode.removeEventListener('change', displayChanged);
      window.removeEventListener('beforeinstallprompt', capture);
      window.removeEventListener('appinstalled', installedEvent);
    };
  }, []);

  async function request() {
    if (!prompt) return;
    setPrompt(null);
    try {
      const result = await prompt.prompt();
      const choice = result?.outcome ? result : await prompt.userChoice;
      setOutcome(choice.outcome);
    } catch {
      setOutcome('error');
    }
  }

  return { installed, available: Boolean(prompt), ios: iosSafari(), outcome, request };
}
