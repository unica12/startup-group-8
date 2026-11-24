"""Инсайты из подтверждённых покупок. Все расчёты независимы от GPT."""
from __future__ import annotations

import re
import unicodedata
from calendar import monthrange
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from database.models import Receipt
from schemas.models import Insight, InsightMetric
from services.receipt_validation import CENT, ZERO, as_decimal, cents

UNIT_SCALE = {"кг": ("кг", Decimal(1)), "г": ("кг", Decimal("0.001")),
              "л": ("л", Decimal(1)), "мл": ("л", Decimal("0.001"))}
SIZE_PATTERN = re.compile(r"(?<![\d.,])(\d+(?:[.,]\d+)?)\s*(кг|г|мл|л)\b")
EMPTY_MESSAGE = (
    "Когда накопятся датированные чеки, здесь появятся покупательские привычки и сравнение расходов. "
    "Для сравнения цен помогут повторные покупки с читаемыми названиями и указанными единицами."
)

# GPT выбирает действие для уже посчитанного факта. Все цифры и утверждения остаются на стороне Python.
ACTIONS = {
    "store_comparison": (
        "Сверь цену именно этого товара в обоих магазинах перед следующей покупкой.",
        "Если оба магазина по пути, проверь наличие и цену нужной упаковки перед походом.",
    ),
    "price_change": (
        "При следующей покупке сохрани чек, чтобы понять, разовое ли это изменение.",
        "Сравни ценник перед следующей покупкой той же упаковки.",
    ),
    "unit_price": (
        "Сравни цену за ту же единицу веса или объёма на ценниках.",
        "Перед покупкой упаковки проверь цену за единицу веса или объёма и удобный для тебя размер.",
    ),
    "shopping_frequency": (
        "Посмотри, какие покупки в этом магазине удобно объединить в один поход.",
        "Используй самые частые покупки как основу следующего списка.",
    ),
    "category_change": (
        "Открой чеки в изменившихся категориях и проверь, были ли там разовые покупки.",
        "Сверь свои чеки за оба периода перед планированием следующего бюджета.",
    ),
    "growth_driver": (
        "Начни проверку роста расходов с чеков этой категории.",
        "Если расходы этой категории повторяются, заложи их в следующий бюджет заранее.",
    ),
    "forecast": (
        "Сверь оценку с бюджетом и отдельно учти известные крупные покупки впереди.",
        "Сравни эту оценку с запланированным бюджетом и проверь её после новых покупок.",
    ),
    "savings": (
        "Для следующей запланированной покупки проверь цену в обоих магазинах и учти дорогу.",
        "Проверь актуальные цены и сравни возможную разницу со стоимостью отдельного похода.",
    ),
}


def amount_text(value: Decimal) -> str:
    value = cents(value)
    return f"{value:,.2f}".rstrip("0").rstrip(".").replace(",", " ").replace(".", ",")


def rubles(value: Decimal) -> str:
    return f"{amount_text(value)} ₽"


def canonical(value: str | None) -> str:
    return " ".join(unicodedata.normalize("NFKC", value or "").casefold().split())


def insight(kind, title, observation, value, unit, label, evidence, savings=None, confidence="medium"):
    return Insight(
        type=kind, title=title, observation=observation, recommendation=ACTIONS[kind][0],
        metric=InsightMetric(value=cents(value), unit=unit, label=label),
        evidence=evidence, estimated_savings=cents(savings) if savings is not None else None,
        confidence=confidence,
    )


@dataclass(frozen=True)
class Purchase:
    receipt_id: int
    day: date
    store: str
    title: str
    exact_key: tuple
    metric_key: tuple | None
    measure: str
    quantity: Decimal
    paid: Decimal
    metric_quantity: Decimal | None
    package_measure: Decimal | None

    @property
    def price(self) -> Decimal:
        return self.paid / self.quantity

    @property
    def metric_price(self) -> Decimal:
        return self.paid / self.metric_quantity


