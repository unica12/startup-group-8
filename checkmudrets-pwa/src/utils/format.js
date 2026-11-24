const moneyFmt = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 });

/** 1234.5 → «1 235 ₽» (обычный пробел как разделитель тысяч) */
export function formatMoney(n) {
  return moneyFmt.format(Math.round(Number(n) || 0)).replace(/ | /g, ' ') + ' ₽';
}

export const MONTHS_NOMINATIVE = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь',
];

/** «Расходы за ноябрь» */
const MONTHS_ACCUSATIVE = [
  'январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
  'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь',
];
export function monthAccusative(monthIndex) {
  return MONTHS_ACCUSATIVE[monthIndex];
}

/** «2026-11-20» → «20 нояб.» */
export function formatDateShort(iso) {
  if (!iso) return '—';
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
}

/** 1 чек, 2 чека, 5 чеков */
export function plural(n, [one, few, many]) {
  const m10 = n % 10;
  const m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
  return many;
}

export const CHART_COLORS = ['#2E7D32', '#8BE04E', '#F2D84C', '#B9CEC0', '#58CC02', '#46A302'];

/**
 * by_category из /stats → сегменты для кольцевой диаграммы.
 * Первые (max-1) категорий как есть, остальные — в «Прочее».
 */
export function toChartSegments(byCategory = [], max = 5) {
  const list = byCategory.filter((c) => c.amount > 0);
  const total = list.reduce((s, c) => s + c.amount, 0);
  if (!total) return [];
  let head = list;
  if (list.length > max) {
    head = list.slice(0, max - 1);
    const restAmount = list.slice(max - 1).reduce((s, c) => s + c.amount, 0);
    head = [...head, { category: 'Прочее', amount: restAmount, grouped: true }];
  }
  return head.map((c, i) => ({
    label: c.category,
    key: c.grouped ? 'grouped' : `category:${c.category}`,
    amount: c.amount,
    percent: Math.round((c.amount / total) * 100),
    color: CHART_COLORS[i % CHART_COLORS.length],
  }));
}
