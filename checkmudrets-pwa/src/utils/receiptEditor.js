const DECIMAL_FIELDS = new Set(['price', 'quantity', 'discount', 'total', 'package_size']);

function numericText(value) {
  return String(value ?? '').replace(/\s/g, '').replace(',', '.');
}

export function cents(value) {
  const normalized = numericText(value);
  if (!/^\d{1,10}(\.\d{1,2})?$/.test(normalized)) return null;
  const [whole, fraction = ''] = normalized.split('.');
  return Number(whole) * 100 + Number(fraction.padEnd(2, '0'));
}

export function editorPayload(data) {
  const clean = (fields) => Object.fromEntries(Object.entries(fields).map(([key, value]) => [
    key, DECIMAL_FIELDS.has(key) ? numericText(value) || null : String(value ?? '').trim() || null,
  ]));
  const { items, ...receipt } = data;
  return { ...clean(receipt), items: items.map(({ editorKey: _key, ...item }) => clean(item)) };
}

export function editSavedReceipt({ store_name, date, total, discount, items }) {
  return {
    store_name, date, total, discount,
    items: items.map(({ id, ...item }) => ({ ...item, editorKey: id })),
  };
}
