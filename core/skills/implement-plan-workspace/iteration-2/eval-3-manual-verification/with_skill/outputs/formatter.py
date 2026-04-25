def wrap_text(text, width=80):
    if width <= 0:
        raise ValueError("Width must be positive")
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    for word in words:
        if current_length + len(word) + len(current_line) > width:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)
        else:
            current_line.append(word)
            current_length += len(word)
    if current_line:
        lines.append(" ".join(current_line))
    return "\n".join(lines)


def center_text(text, width):
    if len(text) >= width:
        return text
    total_padding = width - len(text)
    left_padding = total_padding // 2
    right_padding = total_padding - left_padding
    return " " * left_padding + text + " " * right_padding


def format_table(headers, rows):
    all_rows = [headers] + list(rows)
    col_widths = [
        max(len(str(row[i])) for row in all_rows)
        for i in range(len(headers))
    ]
    separator = "-" * (sum(col_widths) + len(headers) - 1)
    header_line = " ".join(
        str(headers[i]).ljust(col_widths[i]) for i in range(len(headers))
    )
    lines = [header_line, separator]
    for row in rows:
        lines.append(
            " ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(headers)))
        )
    return "\n".join(lines)
