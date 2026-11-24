const API_BASE = import.meta.env.VITE_API_URL || 'https://checkmudrets-api.onrender.com';

function getDeviceId() {
  let id = localStorage.getItem('checkmudrets_device_id');
  if (!id) {
    const randomId = crypto.randomUUID?.() ?? Array.from(
      crypto.getRandomValues(new Uint8Array(16)),
      (byte) => byte.toString(16).padStart(2, '0'),
    ).join('');
    id = `web_${randomId}`;
    localStorage.setItem('checkmudrets_device_id', id);
  }
  return id;
}

function getUserName() {
  return localStorage.getItem('checkmudrets_user_name') || '';
}

function setUserName(name) {
  localStorage.setItem('checkmudrets_user_name', name);
}

const LAST_ADVICE_KEY = 'checkmudrets_last_advice';

/** Последний mini_advice после скана — показываем на главной */
function getLastAdvice() {
  return localStorage.getItem(LAST_ADVICE_KEY) || '';
}

function setLastAdvice(text) {
  if (text) localStorage.setItem(LAST_ADVICE_KEY, text);
}

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const error = new Error(`Ошибка сервера (${res.status})`);
    error.status = res.status;
    throw error;
  }
  return res.json();
}

export async function register(name) {
  const deviceId = getDeviceId();
  return request('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ device_id: deviceId, name }),
  });
}

export async function uploadReceipt(file) {
  const form = new FormData();
  form.append('file', file);
  form.append('device_id', getDeviceId());
  const res = await request('/receipts', { method: 'POST', body: form });
  if (res?.success && res.mini_advice) setLastAdvice(res.mini_advice);
  return res;
}

export async function getReceipts(limit = 20, signal) {
  return request(`/receipts?device_id=${getDeviceId()}&limit=${limit}`, { signal });
}

export async function getStats(month = '', signal) {
  const q = month ? `&month=${month}` : '';
  return request(`/stats?device_id=${getDeviceId()}${q}`, { signal });
}

export async function getAdvice() {
  return request(`/advice?device_id=${getDeviceId()}`);
}

export async function getReport(signal) {
  return request(`/report?device_id=${getDeviceId()}`, { signal });
}

export { getDeviceId, getUserName, setUserName, getLastAdvice, API_BASE };
