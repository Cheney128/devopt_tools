from app.core.security import get_password_hash, verify_password

h = get_password_hash('admin123')
print('Hash:', h[:50] + '...')
print('Verify:', verify_password('admin123', h))