def purchases(receipts, today):
    result = []
    for receipt in receipts:
        if not receipt.price_comparable or receipt.discount or not receipt.store_name or not receipt.date:
            continue
        if not 0 <= (today - receipt.date).days < 90:
            continue
        for line in receipt.items:
            name, brand = canonical(line.name), canonical(line.brand)
            if line.unit not in UNIT_SCALE and line.unit != "шт":
                continue
            if not line.quantity or line.quantity < 0 or line.price is None or not line.total or line.total <= 0:
                continue
            package_unit = UNIT_SCALE.get(line.package_unit)
            if line.unit == "шт" and (not package_unit or not line.package_size):
                continue
            package_size = as_decimal(line.package_size) * package_unit[1] if package_unit and line.package_size else None
            # Между магазинами сопоставляем маркированные товары и явно названные сорта весовых овощей/фруктов.
            bulk_produce = line.category == "Овощи/Фрукты" and line.unit in ("кг", "г") and len(re.findall(r"[а-яa-zё]{3,}", name)) >= 2
            if not name or not brand and not bulk_produce:
                continue
            measure, scale = UNIT_SCALE.get(line.unit, ("шт", Decimal(1)))
            quantity = as_decimal(line.quantity) * scale
            exact_key = (brand, name, line.category, measure, package_unit[0] if package_unit else None, package_size)
            metric_quantity, metric_key = None, None
            if measure != "шт":
                metric_quantity = quantity
                metric_key = (brand, name, line.category, measure)
            elif package_size:
                def remove_size(match):
                    printed_unit, factor = UNIT_SCALE[match[2]]
                    printed_size = as_decimal(match[1].replace(",", ".")) * factor
                    return "" if printed_unit == package_unit[0] and printed_size == package_size else match[0]

                comparable_name = canonical(SIZE_PATTERN.sub(remove_size, name))
                metric_key = (brand, comparable_name, line.category, package_unit[0])
                metric_quantity = quantity * package_size
            result.append(Purchase(
                receipt.id, receipt.date, receipt.store_name.strip(), line.name, exact_key, metric_key,
                measure, quantity, cents(as_decimal(line.total)), metric_quantity, package_size,
            ))
    return sorted(result, key=lambda row: (row.day, row.receipt_id))


def latest_by_store(group):
    latest = {}
    for row in group:
        latest[canonical(row.store)] = row
    return list(latest.values())


def observed(row, per_metric=False):
    value = row.metric_price if per_metric else row.price
    unit = row.metric_key[-1] if per_metric else row.measure
    return f"{row.store}, {row.day:%d.%m.%Y} · {rubles(value)} за {unit}"


