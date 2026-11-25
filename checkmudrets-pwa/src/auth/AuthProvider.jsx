import { useEffect, useRef, useState } from 'react';
import { apiConfigured, deleteProfile, getMe, recordConsents, updateProfile } from '../services/api';
import { emailRedirectUrl, forgetDeletedSession, supabase } from '../services/supabase';
import { acceptedVersions } from './documents';
import { AuthContext } from './context';
const pendingKey = (id) => `checkmudrets:pending-consents:${id}`;

async function clearLocalAccountData(id) {
  try {
    for (const key of ['checkmudrets_device_id', 'checkmudrets_user_name', 'checkmudrets_last_advice',
      pendingKey(id), `checkmudrets:last-advice:${id}`]) {
      localStorage.removeItem(key);
    }
  } catch { /* Браузер ограничил доступ к хранилищу. */ }
  await Promise.allSettled(['api-receipts', 'api-stats'].map((name) => window.caches?.delete(name)));
}

function deletionPending(error) {
  return error.detail?.code === 'account_deletion_pending';
}

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
        if (lastUser.current) void clearLocalAccountData(lastUser.current);
        lastUser.current = next?.user.id;
        setAccount(null);
        setAttempt((value) => value + 1);
      }
      setSession(next);
    });
    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (!userId || !apiConfigured) return;
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
      } catch (error) {
        if (!signal.aborted) setAccount(deletionPending(error) ? { userId, deletionPending: true } : { userId, error: true });
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
    if (userId) await clearLocalAccountData(userId);
    setAccount(null);
  }

  async function saveName(name) {
    const profile = await updateProfile(userId, name);
    if (lastUser.current === userId) setAccount({ userId, profile });
  }

  async function verifyPassword(password) {
    const email = session?.user.email;
    if (!email) throw new Error('Для повторного входа нужен email.');
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
    if (data.user?.id !== userId || lastUser.current !== userId) throw new Error('Сессия изменилась.');
  }

  async function changePassword(currentPassword, password) {
    await verifyPassword(currentPassword);
    const { error } = await supabase.auth.updateUser({ password, current_password: currentPassword });
    if (error) throw error;
  }

  async function deleteAccount(password) {
    if (password !== undefined) await verifyPassword(password);
    try {
      await deleteProfile(userId);
    } catch (error) {
      if (deletionPending(error) && lastUser.current === userId) setAccount({ userId, deletionPending: true });
      throw error;
    }
    try {
      const { data, error } = await supabase.auth.getSession();
      if (error) throw error;
      if (data.session?.user.id === userId) await signOut();
      if (!data.session && lastUser.current === userId) setSession(null);
    } catch {
      if (lastUser.current === userId) {
        forgetDeletedSession();
        setSession(null);
        setAccount(null);
      }
    }
    await clearLocalAccountData(userId);
  }

  async function confirmConsents() {
    const profile = await recordConsents(userId, acceptedVersions);
    pendingConsents(userId, true);
    setAccount({ userId, profile });
  }

  return (
    <AuthContext.Provider value={{
      session, account: account?.userId === userId ? account : null, configured: Boolean(supabase) && apiConfigured,
      signUp, signIn, resendEmail, signOut, reloadProfile, confirmConsents, saveName, changePassword, deleteAccount,
    }}>
      {children}
    </AuthContext.Provider>
  );
}
