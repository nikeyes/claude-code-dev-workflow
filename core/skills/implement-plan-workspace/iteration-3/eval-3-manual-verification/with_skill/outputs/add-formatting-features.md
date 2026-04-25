# Add Text Formatting Features

Extend formatter.py with text centering and table formatting.

## Phase 1: Add center_text function

- [x] `center_text(text, width)` centers text within the given width using spaces
- [x] If text is longer than width, return text unchanged
- [x] Total output length equals `width` (padded with spaces)
- [x] Tests pass for center_text scenarios

## Phase 2: Add format_table function

- [x] `format_table(headers, rows)` produces an ASCII table
- [x] Header row separated from data by a `---` separator line
- [x] Columns are padded so all lines have equal length
- [x] Empty rows list produces header + separator only (2 lines)
- [x] Tests pass for format_table scenarios

### Manual Verification

After Phase 2, please pause and let me verify:
- [ ] Table output is visually aligned when printed to terminal
- [ ] Separator line uses dashes, not other characters
- [ ] Column widths accommodate the longest value in each column
