# Add Text Formatting Features

Extend formatter.py with text centering and table formatting.

## Phase 1: Add center_text function

- [ ] `center_text(text, width)` centers text within the given width using spaces
- [ ] If text is longer than width, return text unchanged
- [ ] Total output length equals `width` (padded with spaces)
- [ ] Tests pass for center_text scenarios

## Phase 2: Add format_table function

- [ ] `format_table(headers, rows)` produces an ASCII table
- [ ] Header row separated from data by a `---` separator line
- [ ] Columns are padded so all lines have equal length
- [ ] Empty rows list produces header + separator only (2 lines)
- [ ] Tests pass for format_table scenarios

### Manual Verification

After Phase 2, please pause and let me verify:
- [ ] Table output is visually aligned when printed to terminal
- [ ] Separator line uses dashes, not other characters
- [ ] Column widths accommodate the longest value in each column
