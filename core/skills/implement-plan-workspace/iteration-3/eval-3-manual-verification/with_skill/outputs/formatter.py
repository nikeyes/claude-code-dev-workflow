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
    return text.center(width)


def format_table(headers, rows):
    all_rows = [headers] + rows
    col_widths = [
        max(len(str(row[i])) for row in all_rows)
        for i in range(len(headers))
    ]
    def format_row(row):
        return "| " + " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) + " |"
    total_width = 2 + sum(col_widths) + len(" | ") * (len(col_widths) - 1) + 2
    separator = "|" + "-" * (total_width - 2) + "|"
    lines = [format_row(headers), separator]
    for row in rows:
        lines.append(format_row(row))
    return "\n".join(lines)
