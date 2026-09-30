import hashlib

password = "my-secret"
password_hash = hashlib.sha256(password.encode()).hexdigest()

candidate = "my-secret"
candidate_hash = hashlib.sha256(candidate.encode()).hexdigest()

print(candidate_hash == password_hash)