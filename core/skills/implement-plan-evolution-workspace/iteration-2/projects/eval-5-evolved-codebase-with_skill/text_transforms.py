def truncate(text, max_length, suffix="..."):
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def title_case(text):
    return " ".join(w.capitalize() for w in text.split())


def pad_right(text, width):
    if len(text) >= width:
        return text
    return text.ljust(width)


def pad_center(text, width):
    if len(text) >= width:
        return text
    return text.center(width)


def repeat_text(text, count):
    return text * count
