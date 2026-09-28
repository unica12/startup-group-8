'use strict';
(function () {
  const goal = (name) => { if (typeof window.ym === 'function') window.ym(112876432, 'reachGoal', name); };
  document.querySelectorAll('a').forEach(link => {
    if (link.href.startsWith('https://t.me/')) link.addEventListener('click', () => goal('telegram_click'));
    else if (link.getAttribute('href') === '#cta') link.addEventListener('click', () => goal('cta_click'));
    else if (link.getAttribute('href') === '#demo') link.addEventListener('click', () => goal('demo_open'));
  });
  if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.remove('reveal-pending'); observer.unobserve(entry.target); }
    }), {threshold: 0.08});
    document.querySelectorAll('.reveal').forEach(el => { el.classList.add('reveal-pending'); observer.observe(el); });
  }
  const range = document.getElementById('budget');
  const presets = {everyday:[42,26,18,14], travel:[28,17,40,15]};
  const labels = ['Продукты','Кафе','Транспорт','Прочее'];
  const colors = ['#2e7d32','#8be04e','#f2d84c','#b9cec0'];
  let preset = 'everyday';
  const money = value => new Intl.NumberFormat('ru-RU').format(value) + ' ₽';
  function render() {
    const value = Number(range.value), shares = presets[preset];
    document.getElementById('budget-value').textContent = money(value);
    document.getElementById('ring-total').textContent = money(value);
    range.setAttribute('aria-valuetext', money(value));
    range.style.setProperty('--progress', ((value - 5000) / 95000 * 100) + '%');
    let offset = 0;
    document.querySelector('.budget-ring').style.background = 'conic-gradient(' + shares.map((share,i) => {
      const segment = colors[i] + ' ' + offset + '% ' + (offset + share) + '%'; offset += share; return segment;
    }).join(',') + ')';
    document.querySelector('.budget-ring').setAttribute('aria-label', labels.map((label,i) => label + ': ' + shares[i] + '%').join(', '));
    document.getElementById('budget-legend').replaceChildren(...shares.map((share,i) => {
      const li = document.createElement('li'), title = document.createElement('span'), amount = document.createElement('strong');
      li.style.setProperty('--category-color', colors[i]); title.textContent = labels[i] + ' · ' + share + '%'; amount.textContent = money(value * share / 100); li.append(title, amount); return li;
    }));
  }
  range.addEventListener('input', render);
  range.addEventListener('change', () => goal('budget_interaction'));
  document.querySelectorAll('[data-preset]').forEach(button => button.addEventListener('click', () => {
    preset = button.dataset.preset;
    document.querySelectorAll('[data-preset]').forEach(el => el.setAttribute('aria-pressed', String(el === button)));
    render(); goal('budget_interaction');
  }));
  render();
})();
