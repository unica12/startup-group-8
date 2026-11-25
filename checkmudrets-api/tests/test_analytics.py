import asyncio
import unittest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from database.models import Item, Receipt
from services.analytics import calculate_insights, price_insights

TODAY = date(2026, 11, 20)


def line(name="Молоко Утро 3,2% 500 мл", brand="Утро", size=500, unit="мл", price=80, category="Молочные"):
    return Item(name=name, brand=brand, package_size=size, package_unit=unit, quantity=1,
                price=price, total=price, unit="шт", category=category)


def receipt(id_, day, store, item, comparable=True):
    return Receipt(id=id_, date=day, store_name=store, total=item.total, items=[item], price_comparable=comparable)


class AnalyticsTests(unittest.TestCase):
    def test_store_prices_trend_and_savings_for_same_product(self):
        rows = [
            receipt(1, TODAY - timedelta(days=15), "Магазин 1", line(price=70)),
            receipt(2, TODAY - timedelta(days=5), "Магазин 2", line(price=60)),
            receipt(3, TODAY - timedelta(days=3), "Магазин 1", line(price=90)),
            receipt(4, TODAY - timedelta(days=1), "Магазин 3", line(brand="Другое", price=5)),
        ]
        facts = {item.type: item for item in price_insights(rows, TODAY)}
        self.assertEqual(facts["store_comparison"].metric.value, Decimal("30.00"))
        self.assertEqual(facts["price_change"].metric.value, Decimal("20.00"))
        self.assertEqual(facts["savings"].estimated_savings, Decimal("40.00"))
        self.assertEqual(price_insights(rows, TODAY, focus_receipt_id=3)[0].type, "store_comparison")
        self.assertEqual(price_insights(rows, TODAY, focus_receipt_id=4), [])

    def test_compares_litres_and_kilos_without_comparing_package_prices(self):
        milk = [
            receipt(1, TODAY, "Магазин 1", line(price=80)),
            receipt(2, TODAY, "Магазин 2", line(name="Молоко Утро 3,2% 1 л", size=1, unit="л", price=100)),
        ]
        facts = price_insights(milk, TODAY)
        self.assertEqual([(item.type, item.metric.value, item.metric.unit) for item in facts],
                         [("unit_price", Decimal("60.00"), "₽/л")])

        coffee = [
            receipt(3, TODAY, "Магазин 1", line("Кофе Утро молотый 250г", size=250, unit="г", price=375, category="Кофе")),
            receipt(4, TODAY, "Магазин 2", line("Кофе Утро молотый 1 кг", size=1, unit="кг", price=1000, category="Кофе")),
        ]
        self.assertEqual(price_insights(coffee, TODAY)[0].metric.value, Decimal("500.00"))
        self.assertEqual(price_insights(coffee, TODAY)[0].metric.unit, "₽/кг")

    def test_unknown_identity_disputed_price_and_unit_without_quantity_are_ignored(self):
        rows = [
            receipt(1, TODAY, "Первый", line(price=100)),
            receipt(2, TODAY, "Второй", line(price=50), comparable=False),
            receipt(3, TODAY, "Третий", line(brand=None, price=20)),
        ]
        self.assertEqual(price_insights(rows, TODAY), [])
        rows[1].price_comparable = True
        rows[1].discount = 10
        rows[2].items[0].unit = None
        self.assertEqual(price_insights(rows, TODAY), [])

    def test_equal_periods_and_forecast_require_coverage(self):
        dates = [date(2026, 10, day) for day in (2, 8, 12, 18, 27, 29)]
        dates += [date(2026, 11, day) for day in (1, 5, 8, 12, 17)]
        rows = [receipt(index, day, "Магазин", line(price=40 if day < date(2026, 10, 21) else 100), comparable=False)
                for index, day in enumerate(dates)]
        # Легаси-чекам без детализации можно доверять для общей истории, но не для сравнения цен.
        for row in rows:
            row.price_comparable = None
        items = {item.type: item for item in calculate_insights(rows, TODAY)}
        self.assertEqual(items["category_change"].metric.value, Decimal("540.00"))
        self.assertEqual(items["growth_driver"].metric.value, Decimal("540.00"))
        self.assertEqual(items["shopping_frequency"].metric.value, Decimal("7.00"))
        self.assertEqual(items["forecast"].metric.value, Decimal("763.16"))
        self.assertEqual(calculate_insights(rows[-1:], TODAY), [])
        self.assertNotIn("category_change", {item.type for item in calculate_insights(rows[-5:], TODAY)})

    def test_frequency_counts_shop_days_and_unique_receipts_per_product(self):
        rows = [receipt(i, TODAY - timedelta(days=day), "Магазин 1", line()) for i, day in enumerate([1, 1, 2, 3])]
        rows[0].items.append(line())
        habits = next(item for item in calculate_insights(rows, TODAY) if item.type == "shopping_frequency")
        self.assertEqual(habits.metric.value, Decimal("3"))
        self.assertIn("«Молоко Утро 3,2% 500 мл» есть в 4 чеках", habits.evidence[-1])


class AdvisorTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalidated_inflight_result_cannot_fill_the_cache(self):
        from services.advisor import _cached, advice_snapshot, clear_advice_cache, generate_advice

        rows = [receipt(1, TODAY, "Магазин 1", line(price=80)), receipt(2, TODAY, "Магазин 2", line(price=100))]
        insights = calculate_insights(rows, TODAY)
        started, finish = asyncio.Event(), asyncio.Event()
        snapshot = advice_snapshot(12347)

        async def choose_old(values):
            started.set()
            await finish.wait()
            return values

        with patch("services.advisor._choose", side_effect=choose_old):
            pending = asyncio.create_task(generate_advice(12347, insights, snapshot))
            await started.wait()
            clear_advice_cache(12347)
            finish.set()
            await pending
        self.assertNotIn(12347, _cached)
        with patch("services.advisor._choose", AsyncMock()) as choose:
            self.assertEqual(await generate_advice(12347, insights, snapshot), insights)
            choose.assert_not_called()

    async def test_choices_are_cached_per_account_and_changed_facts_are_refreshed(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-only", "PYTHON_DOTENV_DISABLED": "1"}):
            from services.advisor import generate_advice
        rows = [
            receipt(1, TODAY, "Магазин 1", line(price=80)),
            receipt(2, TODAY, "Магазин 2", line(price=100)),
        ]
        insights = calculate_insights(rows, TODAY)
        choose = AsyncMock(side_effect=lambda values: values)
        with patch("services.advisor._choose", choose):
            await asyncio.gather(generate_advice(12345, insights), generate_advice(12345, insights))
            self.assertEqual(choose.await_count, 1)
            await generate_advice(12346, insights)
            self.assertEqual(choose.await_count, 2)
            rows[1].items[0].total = 140
            await generate_advice(12345, calculate_insights(rows, TODAY))
            self.assertEqual(choose.await_count, 3)
