from backend.auth.jwt import (
    create_access_token,
    decode_access_token,
)

payload = {
    "user_id": 1,
    "seller_id": 100,
}

token = create_access_token(payload)

print("TOKEN:")
print(token)

decoded = decode_access_token(token)

print("\nDECODED:")
print(decoded)