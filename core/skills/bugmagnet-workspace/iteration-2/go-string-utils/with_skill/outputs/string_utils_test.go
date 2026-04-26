package stringutils

import (
	"strings"
	"testing"
)

// ─── Truncate ────────────────────────────────────────────────────────────────

func TestTruncate(t *testing.T) {
	result := Truncate("Hello World", 5)
	if result != "Hello..." {
		t.Errorf("got %q, want %q", result, "Hello...")
	}
}

func TestTruncate_returnsOriginalWhenShorterThanMaxLen(t *testing.T) {
	result := Truncate("Hi", 10)
	if result != "Hi" {
		t.Errorf("got %q, want %q", result, "Hi")
	}
}

func TestTruncate_returnsOriginalWhenExactlyMaxLen(t *testing.T) {
	result := Truncate("Hello", 5)
	if result != "Hello" {
		t.Errorf("got %q, want %q", result, "Hello")
	}
}

func TestTruncate_returnsEmptyStringWhenInputIsEmpty(t *testing.T) {
	result := Truncate("", 5)
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestTruncate_returnsEllipsisWhenMaxLenIsZero(t *testing.T) {
	result := Truncate("Hello", 0)
	if result != "..." {
		t.Errorf("got %q, want %q", result, "...")
	}
}

func TestTruncate_returnsOriginalWhenSingleCharAndMaxLenOne(t *testing.T) {
	result := Truncate("A", 1)
	if result != "A" {
		t.Errorf("got %q, want %q", result, "A")
	}
}

func TestTruncate_truncatesAtMaxLenMinusOne(t *testing.T) {
	// Off-by-one: string of length 6, maxLen=5 → truncates
	result := Truncate("Helloo", 5)
	if result != "Hello..." {
		t.Errorf("got %q, want %q", result, "Hello...")
	}
}

func TestTruncate_handlesVeryLongString(t *testing.T) {
	longStr := strings.Repeat("a", 10000)
	result := Truncate(longStr, 100)
	if len(result) != 103 { // 100 chars + "..."
		t.Errorf("got length %d, want 103", len(result))
	}
	if !strings.HasSuffix(result, "...") {
		t.Errorf("expected result to end with '...', got %q", result[97:])
	}
}

// BUG TEST: Truncate uses len(s) which counts bytes, not Unicode runes.
// For a multibyte character like "é" (2 bytes), Truncate("café", 4) should
// return "café" (4 runes fit within maxLen=4) but instead truncates it
// because len("café") = 6 bytes > maxLen=4.
func TestTruncate_returnsOriginalWhenRuneCountEqualsMaxLenButByteCountExceeds_BUG(t *testing.T) {
	t.Skip("BUG: Truncate uses len(s) (byte count) instead of utf8.RuneCountInString(s) (rune count)")
	/*
	 * BUG: Truncate uses byte-length comparison (len(s)) instead of rune-length
	 * comparison (utf8.RuneCountInString(s)). For multibyte Unicode characters
	 * this produces incorrect results:
	 * 1. Wrong truncation: "café" has 4 runes but 6 bytes, so Truncate("café", 4)
	 *    truncates when it should not (6 > 4, byte-wise).
	 * 2. Mid-rune split: s[:4] on "café" cuts through the 2-byte 'é', yielding
	 *    "caf\xc3..." — invalid UTF-8.
	 *
	 * CODE LOCATION: string_utils.go:10-13
	 *
	 * CURRENT CODE:
	 *   if len(s) <= maxLen {
	 *       return s
	 *   }
	 *   return s[:maxLen] + "..."
	 *
	 * PROPOSED FIX:
	 *   runes := []rune(s)
	 *   if len(runes) <= maxLen {
	 *       return s
	 *   }
	 *   return string(runes[:maxLen]) + "..."
	 *
	 * EXPECTED: Truncate("café", 4) == "café"  (4 runes == maxLen, no truncation)
	 * ACTUAL:   Truncate("café", 4) == "caf\xc3..."  (invalid UTF-8, truncated)
	 *
	 * MINIMAL REPRODUCTION: Truncate("café", 4)
	 */
	result := Truncate("café", 4)
	if result != "café" {
		t.Errorf("got %q, want %q", result, "café")
	}
}

// ─── SlugifyText ─────────────────────────────────────────────────────────────

func TestSlugifyText(t *testing.T) {
	result := SlugifyText("Hello World")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_returnsEmptyStringWhenInputIsEmpty(t *testing.T) {
	result := SlugifyText("")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestSlugifyText_convertsAllUppercaseToLowercase(t *testing.T) {
	result := SlugifyText("HELLO WORLD")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_collapsesMulitpleSpacesToSingleHyphen(t *testing.T) {
	result := SlugifyText("Hello  World")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_preservesHyphenBetweenWords(t *testing.T) {
	result := SlugifyText("well-known")
	if result != "well-known" {
		t.Errorf("got %q, want %q", result, "well-known")
	}
}

func TestSlugifyText_removesSpecialCharacters(t *testing.T) {
	result := SlugifyText("Hello, World!")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_trimsLeadingAndTrailingHyphens(t *testing.T) {
	result := SlugifyText("  Hello World  ")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_preservesNumbers(t *testing.T) {
	result := SlugifyText("Hello 123 World")
	if result != "hello-123-world" {
		t.Errorf("got %q, want %q", result, "hello-123-world")
	}
}

func TestSlugifyText_handlesSingleWord(t *testing.T) {
	result := SlugifyText("hello")
	if result != "hello" {
		t.Errorf("got %q, want %q", result, "hello")
	}
}

func TestSlugifyText_removesApostrophesWithoutInsertingHyphen(t *testing.T) {
	// "it's" → should be "its" (apostrophe removed, no hyphen inserted)
	result := SlugifyText("it's")
	if result != "its" {
		t.Errorf("got %q, want %q", result, "its")
	}
}

func TestSlugifyText_handlesOnlySpecialChars(t *testing.T) {
	result := SlugifyText("!@#$%")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestSlugifyText_handlesUnicodeLetters(t *testing.T) {
	// unicode.IsLetter passes for accented chars, so they should be kept
	result := SlugifyText("Héllo")
	if result != "héllo" {
		t.Errorf("got %q, want %q", result, "héllo")
	}
}

func TestSlugifyText_handlesConsecutiveHyphens(t *testing.T) {
	result := SlugifyText("a--b")
	if result != "a-b" {
		t.Errorf("got %q, want %q", result, "a-b")
	}
}

// ─── CountWords ──────────────────────────────────────────────────────────────

func TestCountWords(t *testing.T) {
	result := CountWords("one two three")
	if result != 3 {
		t.Errorf("got %d, want %d", result, 3)
	}
}

func TestCountWords_returnsZeroWhenInputIsEmpty(t *testing.T) {
	result := CountWords("")
	if result != 0 {
		t.Errorf("got %d, want %d", result, 0)
	}
}

func TestCountWords_returnsZeroWhenInputIsWhitespaceOnly(t *testing.T) {
	result := CountWords("   \t\n  ")
	if result != 0 {
		t.Errorf("got %d, want %d", result, 0)
	}
}

func TestCountWords_returnsOneWhenInputIsSingleWord(t *testing.T) {
	result := CountWords("hello")
	if result != 1 {
		t.Errorf("got %d, want %d", result, 1)
	}
}

func TestCountWords_countsCorrectlyWithExtraWhitespaceBetweenWords(t *testing.T) {
	result := CountWords("one   two   three")
	if result != 3 {
		t.Errorf("got %d, want %d", result, 3)
	}
}

func TestCountWords_countsCorrectlyWithLeadingAndTrailingWhitespace(t *testing.T) {
	result := CountWords("  one two  ")
	if result != 2 {
		t.Errorf("got %d, want %d", result, 2)
	}
}

func TestCountWords_countsTabsAndNewlinesAsWordSeparators(t *testing.T) {
	result := CountWords("one\ttwo\nthree")
	if result != 3 {
		t.Errorf("got %d, want %d", result, 3)
	}
}

// ─── ExtractInitials ─────────────────────────────────────────────────────────

func TestExtractInitials_returnsUppercaseInitialsForTwoWordName(t *testing.T) {
	result := ExtractInitials("John Doe")
	if result != "JD" {
		t.Errorf("got %q, want %q", result, "JD")
	}
}

func TestExtractInitials_returnsUppercaseInitialsForThreeWordName(t *testing.T) {
	result := ExtractInitials("John Paul Jones")
	if result != "JPJ" {
		t.Errorf("got %q, want %q", result, "JPJ")
	}
}

func TestExtractInitials_returnsSingleUppercaseInitialForSingleWordName(t *testing.T) {
	result := ExtractInitials("Alice")
	if result != "A" {
		t.Errorf("got %q, want %q", result, "A")
	}
}

func TestExtractInitials_uppercasesAlreadyLowercaseName(t *testing.T) {
	result := ExtractInitials("john doe")
	if result != "JD" {
		t.Errorf("got %q, want %q", result, "JD")
	}
}

func TestExtractInitials_handlesExtraWhitespaceBetweenWords(t *testing.T) {
	result := ExtractInitials("John  Doe")
	if result != "JD" {
		t.Errorf("got %q, want %q", result, "JD")
	}
}

// BUG TEST: ExtractInitials panics on empty string input.
// strings.Fields("") returns an empty slice; the loop body never executes,
// but the real issue is that the function doesn't guard against empty input.
// Actually this won't panic — it returns "" because initials slice stays nil.
// BUT: if name is whitespace-only it also returns "". Let's verify.
func TestExtractInitials_returnsEmptyStringWhenInputIsEmpty(t *testing.T) {
	result := ExtractInitials("")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestExtractInitials_returnsEmptyStringWhenInputIsWhitespaceOnly(t *testing.T) {
	result := ExtractInitials("   ")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

// BUG TEST: ExtractInitials uses p[0] (byte index) not []rune(p)[0] (rune).
// For names starting with a multibyte Unicode character, p[0] returns the
// first byte of the UTF-8 encoding, not the actual character codepoint.
// This produces garbage output for non-ASCII names.
func TestExtractInitials_returnsCorrectInitialForNameWithAccentedFirstLetter_BUG(t *testing.T) {
	t.Skip("BUG: ExtractInitials uses p[0] (byte) instead of rune decoding; multibyte first chars produce garbage output")
	/*
	 * BUG: ExtractInitials uses p[0] to get the first character of each name part.
	 * In Go, indexing a string returns a byte, not a rune. For any name part
	 * starting with a multibyte UTF-8 codepoint (e.g. 'Å' = 0xC3 0x85),
	 * rune(p[0]) produces rune(0xC3) = 'Ã', not 'Å' (U+00C5).
	 *
	 * CODE LOCATION: string_utils.go:44
	 *
	 * CURRENT CODE:
	 *   initials = append(initials, rune(p[0]))
	 *
	 * PROPOSED FIX:
	 *   r, _ := utf8.DecodeRuneInString(p)
	 *   initials = append(initials, r)
	 *
	 * EXPECTED: ExtractInitials("Ångström Doe") == "ÅD"
	 * ACTUAL:   ExtractInitials("Ångström Doe") returns garbled bytes (e.g. "ÃD")
	 *
	 * MINIMAL REPRODUCTION: ExtractInitials("Ångström Doe")
	 */
	result := ExtractInitials("Ångström Doe")
	if result != "ÅD" {
		t.Errorf("got %q, want %q", result, "ÅD")
	}
}

// ─── WrapText ────────────────────────────────────────────────────────────────

func TestWrapText_wrapsTextAtSpecifiedWidth(t *testing.T) {
	result := WrapText("one two three four", 10)
	if result != "one two\nthree four" {
		t.Errorf("got %q, want %q", result, "one two\nthree four")
	}
}

func TestWrapText_returnsEmptyStringWhenInputIsEmpty(t *testing.T) {
	result := WrapText("", 10)
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestWrapText_returnsInputUnchangedWhenInputFitsInWidth(t *testing.T) {
	result := WrapText("Hello World", 20)
	if result != "Hello World" {
		t.Errorf("got %q, want %q", result, "Hello World")
	}
}

func TestWrapText_returnsSingleWordWhenInputIsSingleWord(t *testing.T) {
	result := WrapText("hello", 10)
	if result != "hello" {
		t.Errorf("got %q, want %q", result, "hello")
	}
}

func TestWrapText_wrapsAtExactWidthBoundary(t *testing.T) {
	// "Hello" is 5 chars, " World" is 6 chars → "Hello World" is 11 chars.
	// With width=11 it should all fit on one line.
	result := WrapText("Hello World", 11)
	if result != "Hello World" {
		t.Errorf("got %q, want %q", result, "Hello World")
	}
}

func TestWrapText_wrapsWhenLineExceedsWidthByOne(t *testing.T) {
	// With width=10, "Hello World" (11 chars) must wrap
	result := WrapText("Hello World", 10)
	if result != "Hello\nWorld" {
		t.Errorf("got %q, want %q", result, "Hello\nWorld")
	}
}

func TestWrapText_returnsInputUnchangedWhenWidthIsWhitespaceOnly(t *testing.T) {
	result := WrapText("   ", 10)
	// strings.Fields strips whitespace, so empty words → returns ""
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestWrapText_placesSingleWordOnOwnLineWhenWordIsLongerThanWidth(t *testing.T) {
	// A word longer than width should still appear (no truncation)
	result := WrapText("superlongword short", 5)
	if result != "superlongword\nshort" {
		t.Errorf("got %q, want %q", result, "superlongword\nshort")
	}
}

func TestWrapText_wrapsMultipleLinesCorrectly(t *testing.T) {
	result := WrapText("a b c d e f", 3)
	expected := "a b\nc d\ne f"
	if result != expected {
		t.Errorf("got %q, want %q", result, expected)
	}
}

// ─── Bugmagnet Session 2026-04-26 ────────────────────────────────────────────
// Advanced coverage: edge cases, Unicode, boundaries, security patterns

func TestBugmagnet_Truncate_returnsEmptyWhenBothInputAndMaxLenAreZero(t *testing.T) {
	result := Truncate("", 0)
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestBugmagnet_Truncate_appendsEllipsisNotTruncatesWhenMaxLenNegative_BUG(t *testing.T) {
	t.Skip("BUG: Truncate panics on negative maxLen — s[:maxLen] with negative index causes runtime panic")
	/*
	 * BUG: Truncate does not guard against negative maxLen values.
	 * When maxLen is negative, len(s) <= maxLen is always false for any
	 * non-empty string, so the code reaches s[:maxLen] — a negative slice
	 * index — causing a runtime panic: "slice bounds out of range [:-1]".
	 *
	 * CODE LOCATION: string_utils.go:10-13
	 *
	 * CURRENT CODE:
	 *   if len(s) <= maxLen {
	 *       return s
	 *   }
	 *   return s[:maxLen] + "..."
	 *
	 * PROPOSED FIX:
	 *   if maxLen < 0 {
	 *       maxLen = 0
	 *   }
	 *   if len(s) <= maxLen {
	 *       return s
	 *   }
	 *   return s[:maxLen] + "..."
	 *
	 * EXPECTED: Truncate("Hello", -1) returns "..."  (negative treated as 0)
	 * ACTUAL:   panic: runtime error: slice bounds out of range [:-1]
	 *
	 * MINIMAL REPRODUCTION: Truncate("Hello", -1)
	 */
	result := Truncate("Hello", -1)
	if result != "..." {
		t.Errorf("got %q, want %q", result, "...")
	}
}

func TestBugmagnet_Truncate_handlesWhitespaceOnlyString(t *testing.T) {
	result := Truncate("     ", 3)
	if result != "   ..." {
		t.Errorf("got %q, want %q", result, "   ...")
	}
}

func TestBugmagnet_SlugifyText_handlesSQLInjectionInput(t *testing.T) {
	// Security: SQL injection pattern should produce a safe slug (no special chars)
	result := SlugifyText("'; DROP TABLE users; --")
	if result != "drop-table-users" {
		t.Errorf("got %q, want %q", result, "drop-table-users")
	}
}

func TestBugmagnet_SlugifyText_handlesXSSInput(t *testing.T) {
	result := SlugifyText("<script>alert('xss')</script>")
	if result != "scriptalertxssscript" {
		t.Errorf("got %q, want %q", result, "scriptalertxssscript")
	}
}

func TestBugmagnet_SlugifyText_handlesVeryLongString(t *testing.T) {
	longStr := strings.Repeat("a", 10000)
	result := SlugifyText(longStr)
	if len(result) != 10000 {
		t.Errorf("got length %d, want 10000", len(result))
	}
}

func TestBugmagnet_SlugifyText_handlesStringWithOnlyHyphens(t *testing.T) {
	result := SlugifyText("---")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestBugmagnet_SlugifyText_handlesStringWithOnlySpaces(t *testing.T) {
	result := SlugifyText("   ")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestBugmagnet_SlugifyText_handlesMixedHyphensAndSpaces(t *testing.T) {
	result := SlugifyText("hello - world")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestBugmagnet_CountWords_countsSingleCharWords(t *testing.T) {
	result := CountWords("a b c")
	if result != 3 {
		t.Errorf("got %d, want %d", result, 3)
	}
}

func TestBugmagnet_CountWords_handlesVeryLongWord(t *testing.T) {
	longWord := strings.Repeat("a", 10000)
	result := CountWords(longWord)
	if result != 1 {
		t.Errorf("got %d, want %d", result, 1)
	}
}

func TestBugmagnet_CountWords_handlesManyWords(t *testing.T) {
	words := make([]string, 1000)
	for i := range words {
		words[i] = "word"
	}
	input := strings.Join(words, " ")
	result := CountWords(input)
	if result != 1000 {
		t.Errorf("got %d, want %d", result, 1000)
	}
}

func TestBugmagnet_ExtractInitials_returnsInitialsInUpperCaseForLowercaseInput(t *testing.T) {
	result := ExtractInitials("alice bob")
	if result != "AB" {
		t.Errorf("got %q, want %q", result, "AB")
	}
}

func TestBugmagnet_ExtractInitials_handlesNameWithManyParts(t *testing.T) {
	result := ExtractInitials("A B C D E")
	if result != "ABCDE" {
		t.Errorf("got %q, want %q", result, "ABCDE")
	}
}

func TestBugmagnet_WrapText_handlesWhitespaceOnlyInput(t *testing.T) {
	result := WrapText("   \t\n  ", 10)
	// strings.Fields strips all whitespace, returning no words → ""
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestBugmagnet_WrapText_handlesWidthOfOne(t *testing.T) {
	// width=1: each word on its own line since any two-char word won't fit with another
	result := WrapText("a b c", 1)
	expected := "a\nb\nc"
	if result != expected {
		t.Errorf("got %q, want %q", result, expected)
	}
}

func TestBugmagnet_WrapText_doesNotAddTrailingNewline(t *testing.T) {
	result := WrapText("Hello World", 5)
	if strings.HasSuffix(result, "\n") {
		t.Errorf("result should not end with newline, got %q", result)
	}
}

func TestBugmagnet_WrapText_handlesRepeatedSpaces(t *testing.T) {
	// strings.Fields collapses multiple spaces — verify wrap still works
	result := WrapText("one   two   three", 8)
	if result != "one two\nthree" {
		t.Errorf("got %q, want %q", result, "one two\nthree")
	}
}

// BUG: WrapText uses len(currentLine) and len(w) which count bytes, not runes.
// For Unicode words this may cause lines to wrap earlier than expected.
func TestBugmagnet_WrapText_wrapsAtCorrectWidthWithUnicodeWords_BUG(t *testing.T) {
	t.Skip("BUG: WrapText uses len() (bytes) not utf8.RuneCountInString() (runes); causes premature wrapping for multibyte Unicode")
	/*
	 * BUG: WrapText uses len(currentLine) and len(w) to measure line width,
	 * which counts bytes, not Unicode rune count. For multibyte characters
	 * (accented letters, CJK, emoji, etc.), byte count exceeds rune count,
	 * causing premature line wrapping even when the visible character count
	 * fits within the requested width.
	 *
	 * CODE LOCATION: string_utils.go:58
	 *
	 * CURRENT CODE:
	 *   if len(currentLine)+1+len(w) <= width {
	 *
	 * PROPOSED FIX:
	 *   if utf8.RuneCountInString(currentLine)+1+utf8.RuneCountInString(w) <= width {
	 *
	 * EXPECTED: WrapText("héllo wörld", 11) == "héllo wörld"
	 *           "héllo" has 5 runes, "wörld" has 5 runes, space=1 → 11 runes total,
	 *           which fits exactly in width=11.
	 * ACTUAL:   WrapText("héllo wörld", 11) wraps to "héllo\nwörld"
	 *           because len("héllo")=7 + 1 + len("wörld")=6 = 14 > 11 (byte count).
	 *
	 * MINIMAL REPRODUCTION: WrapText("héllo wörld", 11)
	 */
	result := WrapText("héllo wörld", 11)
	if result != "héllo wörld" {
		t.Errorf("got %q, want %q", result, "héllo wörld")
	}
}
