import { supabase } from './supabase';

const API_BASE = import.meta.env.VITE_API_URL.replace(/\/+$/, '');
export const apiConfigured = Boolean(API_BASE);

async function getSession(expectedUser) {
  const { data, error } = await supabase.auth.getSession();
  if (error) throw error;
  if (!data.session || (expectedUser && data.session.user.id !== expectedUser)) {
    throw new Error('Сессия изменилась. Войди снова.');
  }
  return data.session;
}

async function request(path, options = {}, session) {
  if (!apiConfigured) throw new Error('Настрой адрес API.');
  const current = session ?? await getSession();
  const headers = new Headers(options.headers);
  headers.set('Authorization', `Bearer ${current.access_token}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers, cache: 'no-store' });
  if (!response.ok) {
    if (response.status === 401) {
      const { data } = await supabase.auth.getSession();
      if (data.session?.access_token === current.access_token) {
        await supabase.auth.signOut({ scope: 'local' });
      }
    }
    const error = new Error(`Ошибка сервера (${response.status})`);
    error.status = response.status;
    error.detail = (await response.json().catch(() => null))?.detail;
    throw error;
  }
  return response.status === 204 ? null : response.json();
}

export async function getMe(userId, signal) {
  return request('/auth/me', { signal }, await getSession(userId));
}

export async function updateProfile(userId, name) {
  return request('/auth/me', {
    method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }),
  }, await getSession(userId));
}

export async function getProfileStats(userId, signal) {
  return request('/auth/me/stats', { signal }, await getSession(userId));
}

export async function exportProfile(userId, signal) {
  return request('/auth/me/export', { signal }, await getSession(userId));
}

export async function deleteProfile(userId) {
  return request('/auth/me', { method: 'DELETE' }, await getSession(userId));
}

export async function recordConsents(userId, consents, signal) {
  return request('/auth/consents', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ consents }),
    signal,
  }, await getSession(userId));
}

export async function recognizeReceipt(file, userId) {
  const session = await getSession(userId);
  const form = new FormData();
  form.append('file', file);
  return request('/receipts/recognize', { method: 'POST', body: form }, session);
}

export async function confirmReceipt(draftId, receipt, acceptWarnings, userId) {
  const session = await getSession(userId);
  return request(`/receipts/${draftId}/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ receipt, accept_warnings: acceptWarnings }),
  }, session);
}

export function getReceipts(limit = 20, signal) {
  return request(`/receipts?limit=${limit}`, { signal });
}

export function getStats(month = '', signal) {
  return request(month ? `/stats?month=${encodeURIComponent(month)}` : '/stats', { signal });
}

export function getAdvice({ personalize = false, signal } = {}) {
  return request(personalize ? '/advice?personalize=true' : '/advice', { signal });
}

export function getReport(signal) {
  return request('/report', { signal });
}
