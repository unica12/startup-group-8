import json
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from tempfile import TemporaryDirectory
from time import time
from threading import Thread
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient


def test_key(kid):
    key = ec.generate_private_key(ec.SECP256R1())
    jwk = jwt.algorithms.ECAlgorithm.to_jwk(key.public_key(), as_dict=True)
    return key, dict(jwk, kid=kid, alg="ES256", use="sig")


class JwksHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/auth/v1/.well-known/jwks.json":
            self.send_error(404)
            return
        body = json.dumps({"keys": self.server.keys}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class AuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = cls.enterClassContext(TemporaryDirectory())
        cls.key, jwk = test_key("first")
        cls.jwks = cls.enterClassContext(ThreadingHTTPServer(("127.0.0.1", 0), JwksHandler))
        cls.jwks.keys = [jwk]
        thread = Thread(target=cls.jwks.serve_forever, daemon=True)
        thread.start()
        cls.addClassCleanup(cls.jwks.shutdown)
        url = f"http://127.0.0.1:{cls.jwks.server_port}"
        cls.issuer = f"{url}/auth/v1"
        cls.enterClassContext(patch.dict(os.environ, {
            "DATABASE_URL": f"sqlite+aiosqlite:///{folder}/test.db", "SUPABASE_URL": url,
            "OPENAI_API_KEY": "test-only", "PYTHON_DOTENV_DISABLED": "1",
            "SUPABASE_SECRET_KEY": "sb_secret_test-only",
        }))
        from main import app
        from services.auth import REQUIRED_CONSENTS

        cls.required = REQUIRED_CONSENTS
        cls.client = cls.enterClassContext(TestClient(app, client=("127.0.0.1", 32100)))

    def auth(self, user=None, key=None, kid="first", **claims):
        payload = {
            "sub": str(user or uuid4()), "iss": self.issuer, "aud": "authenticated",
            "role": "authenticated", "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            "email": "student@example.test", "user_metadata": {"name": "Участник"},
        }
        token = jwt.encode(payload | claims, key or self.key, algorithm="ES256", headers={"kid": kid})
        return {"Authorization": f"Bearer {token}"}

    def accept(self, headers):
        return self.client.post("/auth/consents", headers=headers, json={"consents": self.required})

    def test_requires_valid_jwt(self):
        for endpoint in ("/auth/me", "/receipts", "/stats", "/report", "/advice"):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 401, endpoint)
            self.assertEqual(response.headers["www-authenticate"], "Bearer")
        self.assertEqual(self.client.post("/auth/register", json={}).status_code, 404)
        self.assertEqual(self.client.post("/receipts/recognize", files={"file": ("receipt.png", b"x", "image/png")}).status_code, 401)
        invalid = [
            self.auth(key=ec.generate_private_key(ec.SECP256R1())),
            self.auth(exp=datetime.now(timezone.utc) - timedelta(seconds=1)),
            self.auth(aud="another-app"), self.auth(iss="https://wrong.example.test/auth/v1"),
            self.auth(sub="invalid"), self.auth(role="anon"), self.auth(is_anonymous=True),
        ]
        for headers in invalid:
            self.assertEqual(self.client.get("/auth/me", headers=headers).status_code, 401)

    def test_rotation_accepts_new_kid(self):
        self.assertEqual(self.client.get("/auth/me", headers=self.auth()).status_code, 200)
        key, jwk = test_key("second")
        self.jwks.keys.append(jwk)
        response = self.client.get("/auth/me", headers=self.auth(key=key, kid="second"))
        self.assertEqual(response.status_code, 200)

    def test_profiles_and_consents_are_idempotent(self):
        from sqlalchemy import select
        from database.db import AsyncSessionFactory
        from database.models import Consent

        headers = self.auth()
        with ThreadPoolExecutor(max_workers=4) as threads:
            profiles = list(threads.map(lambda _: self.client.get("/auth/me", headers=headers).json(), range(4)))
        self.assertEqual(len({row["id"] for row in profiles}), 1)
        profile = profiles[0]
        self.assertFalse(profile["consents_complete"])
        for endpoint in ("/receipts", "/stats", "/report", "/advice"):
            self.assertEqual(self.client.get(endpoint, headers=headers).status_code, 403)
        incomplete = self.client.post("/auth/consents", headers=headers, json={"consents": {"terms": "prototype-1"}})
        self.assertEqual(incomplete.status_code, 422)
        self.assertTrue(self.accept(headers).json()["consents_complete"])
        self.assertTrue(self.accept(headers).json()["consents_complete"])

        async def read_consents():
            async with AsyncSessionFactory() as session:
                return (await session.scalars(select(Consent).where(Consent.user_id == profile["id"]))).all()

        rows = self.client.portal.call(read_consents)
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertIsNotNone(row.accepted_at)
            self.assertEqual(row.ip_address, "127.0.0.1")
            self.assertEqual(row.user_agent, "testclient")

    def test_receipt_review_ownership_idempotency_and_derived_data(self):
        from services.receipt_validation import from_ocr

        first, second = self.auth(), self.auth()
        owner = self.accept(first).json()
        self.assertTrue(self.accept(second).json()["consents_complete"])
        from utils.receipt_dates import reporting_day

        today = reporting_day()
        parsed = {"store_name": "Тестовый магазин", "date": today.isoformat(),
                  "total": "26", "items": [{
            "raw_name": "Кофе тест молотый 250г", "name": "Кофе Тест молотый 250 г", "brand": "Тест",
            "quantity": "1", "unit": "шт", "price": "13", "total": "13", "category": "Кофе",
            "package_size": "250", "package_unit": "г",
        }]}

        def recognize(payload):
            receipt, warnings = from_ocr(payload)
            with patch("routers.receipts.recognize_receipt", AsyncMock(return_value=(receipt, warnings, False))):
                return self.client.post("/receipts/recognize", headers=first,
                    files={"file": ("receipt.png", b"synthetic", "image/png")},
                    data={"user_id": "999"}).json()

        draft = recognize(parsed)
        self.assertTrue(draft["success"])
        self.assertTrue(draft["warnings"])
        path = f'/receipts/{draft["draft_id"]}/confirm'
        review = {"receipt": draft["receipt"]}
        self.assertEqual(self.client.post(path, headers=second, json=review).status_code, 404)
        self.assertEqual(self.client.get("/receipts", headers=first).json()["total_count"], 0)
        self.assertEqual(self.client.get("/stats", headers=first).json()["receipts_count"], 0)
        self.assertEqual(self.client.post(path, headers=first, json=review).status_code, 409)
        self.assertEqual(self.client.get("/receipts", headers=first).json()["total_count"], 0)

        # Исправляем магазин, количество и стоимость до сохранения.
        review["receipt"]["store_name"] = "Магазин А"
        review["receipt"]["items"][0].update(quantity="2", total="26")
        with ThreadPoolExecutor(max_workers=3) as threads:
            saves = list(threads.map(lambda _: self.client.post(path, headers=first, json=review), range(3)))
        self.assertEqual([response.status_code for response in saves], [200, 200, 200])
        records = [response.json()["receipt"] for response in saves]
        self.assertEqual(len({row["id"] for row in records}), 1)
        receipt = records[0]
        self.assertEqual(receipt["store_name"], "Магазин А")
        self.assertEqual(receipt["items"][0]["quantity"], 2)
        self.assertGreater(receipt["items"][0]["id"], 0)
        self.assertEqual(self.client.get("/receipts", headers=first).json()["total_count"], 1)

        cheaper = recognize(parsed | {"store_name": "Магазин Б", "total": "10",
                                     "items": [parsed["items"][0] | {"price": "10", "total": "10"}]})
        second_save = self.client.post(f'/receipts/{cheaper["draft_id"]}/confirm', headers=first,
                                       json={"receipt": cheaper["receipt"]})
        self.assertEqual(second_save.status_code, 200)
        self.assertIsNone(second_save.json()["mini_advice"])
        another = recognize(parsed | {"store_name": "Магазин А", "total": "13", "date": today.isoformat()})
        mini = self.client.post(f'/receipts/{another["draft_id"]}/confirm', headers=first,
                                json={"receipt": another["receipt"]})
        self.assertEqual(mini.json()["mini_advice"]["type"], "store_comparison")
        self.assertEqual(mini.json()["mini_advice"]["metric"]["value"], "3.00")

        for headers, count, total in ((first, 3, 49), (second, 0, 0)):
            params = {"user_id": owner["id"], "receipt_id": receipt["id"], "device_id": "legacy"}
            listing = self.client.get("/receipts", headers=headers, params=params)
            self.assertEqual(listing.headers["cache-control"], "no-store")
            self.assertEqual(len(listing.json()["receipts"]), count)
            for endpoint in ("/stats", "/report"):
                data = self.client.get(endpoint, headers=headers, params=params).json()
                self.assertEqual(data["receipts_count"], count)
                self.assertEqual(data["total_spent"], total)
            advice = self.client.get("/advice", headers=headers, params=params).json()
            if count:
                self.assertIn("store_comparison", [item["type"] for item in advice["insights"]])
            else:
                self.assertEqual(advice["insights"], [])
                self.assertTrue(advice["empty_message"])

    def test_confirmed_date_and_missing_unit_price_are_preserved(self):
        from schemas.receipt_input import ReceiptInput

        headers = self.auth()
        self.accept(headers)
        from utils.receipt_dates import reporting_day

        now = reporting_day()
        previous = now.replace(day=1) - timedelta(days=1)
        draft = ReceiptInput.model_validate({"date": now.isoformat(), "total": "30", "items": [
            {"raw_name": "Тестовая позиция", "name": "Тестовая позиция", "total": "30", "category": "Продукты"},
        ]})
        with patch("routers.receipts.recognize_receipt", AsyncMock(return_value=(draft, [], False))):
            preview = self.client.post("/receipts/recognize", headers=headers,
                files={"file": ("receipt.png", b"synthetic", "image/png")}).json()
        body = {"receipt": preview["receipt"] | {"date": previous.isoformat()}}
        url = f'/receipts/{preview["draft_id"]}/confirm'
        self.assertEqual(self.client.post(url, headers=headers, json=body).status_code, 409)
        saved = self.client.post(url, headers=headers, json=body | {"accept_warnings": True})
        self.assertEqual(saved.status_code, 200)
        receipt = saved.json()["receipt"]
        self.assertEqual(receipt["date"], previous.isoformat())
        self.assertIsNone(receipt["items"][0]["price"])
        self.assertIsNone(receipt["items"][0]["quantity"])
        self.assertEqual(self.client.get("/stats", headers=headers).json()["receipts_count"], 0)
        old_month = self.client.get("/stats", headers=headers, params={"month": previous.strftime("%Y-%m")}).json()
        self.assertEqual(old_month["total_spent"], 30)

    def test_receipt_periods_and_totals_follow_add_edit_and_delete(self):
        from decimal import Decimal
        from schemas.receipt_input import ReceiptInput
        from services.advisor import _cached, clear_advice_cache

        headers, other = self.auth(), self.auth()
        user_id = self.accept(headers).json()["id"]
        other_id = self.accept(other).json()["id"]
        self.addCleanup(clear_advice_cache, user_id)
        self.addCleanup(clear_advice_cache, other_id)

        def purchase(day, amount):
            return {"date": day, "store_name": "Тестовый магазин", "total": amount, "items": [{
                "name": "Молоко Утро 500 мл", "brand": "Утро", "quantity": "1", "unit": "шт",
                "price": amount, "total": amount, "category": "Молочные",
                "package_size": "500", "package_unit": "мл",
            }]}

        def save(payload, actor=headers):
            with patch("routers.receipts.recognize_receipt", AsyncMock(return_value=(ReceiptInput.model_validate(payload), [], False))):
                draft = self.client.post("/receipts/recognize", headers=actor,
                    files={"file": ("receipt.png", b"synthetic", "image/png")}).json()
            path = f'/receipts/{draft["draft_id"]}/confirm'
            response = self.client.post(path, headers=actor, json={"receipt": payload})
            self.assertEqual(response.status_code, 200)
            return response.json()["receipt"]["id"], path

        def totals(month, count, spent):
            data = self.client.get("/stats", headers=headers, params={"month": month}).json()
            self.assertEqual(data["receipts_count"], count)
            self.assertEqual(Decimal(str(data["total_spent"])), Decimal(spent))

        first, _ = save(purchase("2025-01-29", "11.01"))
        save(purchase("2025-01-31", "12.02"))
        save(purchase("2025-02-01", "20.03"))
        save(purchase("2025-02-02", "21.04"))
        save(purchase("2025-02-02", "179.00"), other)
        totals("all", 4, "64.10")
        self.assertEqual(self.client.get("/stats?month=all", headers=headers).json()["average_receipt"], 16.03)
        totals("2025-01", 2, "23.03")
        totals("2025-02", 2, "41.07")
        self.assertEqual(self.client.get("/auth/me/stats", headers=headers).json()["total_spent"], "64.10")
        history = self.client.get("/receipts?limit=2", headers=headers).json()
        self.assertEqual((history["total_count"], len(history["receipts"])), (4, 2))
        second_page = self.client.get("/receipts?limit=2&offset=2", headers=headers).json()
        self.assertTrue({r["id"] for r in history["receipts"]}.isdisjoint(r["id"] for r in second_page["receipts"]))

        _cached[user_id] = ("before-add", [])
        _cached[other_id] = ("other", [])
        extra = purchase("2025-02-07", "5.55")
        added, confirm_path = save(extra)
        self.assertNotIn(user_id, _cached)
        totals("all", 5, "69.65")
        totals("2025-02", 3, "46.62")

        _cached[user_id] = ("before-edit", [])
        edited = purchase("2025-02-03", "10.50")
        path = f"/receipts/{first}"
        self.assertEqual(self.client.patch(path, headers=other, json={"receipt": edited}).status_code, 404)
        self.assertEqual(self.client.delete(path, headers=other).status_code, 404)
        self.assertIn(user_id, _cached)
        response = self.client.patch(path, headers=headers, json={"receipt": edited})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["accounting_date"], edited["date"])
        self.assertNotIn(user_id, _cached)
        totals("2025-01", 1, "12.02")
        totals("2025-02", 4, "57.12")
        totals("all", 5, "69.14")

        _cached[user_id] = ("before-delete", [])
        self.assertEqual(self.client.delete(f"/receipts/{added}", headers=headers).status_code, 204)
        self.assertNotIn(user_id, _cached)
        self.assertEqual(_cached[other_id][0], "other")
        self.assertEqual(self.client.post(confirm_path, headers=headers, json={"receipt": extra}).status_code, 404)
        totals("all", 4, "63.59")
        totals("2025-02", 3, "51.57")
        profile = self.client.get("/auth/me/stats", headers=headers).json()
        self.assertEqual((profile["receipts_count"], profile["total_spent"], profile["items_count"]), (4, "63.59", 4))
        self.assertEqual(self.client.get("/receipts", headers=other).json()["total_count"], 1)
        self.assertEqual(self.client.get("/stats?month=all", headers=other).json()["total_spent"], 179)

    def test_accounting_dates_use_moscow_for_scan_date_fallback(self):
        from database.db import AsyncSessionFactory
        from database.models import Receipt, ReceiptDraft

        headers = self.auth()
        user_id = self.accept(headers).json()["id"]

        async def seed():
            async with AsyncSessionFactory() as session:
                draft = ReceiptDraft(id=uuid4(), user_id=user_id)
                session.add(draft)
                await session.flush()
                session.add_all([
                    Receipt(user_id=user_id, store_name="Старый чек", date=date(2025, 2, 10),
                            created_at=datetime(2025, 1, 31, 20, 59, 59), total=100),
                    Receipt(user_id=user_id, store_name="Без даты", draft_id=draft.id,
                            created_at=datetime(2025, 1, 31, 21), total=200),
                ])
                await session.commit()

        self.client.portal.call(seed)
        listing = self.client.get("/receipts", headers=headers).json()
        self.assertEqual([row["accounting_date"] for row in listing["receipts"]], ["2025-02-01", "2025-01-31"])
        self.assertEqual(self.client.get("/stats?month=2025-01", headers=headers).json()["total_spent"], 100)
        with patch("routers.stats.reporting_day", return_value=date(2025, 2, 1)):
            self.assertEqual(self.client.get("/stats", headers=headers).json()["total_spent"], 200)
        with patch("database.queries.reporting_day", return_value=date(2025, 2, 1)):
            self.assertEqual(self.client.get("/report", headers=headers).json()["receipts_count"], 2)

    def seed_profile_receipts(self, owner, name, *, count=1):
        from database.db import AsyncSessionFactory
        from database.models import Item, Receipt, ReceiptDraft

        draft_id = uuid4()

        async def seed():
            async with AsyncSessionFactory() as session:
                session.add(ReceiptDraft(id=draft_id, user_id=owner))
                await session.flush()
                for index in range(count):
                    total = .1 if index % 2 == 0 else .2
                    session.add(Receipt(user_id=owner, draft_id=draft_id if index == 0 else None,
                                        date=date(2021, 1, 1), store_name=name, total=total, items=[
                        Item(name=f"{name} SKU", quantity=2, total=total / 2, category="Кофе"),
                        Item(name=f"{name} скидка", total=total / 2, category="  "),
                    ]))
                await session.commit()

        self.client.portal.call(seed)
        return draft_id

    def test_profile_name_is_normalized_and_stays_authoritative_after_sign_in(self):
        user_id = uuid4()
        headers = self.auth(user_id, user_metadata={"name": "При регистрации"})
        profile = self.accept(headers).json()
        self.assertEqual(profile["name"], "При регистрации")
        for invalid in ("    ", "x" * 51, "\u200b"):
            self.assertEqual(self.client.patch("/auth/me", headers=headers, json={"name": invalid}).status_code, 422)
        changed = self.client.patch("/auth/me", headers=headers, json={"name": "  Иван   Петров "})
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.json()["name"], "Иван Петров")
        stale = self.auth(user_id, user_metadata={"name": "Устаревшее имя"})
        self.assertEqual(self.client.get("/auth/me", headers=stale).json()["name"], "Иван Петров")
        self.assertEqual(self.client.get("/auth/me", headers=stale).json()["created_at"], profile["created_at"])

    def test_all_time_stats_and_full_export_are_scoped_to_current_user(self):
        first, other = self.auth(), self.auth(email="other@example.test")
        owner = self.accept(first).json()
        stranger = self.accept(other).json()
        for path in ("/auth/me/stats", "/auth/me/export"):
            self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.client.get("/auth/me/stats", headers=first).json(), {
            "receipts_count": 0, "total_spent": "0.00", "items_count": 0, "top_category": None,
        })
        self.seed_profile_receipts(owner["id"], "Магазин пользователя", count=103)
        self.seed_profile_receipts(stranger["id"], "Чужой магазин")
        result = self.client.get("/auth/me/stats", headers=first, params={"user_id": stranger["id"]})
        self.assertEqual(result.json(), {
            "receipts_count": 103, "total_spent": "15.40", "items_count": 206, "top_category": "Кофе",
        })

        response = self.client.get("/auth/me/export", headers=first, params={"user_id": stranger["id"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertIn('attachment; filename="checkmudrets-export-', response.headers["content-disposition"])
        exported = response.json()
        self.assertEqual(exported["profile"]["id"], owner["id"])
        self.assertEqual(exported["profile"]["created_at"], owner["created_at"])
        self.assertTrue(exported["exported_at"])
        self.assertEqual(len(exported["receipts"]), 103)
        self.assertEqual(len(exported["receipts"][0]["items"]), 2)
        self.assertEqual(len(exported["consents"]), 3)
        self.assertNotIn("Чужой магазин", response.text)
        self.assertNotIn("other@example.test", response.text)
        self.assertFalse({"access_token", "refresh_token", "password", "DATABASE_URL"} & exported["profile"].keys())

    def test_deletion_reauth_idempotency_and_related_rows(self):
        from sqlalchemy import func, select
        from database.accounts import account_fingerprint
        from database.db import AsyncSessionFactory
        from database.models import AccountDeletion, Consent, Item, Receipt, ReceiptDraft, User
        from services.advisor import _cached

        identity = uuid4()
        fresh = self.auth(identity, amr=[{"method": "password", "timestamp": int(time())}])
        stale = self.auth(identity, amr=[{"method": "password", "timestamp": int(time()) - 600}])
        owner = self.accept(fresh).json()["id"]
        stranger = self.auth()
        other_id = self.accept(stranger).json()["id"]
        self.seed_profile_receipts(owner, "Удаляемый тест")
        self.seed_profile_receipts(other_id, "Остающийся тест")
        _cached[owner] = ("test", [])

        self.assertEqual(self.client.delete("/auth/me", headers=stale).status_code, 403)
        self.assertEqual(self.client.get("/auth/me/stats", headers=fresh).json()["receipts_count"], 1)
        with patch("services.account_deletion.delete_auth_user", AsyncMock()) as admin:
            with ThreadPoolExecutor(max_workers=2) as threads:
                outcomes = list(threads.map(lambda _: self.client.delete("/auth/me", headers=fresh).status_code, range(2)))
            self.assertEqual(outcomes, [204, 204])
            self.assertEqual(self.client.delete("/auth/me", headers=fresh).status_code, 204)
            admin.assert_awaited_once_with(identity)

        for path in ("/auth/me", "/auth/me/stats", "/auth/me/export", "/receipts", "/advice"):
            self.assertEqual(self.client.get(path, headers=fresh).status_code, 401)
        self.assertNotIn(owner, _cached)
        self.assertEqual(self.client.get("/auth/me/stats", headers=stranger).json()["receipts_count"], 1)

        async def verify_removal():
            async with AsyncSessionFactory() as session:
                self.assertIsNone(await session.get(User, owner))
                for model in (Consent, Receipt, ReceiptDraft):
                    self.assertEqual(await session.scalar(select(func.count()).select_from(model).where(model.user_id == owner)), 0)
                self.assertEqual(await session.scalar(select(func.count(Item.id)).where(Item.name.like("Удаляемый тест%"))), 0)
                self.assertIsNone((await session.get(AccountDeletion, account_fingerprint(identity))).auth_user_id)

        self.client.portal.call(verify_removal)

    def test_deletion_can_resume_after_admin_failure(self):
        from services.account_deletion import AuthDeletionUnavailable

        identity = uuid4()
        fresh = self.auth(identity, amr=[{"method": "password", "timestamp": int(time())}])
        owner = self.accept(fresh).json()["id"]
        self.seed_profile_receipts(owner, "Временный сбой")
        admin = AsyncMock(side_effect=[AuthDeletionUnavailable(), None])
        with patch("services.account_deletion.delete_auth_user", admin):
            partial = self.client.delete("/auth/me", headers=fresh)
            self.assertEqual(partial.status_code, 503)
            self.assertEqual(partial.json()["detail"]["code"], "account_deletion_pending")
            self.assertEqual(self.client.get("/auth/me", headers=fresh).status_code, 409)
            self.assertEqual(self.client.get("/receipts", headers=fresh).status_code, 409)
            self.assertEqual(self.client.delete("/auth/me", headers=self.auth(identity)).status_code, 204)
            self.assertEqual(admin.await_count, 2)
        self.assertEqual(self.client.get("/auth/me", headers=fresh).status_code, 401)
