from app.auth.jwt_handler import create_access_token, verify_access_token

token = create_access_token(
    {
        "sub": "admin",
        "role": "ADMIN",
    }
)

print("Generated Token:\n")
print(token)

print("\nDecoded Payload:\n")
print(verify_access_token(token))