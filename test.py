import jwt
from datetime import datetime, timedelta

SECRET = 'a-string-secret-at-least-256-bits-long'

def create_token(user_id):
    payload = {
        'sub': str(user_id),
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET, algorithm='HS256')
    return token

def decode_token(token):
    decoded = jwt.decode(token, SECRET, algorithms=['HS256'], options={"verify_exp": False})
    return decoded

if __name__ == "__main__":
    user_id = 1
    token = create_token(user_id)
    print("Сгенерированный токен:")
    print(token)

    decoded = decode_token(token)
    print("\nДекодированный payload:")
    print(decoded)

    print("\nТип поля sub:", type(decoded['sub']))
