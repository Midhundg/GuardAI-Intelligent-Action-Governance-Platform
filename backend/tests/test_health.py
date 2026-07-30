import unittest
from app.routes.health import health_check, readiness_check, liveness_check
from app.database import SessionLocal


class TestHealth(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_health_check(self):
        res = health_check(db=self.db)
        self.assertIn(res["status"], ("healthy", "degraded"))
        self.assertIn("dependencies", res)

    def test_readiness_check(self):
        res = readiness_check(db=self.db)
        self.assertEqual(res["status"], "ready")

    def test_liveness_check(self):
        res = liveness_check()
        self.assertTrue(res["live"])


if __name__ == "__main__":
    unittest.main()
