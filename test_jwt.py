from app.core.security import decode_token

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsImV4cCI6MTc3MzE5NTk1MH0.uC3G_Qh8U6hPqtsVivnHhqx6kDXjmWK_oAkwbv5svoo'

try:
    payload = decode_token(token)
    print('Decoded:', payload)
except Exception as e:
    print('Error:', e)
