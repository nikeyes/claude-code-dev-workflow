import re


def shorten(text, max_len, ellipsis="..."):
    """Deviation: named 'shorten' instead of 'truncate', params renamed."""
    if max_len < len(ellipsis):
        raise ValueError("max_len must be >= length of ellipsis")
    if len(text) <= max_len:
        return text
    return text[:max_len - len(ellipsis)] + ellipsis


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text.strip('-')


def count_words(text):
    """Deviation: named 'count_words' instead of 'word_count'."""
    return len(text.split())


def extract_emails(text):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(pattern, text)


def mask_sensitive(text, pattern, replacement="***"):
    return text.replace(pattern, replacement)


def reverse_words(text):
    """Deviation: unplanned function not in the plan."""
    return ' '.join(text.split()[::-1])
