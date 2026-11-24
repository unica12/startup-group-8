import { useEffect, useRef, useState } from 'react';
import { getMe, recordConsents } from '../services/api';
import { emailRedirectUrl, supabase } from '../services/supabase';
import { acceptedVersions } from './documents';
import { AuthContext } from './context';
const pendingKey = (id) => `checkmudrets:pending-consents:${id}`;

function pendingConsents(id, remove = false) {
  try {
    const key = pendingKey(id);
    if (remove) return localStorage.removeItem(key);
    return JSON.parse(localStorage.getItem(key));
  } catch {
    return null;
  }
}

export default function AuthProvider({ children }) {
  const [session, setSession] = useState(supabase ? undefined : null);
  const [account, setAccount] = useState(null);
  const [attempt, setAttempt] = useState(0);
  const lastUser = useRef(undefined);
  const userId = session?.user.id;

  useEffect(() => {
    if (!supabase) return;
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, next) => {
      if (lastUser.current !== next?.user.id) {
        lastUser.current = next?.user.id;
        setAccount(null);
        setAttempt((value) => value + 1);
      }
      setSession(next);
    });
    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (!userId) return;
    const controller = new AbortController();
    const { signal } = controller;

    async function load() {
      try {
        let profile = await getMe(userId, signal);
        const pending = pendingConsents(userId);
        if (!profile.consents_complete && pending && Object.entries(acceptedVersions).every(([id, version]) => pending[id] === version)) {
          try {
            profile = await recordConsents(userId, acceptedVersions, signal);
          } catch (error) {
            if (error.status !== 422) throw error;
          }
        }
        if (pending) pendingConsents(userId, true);
        if (!signal.aborted) setAccount({ userId, profile });
      } catch {
        if (!signal.aborted) setAccount({ userId, error: true });
      }
    }

    load();
    return () => controller.abort();
  }, [userId, attempt]);

  function reloadProfile() {
    setAccount(null);
    setAttempt((value) => value + 1);
  }

  async function signUp({ name, email, password }) {
    const { data, error } = await supabase.auth.signUp({
      email, password, options: { data: { name }, emailRedirectTo: emailRedirectUrl() },
    });
    if (error) throw error;
    if (data.user?.id && data.user.identities?.length !== 0) {
      try {
        localStorage.setItem(pendingKey(data.user.id), JSON.stringify(acceptedVersions));
      } catch {
        // Если браузер не сохранил выбор, его можно подтвердить после входа.
      }
    }
    if (data.session) reloadProfile();
    return Boolean(data.session);
  }

  async function signIn(email, password) {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
    reloadProfile();
  }

  async function resendEmail(email) {
    const { error } = await supabase.auth.resend({ type: 'signup', email, options: { emailRedirectTo: emailRedirectUrl() } });
    if (error) throw error;
  }

  async function signOut() {
    const { error } = await supabase.auth.signOut({ scope: 'local' });
    if (error) throw error;
    setAccount(null);
  }

  async function confirmConsents() {
    const profile = await recordConsents(userId, acceptedVersions);
    pendingConsents(userId, true);
    setAccount({ userId, profile });
  }

  return (
    <AuthContext.Provider value={{
      session, account: account?.userId === userId ? account : null, configured: Boolean(supabase),
      signUp, signIn, resendEmail, signOut, reloadProfile, confirmConsents,
    }}>
      {children}
    </AuthContext.Provider>
  );
}