def price_insights(receipts: list[Receipt], today: date, focus_receipt_id: int | None = None) -> list[Insight]:
    exact, metric = defaultdict(list), defaultdict(list)
    for row in purchases(receipts, today):
        exact[row.exact_key].append(row)
        if row.metric_key:
            metric[row.metric_key].append(row)
    best = {}

    def offer(kind, delta, title, observation, unit, label, evidence, savings=None, confidence="medium"):
        if cents(abs(delta)) >= CENT and (kind not in best or abs(delta) > abs(best[kind][0])):
            best[kind] = delta, insight(kind, title, observation, delta, unit, label, evidence, savings, confidence)

    for group in exact.values():
        recent = [row for row in group if (today - row.day).days < 30]
        stores = latest_by_store(recent)
        for expensive in stores:
            if focus_receipt_id is not None and expensive.receipt_id != focus_receipt_id:
                continue
            alternatives = [row for row in stores if canonical(row.store) != canonical(expensive.store)
                            and abs((row.day - expensive.day).days) <= 14 and row.price < expensive.price]
            if not alternatives:
                continue
            cheaper = min(alternatives, key=lambda row: row.price)
            delta = expensive.price - cheaper.price
            evidence = [observed(expensive), observed(cheaper)]
            offer("store_comparison", delta, "Цены в разных магазинах",
                  f"«{expensive.title}» обошёлся дешевле в магазине «{cheaper.store}» по двум недавним чекам.",
                  f"₽/{expensive.measure}", "Разница в ценах", evidence)
            visits = [row for row in recent if canonical(row.store) == canonical(expensive.store) and row.price > cheaper.price]
            count = len({row.receipt_id for row in visits})
            if count >= 2 and focus_receipt_id is None:
                savings = sum(((row.price - cheaper.price) * row.quantity for row in visits), ZERO)
                offer("savings", savings, "Возможная экономия",
                      f"«{expensive.title}» есть в {count} чеках за последние 30 дней из магазина «{expensive.store}». "
                      f"Оценка использует фактический объём этих покупок и наблюдавшуюся цену в «{cheaper.store}».",
                      "₽", "Оценка по покупкам за 30 дней", evidence, savings=savings)

        if focus_receipt_id is None:
            by_store = defaultdict(list)
            for row in group:
                by_store[canonical(row.store)].append(row)
            for rows in by_store.values():
                first, last = rows[0], rows[-1]
                if (last.day - first.day).days >= 7:
                    delta = last.price - first.price
                    offer("price_change", delta, "Изменение цены",
                          f"Цена «{last.title}» {('выросла' if delta > 0 else 'снизилась')} в чеках магазина «{last.store}».",
                          f"₽/{last.measure}", "Изменение цены", [observed(first), observed(last)],
                          confidence="high" if len({row.day for row in rows}) >= 3 else "medium")

    if focus_receipt_id is not None:
        return [best["store_comparison"][1]] if "store_comparison" in best else []

    for key, group in metric.items():
        # Разные размеры или способы фасовки дают дополнительное сравнение цены за кг/л.
        latest = {}
        for row in group:
            if (today - row.day).days < 30:
                latest[(canonical(row.store), row.package_measure, row.measure)] = row
        rows = sorted(latest.values(), key=lambda row: row.metric_price)
        for high in reversed(rows):
            low = next((row for row in rows if row.package_measure != high.package_measure
                        and abs((row.day - high.day).days) <= 14), None)
            if low and high.metric_price > low.metric_price:
                offer("unit_price", high.metric_price - low.metric_price, "Цена за вес или объём",
                      f"«{low.title}» стоил дешевле за {key[-1]}, чем «{high.title}», в сопоставимых чеках.",
                      f"₽/{key[-1]}", "Разница в пересчёте", [observed(low, True), observed(high, True)])
    return [best[kind][1] for kind in ("savings", "store_comparison", "price_change", "unit_price") if kind in best]


def window(receipts, start, end):
    return [receipt for receipt in receipts if receipt.date and start <= receipt.date < end]


def coverage(rows, distinct_days, span):
    days = {receipt.date for receipt in rows}
    return len(days) >= distinct_days and (max(days) - min(days)).days >= span


