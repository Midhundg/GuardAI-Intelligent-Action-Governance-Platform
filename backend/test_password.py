from app.auth.passwords import hash_password, verify_password

password = "Admin@123"

hashed = hash_password(password)

print("Hashed Password:")
print(hashed)

print("\nVerification:")
print(verify_password(password, hashed))