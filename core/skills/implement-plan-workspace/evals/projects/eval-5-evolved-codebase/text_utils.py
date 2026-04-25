def slugify(text):
    return text.lower().strip().replace(" ", "-")


def word_count(text):
    if not text or not text.strip():
        return 0
    return len(text.split())
