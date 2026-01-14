import bcrypt
print(bcrypt.hashpw("nexa123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))
