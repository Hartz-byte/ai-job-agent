import hashlib

def hash_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def job_key(title: str, company: str, location: str) -> str:
    base = f"{title.strip().lower()}::{company.strip().lower()}::{location.strip().lower()}"
    return hash_text(base)
