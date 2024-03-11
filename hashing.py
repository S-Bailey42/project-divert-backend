from bcrypt import hashpw, gensalt, checkpw




def password(pw: str) -> bytes:
    return hashpw(pw.encode("utf-8"), gensalt(14))

def check(pw: str, hashed_pw: bytes) -> bool:
    return checkpw(checkpw.encode("utf-8"), hashed_pw)
