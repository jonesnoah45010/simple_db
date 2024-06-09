import bcrypt
import secrets
import string

def generate_password(length=12):
	characters = string.ascii_letters + string.digits + string.punctuation
	password = ''.join(secrets.choice(characters) for _ in range(length))
	return password

def hash_password(password):
	salt = bcrypt.gensalt()
	hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
	return hashed

def check_password(hashed_password, user_password):
	if isinstance(hashed_password, str):
		hashed_password = hashed_password.encode('utf-8')
	return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password)