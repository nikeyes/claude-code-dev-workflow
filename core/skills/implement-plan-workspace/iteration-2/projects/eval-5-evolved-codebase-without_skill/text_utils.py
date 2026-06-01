import re


def slugify(text):
    return text.lower().strip().replace(" ", "-")


def word_count(text):
    if not text or not text.strip():
        return 0
    return len(text.split())


def contains_any(text, keywords):
    return any(keyword in text for keyword in keywords)


def extract_emails(text):
    return re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