def period_insights(receipts, today):
    recent_start = today - timedelta(days=30)
    previous_start = recent_start - timedelta(days=30)
    recent = window(receipts, recent_start, today)
    previous = window(receipts, previous_start, recent_start)
    result = []

    visits, store_names, categories = defaultdict(set), {}, Counter()
    for receipt in recent:
        store = canonical(receipt.store_name)
        if store:
            visits[store].add(receipt.date)
            store_names[store] = receipt.store_name
        categories.update({item.category for item in receipt.items if item.category})
    if visits:
        store, days = max(visits.items(), key=lambda entry: len(entry[1]))
        if len(days) >= 3:
            evidence = [f"{recent_start:%d.%m.%Y}–{today - timedelta(days=1):%d.%m.%Y} · {len(recent)} чеков во всех магазинах"]
            purchase_receipts, titles = defaultdict(set), {}
            for purchase in purchases(recent, today):
                purchase_receipts[purchase.exact_key].add(purchase.receipt_id)
                titles[purchase.exact_key] = purchase.title
            frequent = max(purchase_receipts, key=lambda key: len(purchase_receipts[key]), default=None)
            if frequent is not None and len(purchase_receipts[frequent]) >= 2:
                evidence.append(f"«{titles[frequent]}» есть в {len(purchase_receipts[frequent])} чеках за этот период.")
            elif categories:
                name, count = categories.most_common(1)[0]
                evidence.append(f"«{name}» есть в {count} чеках за этот период.")
            result.append(insight(
                "shopping_frequency", "Покупательские привычки",
                f"Больше всего дней с покупками в одном магазине пришлось на «{store_names[store]}».",
                Decimal(len(days)), "дн.", "Дней с чеками этого магазина", evidence, confidence="high",
            ))

    def usable(rows):
        return [receipt for receipt in rows if receipt.price_comparable is not False and not receipt.discount]

    old, new = usable(previous), usable(recent)
    if coverage(old, 3, 14) and coverage(new, 3, 14):
        def totals(rows):
            by_cat = defaultdict(Decimal)
            for receipt in rows:
                for item in receipt.items:
                    by_cat[item.category] += cents(as_decimal(item.total))
            return by_cat

        before, after = totals(old), totals(new)
        change = {key: after[key] - before[key] for key in sorted(before.keys() | after.keys())}
        moved = sorted((key for key in change if change[key]), key=lambda key: -abs(change[key]))
        dates = f"{previous_start:%d.%m}–{recent_start - timedelta(days=1):%d.%m} и {recent_start:%d.%m}–{today - timedelta(days=1):%d.%m}"
        if moved:
            net = sum(change.values(), ZERO)
            result.append(insight(
                "category_change", "Изменение расходов по категориям",
                f"Сравнение учтённых покупок за два периода по 30 дней: {dates}.",
                net, "₽", "Общее изменение по категориям",
                [f"{key} · {rubles(before[key])} → {rubles(after[key])}" for key in moved[:3]],
            ))
            driver = max(moved, key=change.get)
            if net > 0 and change[driver] > 0:
                gross_growth = sum((value for value in change.values() if value > 0), ZERO)
                result.append(insight(
                    "growth_driver", "Что увеличило расходы",
                    f"«{driver}» дал наибольшую прибавку среди выросших категорий.",
                    change[driver], "₽", "Вклад категории в рост",
                    [f"{driver} · {rubles(before[driver])} → {rubles(after[driver])}",
                     f"Сумма прибавок выросших категорий · {rubles(gross_growth)}"],
                ))

    month_start = today.replace(day=1)
    previous_month_start = (month_start - timedelta(days=1)).replace(day=1)
    prior_month = window(receipts, previous_month_start, month_start)
    current = window(receipts, month_start, today)
    elapsed = today.day - 1
    days_left = monthrange(today.year, today.month)[1] - today.day
    if elapsed >= 10 and days_left and coverage(prior_month, 6, 20) and coverage(current, 4, 7):
        recorded = sum((cents(as_decimal(row.total)) for row in current), ZERO)
        already_today = sum((cents(as_decimal(row.total)) for row in receipts if row.date == today), ZERO)
        pace = recorded / elapsed
        if pace > 0:
            result.append(insight(
                "forecast", "Прогноз на месяц",
                "Оценка предполагает, что средний темп записанных расходов сохранится до конца месяца.",
                recorded + already_today + pace * days_left, "₽", "Оценка расходов к концу месяца",
                [f"За {elapsed} полных дней записано {rubles(recorded)} · {rubles(pace)} в день",
                 f"До конца месяца после сегодняшнего дня · {days_left} дн."],
            ))
    return result


def calculate_insights(receipts: list[Receipt], today: date) -> list[Insight]:
    return price_insights(receipts, today) + period_insights(receipts, today)
