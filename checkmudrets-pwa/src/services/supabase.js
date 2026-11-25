import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL;
const key = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;
const storageKey = url && `sb-${new URL(url).hostname.split('.')[0]}-auth-token`;

export const supabase = url && key ? createClient(url, key, {
  auth: { storageKey, persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
}) : null;

export function forgetDeletedSession() {
  // Запасной путь, если Auth уже удалил пользователя и запрос выхода прервался.
  try {
    localStorage.removeItem(storageKey);
    localStorage.removeItem(`${storageKey}-user`);
  } catch { /* Браузер ограничил доступ к хранилищу. */ }
}

export function emailRedirectUrl() {
  return new URL(import.meta.env.BASE_URL, window.location.origin).href;
}
