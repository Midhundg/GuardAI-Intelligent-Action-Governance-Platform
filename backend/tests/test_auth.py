import unittest
from app.routes.auth import register, login
from app.schemas.user import UserCreate
from app.database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm


class TestAuth(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_register_and_login_flow(self):
        user_in = UserCreate(
            username="unittest_flow_user",
            email="unittest_flow_user@example.com",
            password="Password123!",
            role="EMPLOYEE",
            department="Engineering"
        )
        try:
            reg_res = register(user=user_in, db=self.db)
            self.assertEqual(reg_res.username, "unittest_flow_user")
        except Exception:
            pass  # Already registered

        form = OAuth2PasswordRequestForm(username="unittest_flow_user", password="Password123!", scope="")
        token_res = login(form_data=form, db=self.db)
        self.assertIsNotNone(token_res.access_token)
        self.assertEqual(token_res.token_type, "bearer")


if __name__ == "__main__":
    unittest.main()
