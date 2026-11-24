import json
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from tempfile import TemporaryDirectory
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
        self.assertEqual(self.client.post("/receipts", files={"file": ("receipt.png", b"x", "image/png")}).status_code, 401)
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

    def test_receipt_and_derived_data_belong_to_authenticated_account(self):
        first, second = self.auth(), self.auth()
        owner = self.accept(first).json()
        self.assertTrue(self.accept(second).json()["consents_complete"])
        parsed = {"success": True, "store_name": "Тестовый магазин", "total": 12.5, "items": [
            {"name": "Кофе", "quantity": 1, "price": 12.5, "total": 12.5, "category": "Кофе"},
        ]}

        with (
            patch("routers.receipts.recognize_receipt", AsyncMock(return_value=parsed)),
            patch("routers.receipts.generate_mini_advice", AsyncMock(return_value="Совет")),
            patch("routers.advice.generate_advice", AsyncMock(side_effect=lambda costs: str(costs["total_receipts"]))),
        ):
            upload = self.client.post("/receipts", headers=first,
                files={"file": ("receipt.png", b"test", "image/png")}, data={"user_id": "999"})
            self.assertEqual(upload.status_code, 200)
            receipt = upload.json()["receipt"]
            self.assertGreater(receipt["items"][0]["id"], 0)
            for headers, count in ((first, 1), (second, 0)):
                params = {"user_id": owner["id"], "receipt_id": receipt["id"], "device_id": "legacy"}
                listing = self.client.get("/receipts", headers=headers, params=params)
                self.assertEqual(listing.headers["cache-control"], "no-store")
                self.assertEqual(len(listing.json()["receipts"]), count)
                for endpoint in ("/stats", "/report"):
                    data = self.client.get(endpoint, headers=headers, params=params).json()
                    self.assertEqual(data["receipts_count"], count)
                    self.assertEqual(data["total_spent"], 12.5 * count)
                advice = self.client.get("/advice", headers=headers, params=params).json()
                self.assertEqual(advice["advice"], str(count))
