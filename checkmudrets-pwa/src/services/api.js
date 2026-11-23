const API_BASE = import.meta.env.VITE_API_URL || 'https://checkmudrets-api.onrender.com';

function getDeviceId() {
  let id = localStorage.getItem('checkmudrets_device_id');
  if (!id) {
    id = 'web_' + crypto.randomUUID();
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

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...options.headers },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export async function register(name) {
  const deviceId = getDeviceId();
  setUserName(name);
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
  return request('/receipts', { method: 'POST', body: form });
}

export async function getReceipts(limit = 20) {
  return request(`/receipts?device_id=${getDeviceId()}&limit=${limit}`);
}

export async function getStats(month = '') {
  const q = month ? `&month=${month}` : '';
  return request(`/stats?device_id=${getDeviceId()}${q}`);
}

export async function getAdvice() {
  return request(`/advice?device_id=${getDeviceId()}`);
}

export async function getReport() {
  return request(`/report?device_id=${getDeviceId()}`);
}

export { getDeviceId, getUserName, setUserName, API_BASE };
