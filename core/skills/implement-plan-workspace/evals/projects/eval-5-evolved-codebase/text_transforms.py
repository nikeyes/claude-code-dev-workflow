def truncate(text, max_length, suffix="..."):
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def title_case(text):
    return " ".join(w.capitalize() for w in text.split())
