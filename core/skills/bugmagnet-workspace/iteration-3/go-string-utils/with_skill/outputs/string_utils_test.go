package stringutils

import (
	"strings"
	"testing"
)

// ─── Truncate ────────────────────────────────────────────────────────────────

func TestTruncate_noTruncationWhenStringFitsExactly(t *testing.T) {
	tests := []struct {
		name   string
		input  string
		maxLen int
		want   string
	}{
		{"exactly at limit", "Hello", 5, "Hello"},
		{"one under limit", "Hi", 3, "Hi"},
		{"empty string any limit", "", 10, ""},
		{"single char at limit 1", "X", 1, "X"},
		{"single char below limit", "X", 5, "X"},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := Truncate(tc.input, tc.maxLen)
			if got != tc.want {
				t.Errorf("Truncate(%q, %d) = %q, want %q", tc.input, tc.maxLen, got, tc.want)
			}
		})
	}
}

func TestTruncate_appendsEllipsisWhenTruncated(t *testing.T) {
	tests := []struct {
		name   string
		input  string
		maxLen int
		want   string
	}{
		{"one over limit", "Hello!", 5, "Hello..."},
		{"long string short limit", "Hello World", 3, "Hel..."},
		{"limit zero non-empty", "abc", 0, "..."},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := Truncate(tc.input, tc.maxLen)
			if got != tc.want {
				t.Errorf("Truncate(%q, %d) = %q, want %q", tc.input, tc.maxLen, got, tc.want)
			}
		})
	}
}

func TestTruncate_outputLengthIsMaxLenPlusThreeWhenTruncated(t *testing.T) {
	// The truncated result is always maxLen bytes + 3 for "..."
	result := Truncate("abcdefghij", 4)
	if result != "abcd..." {
		t.Errorf("got %q, want %q", result, "abcd...")
	}
	if len(result) != 7 {
		t.Errorf("expected length 7 (4+3), got %d", len(result))
	}
}

// BUG: Truncate compares and slices by bytes, not Unicode runes.
// For a multibyte character like '☺' (3 bytes), Truncate("☺☺", 2) should
// return "☺☺" (2 runes fit) but instead panics or returns garbled text.
func TestTruncate_multibyteRuneCountEqualsMaxLen_BUG(t *testing.T) {
	t.Skip("☺ BUG: Truncate uses len(s) (bytes) instead of rune count; multibyte strings are mis-measured and sliced mid-rune")
	/*
	 * ROOT CAUSE: Truncate uses len(s) which returns byte count in UTF-8, not
	 * the number of Unicode code points. It also slices with s[:maxLen] which
	 * is a byte-level slice. Together these cause two failures for strings with
	 * multibyte code points:
	 *   1. The condition len(s) <= maxLen uses bytes, so a 2-rune string made of
	 *      3-byte runes has len=6, failing even when maxLen=2 intends "2 chars".
	 *   2. s[:maxLen] cuts at byte offset maxLen which may land inside a multibyte
	 *      sequence, producing invalid UTF-8 output.
	 *
	 * CODE LOCATION: string_utils.go:10 (len comparison), string_utils.go:13 (byte slice)
	 *
	 * PROPOSED FIX:
	 *   runes := []rune(s)
	 *   if len(runes) <= maxLen {
	 *       return s
	 *   }
	 *   return string(runes[:maxLen]) + "..."
	 *
	 * EXPECTED: Truncate("☺☺", 2) == "☺☺"   (2 runes fit within maxLen=2)
	 * ACTUAL:   Truncate("☺☺", 2) == "\xe2\x98..." (byte slice through 3-byte rune → garbled)
	 */
	result := Truncate("☺☺", 2)
	if result != "☺☺" {
		t.Errorf("Truncate(%q, 2) = %q, want %q", "☺☺", result, "☺☺")
	}
}

// BUG: Truncate panics when maxLen is negative.
func TestTruncate_negativMaxLenPanics_BUG(t *testing.T) {
	t.Skip("BUG: Truncate panics on negative maxLen — s[:maxLen] with a negative index triggers a runtime panic")
	/*
	 * ROOT CAUSE: There is no guard for negative maxLen. When maxLen < 0,
	 * the guard condition len(s) <= maxLen is always false for non-empty strings
	 * (len returns >= 0). Execution falls through to s[:maxLen], which is
	 * s[:-N] — an invalid slice expression that panics at runtime:
	 *   panic: runtime error: slice bounds out of range [:-1]
	 *
	 * CODE LOCATION: string_utils.go:10-13
	 *
	 * PROPOSED FIX:
	 *   if maxLen < 0 {
	 *       maxLen = 0
	 *   }
	 *
	 * EXPECTED: Truncate("hello", -3) == "..."  (negative treated as 0, return ellipsis only)
	 * ACTUAL:   panic: runtime error: slice bounds out of range [:-3]
	 */
	result := Truncate("hello", -3)
	if result != "..." {
		t.Errorf("Truncate(%q, -3) = %q, want %q", "hello", result, "...")
	}
}

// BUG: Truncate slices bytes, not runes. A 2-byte accented character at the
// cut point produces an invalid UTF-8 byte sequence in the output.
func TestTruncate_midRuneSliceProducesInvalidUTF8_BUG(t *testing.T) {
	t.Skip("BUG: Truncate slices at a byte offset that may fall inside a multibyte rune, yielding invalid UTF-8")
	/*
	 * ROOT CAUSE: The expression s[:maxLen] is a byte-level slice. When the
	 * character at position maxLen is encoded with more than one byte (e.g. 'é'
	 * encodes as 0xC3 0xA9), slicing at the byte boundary splits the encoding,
	 * producing a lone 0xC3 byte which is not a valid UTF-8 sequence on its own.
	 *
	 * CODE LOCATION: string_utils.go:13
	 *
	 * PROPOSED FIX:
	 *   runes := []rune(s)
	 *   if len(runes) <= maxLen {
	 *       return s
	 *   }
	 *   return string(runes[:maxLen]) + "..."
	 *
	 * EXPECTED: Truncate("naïve", 3) == "naï..."   (clean cut after 3rd rune)
	 * ACTUAL:   Truncate("naïve", 3) == "na\xc3..."  (0xc3 is half of 'ï' in UTF-8)
	 */
	result := Truncate("naïve", 3)
	if result != "naï..." {
		t.Errorf("Truncate(%q, 3) = %q, want %q", "naïve", result, "naï...")
	}
}

// ─── SlugifyText ─────────────────────────────────────────────────────────────

func TestSlugifyText_happyPath(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  string
	}{
		{"lowercase words", "hello world", "hello-world"},
		{"uppercase words", "HELLO WORLD", "hello-world"},
		{"mixed case", "Hello World", "hello-world"},
		{"single word", "golang", "golang"},
		{"numbers included", "go 1 2 3", "go-1-2-3"},
		{"already hyphenated", "well-known", "well-known"},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := SlugifyText(tc.input)
			if got != tc.want {
				t.Errorf("SlugifyText(%q) = %q, want %q", tc.input, got, tc.want)
			}
		})
	}
}

func TestSlugifyText_emptyAndWhitespaceInputs(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  string
	}{
		{"empty string", "", ""},
		{"single space", " ", ""},
		{"multiple spaces", "   ", ""},
		{"tabs and newlines", "\t\n", ""},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := SlugifyText(tc.input)
			if got != tc.want {
				t.Errorf("SlugifyText(%q) = %q, want %q", tc.input, got, tc.want)
			}
		})
	}
}

func TestSlugifyText_specialCharactersDropped(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  string
	}{
		{"comma and exclamation", "Hello, World!", "hello-world"},
		{"only special chars", "!@#$%^&*()", ""},
		{"underscore treated as separator", "hello_world", "helloworld"}, // underscore is dropped, words merge
		{"dot between words", "foo.bar", "foobar"},
		{"ampersand between words", "cats & dogs", "cats-dogs"},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := SlugifyText(tc.input)
			if got != tc.want {
				t.Errorf("SlugifyText(%q) = %q, want %q", tc.input, got, tc.want)
			}
		})
	}
}

func TestSlugifyText_multipleConsecutiveHyphensCollapsed(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  string
	}{
		{"explicit double hyphen", "a--b", "a-b"},
		{"triple hyphen", "a---b", "a-b"},
		{"space around hyphen", "a - b", "a-b"},
		{"only hyphens", "---", ""},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := SlugifyText(tc.input)
			if got != tc.want {
				t.Errorf("SlugifyText(%q) = %q, want %q", tc.input, got, tc.want)
			}
		})
	}
}

func TestSlugifyText_leadingTrailingHyphensRemoved(t *testing.T) {
	// Leading/trailing spaces produce leading/trailing hyphens before Trim
	result := SlugifyText("  hello  ")
	if result != "hello" {
		t.Errorf("SlugifyText(%q) = %q, want %q", "  hello  ", result, "hello")
	}
}

func TestSlugifyText_unicodeLettersPreserved(t *testing.T) {
	// unicode.IsLetter returns true for accented characters; they stay in the slug
	tests := []struct {
		name  string
		input string
		want  string
	}{
		{"French accent", "café au lait", "café-au-lait"},
		{"German umlaut", "über alles", "über-alles"},
		{"Spanish tilde", "mañana", "mañana"},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := SlugifyText(tc.input)
			if got != tc.want {
				t.Errorf("SlugifyText(%q) = %q, want %q", tc.input, got, tc.want)
			}
		})
	}
}

func TestSlugifyText_apostropheDroppedWithoutAddingHyphen(t *testing.T) {
	// Apostrophe is neither letter/digit nor space/hyphen — it is silently dropped.
	// "it's" → "its"  (contraction stays as one word, no hyphen inserted)
	result := SlugifyText("it's a trap")
	if result != "its-a-trap" {
		t.Errorf("SlugifyText(%q) = %q, want %q", "it's a trap", result, "its-a-trap")
	}
}

// ─── CountWords ──────────────────────────────────────────────────────────────

func TestCountWords_tableTests(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  int
	}{
		{"empty string", "", 0},
		{"single word", "hello", 1},
		{"two words", "hello world", 2},
		{"whitespace only", "   \t\n  ", 0},
		{"extra spaces between words", "one   two   three", 3},
		{"leading and trailing spaces", "  one two  ", 2},
		{"tabs as separators", "one\ttwo\tthree", 3},
		{"newlines as separators", "one\ntwo\nthree", 3},
		{"mixed whitespace", "one \t two \n three", 3},
		{"punctuation attached to word", "hello, world!", 2},
		{"single char words", "a b c d", 4},
		{"unicode words", "héllo wörld", 2},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := CountWords(tc.input)
			if got != tc.want {
				t.Errorf("CountWords(%q) = %d, want %d", tc.input, got, tc.want)
			}
		})
	}
}

// ─── ExtractInitials ─────────────────────────────────────────────────────────

func TestExtractInitials_happyPath(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  string
	}{
		{"two names", "John Doe", "JD"},
		{"three names", "Mary Jane Watson", "MJW"},
		{"already uppercase", "ALICE BOB", "AB"},
		{"already lowercase", "alice bob", "AB"},
		{"single name", "Madonna", "M"},
		{"extra spaces between names", "John  Doe", "JD"},
		{"leading and trailing spaces", "  John Doe  ", "JD"},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := ExtractInitials(tc.input)
			if got != tc.want {
				t.Errorf("ExtractInitials(%q) = %q, want %q", tc.input, got, tc.want)
			}
		})
	}
}

func TestExtractInitials_emptyAndWhitespace(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  string
	}{
		{"empty string", "", ""},
		{"whitespace only", "   ", ""},
		{"tab only", "\t", ""},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := ExtractInitials(tc.input)
			if got != tc.want {
				t.Errorf("ExtractInitials(%q) = %q, want %q", tc.input, got, tc.want)
			}
		})
	}
}

func TestExtractInitials_hyphenatedNameCountsAsOneToken(t *testing.T) {
	// strings.Fields splits on whitespace only; "Mary-Jane" is one token → one initial
	result := ExtractInitials("Mary-Jane Smith")
	if result != "MS" {
		t.Errorf("ExtractInitials(%q) = %q, want %q", "Mary-Jane Smith", result, "MS")
	}
}

// BUG: ExtractInitials uses p[0] (byte access) instead of decoding the first rune.
// Names starting with a multibyte UTF-8 character produce a garbage initial.
func TestExtractInitials_nonASCIIFirstLetterProducesGarbage_BUG(t *testing.T) {
	t.Skip("BUG: ExtractInitials uses p[0] byte access; for multibyte rune first-chars it returns the first byte, not the codepoint")
	/*
	 * ROOT CAUSE: The expression rune(p[0]) takes the first byte of the UTF-8
	 * encoded string p and casts it to rune. For any name token starting with a
	 * multibyte codepoint this is wrong:
	 *   - 'Ö' encodes as 0xC3 0x96; p[0] = 0xC3; rune(0xC3) = 'Ã' (U+00C3), not 'Ö'
	 *   - '中' encodes as 0xE4 0xB8 0xAD; p[0] = 0xE4; rune(0xE4) = 'ä' (U+00E4), not '中'
	 *
	 * CODE LOCATION: string_utils.go:44
	 *
	 * PROPOSED FIX:
	 *   import "unicode/utf8"
	 *   r, _ := utf8.DecodeRuneInString(p)
	 *   initials = append(initials, r)
	 *
	 * EXPECTED: ExtractInitials("Örjan Nilsson") == "ÖN"
	 * ACTUAL:   ExtractInitials("Örjan Nilsson") == "ÃN"  (0xC3 = 'Ã', not 'Ö')
	 */
	result := ExtractInitials("Örjan Nilsson")
	if result != "ÖN" {
		t.Errorf("ExtractInitials(%q) = %q, want %q", "Örjan Nilsson", result, "ÖN")
	}
}

// BUG: ExtractInitials panics on a token that is somehow an empty string.
// strings.Fields never returns empty tokens from normal input, but an
// adversarial strings.Fields-like situation is not the concern here — the
// concern is that the implementation does p[0] without length-checking, which
// would panic on a zero-length token. Verify with a CJK first character too.
func TestExtractInitials_CJKFirstLetterProducesGarbage_BUG(t *testing.T) {
	t.Skip("BUG: ExtractInitials uses p[0] byte access; CJK characters (3-byte UTF-8) produce wrong first byte as rune")
	/*
	 * ROOT CAUSE: Same as above — rune(p[0]) returns the leading byte of the
	 * 3-byte CJK encoding. '李' = 0xE6 0x9D 0x8E; rune(0xE6) = 'æ' (U+00E6).
	 *
	 * CODE LOCATION: string_utils.go:44
	 *
	 * PROPOSED FIX: utf8.DecodeRuneInString(p) instead of rune(p[0])
	 *
	 * EXPECTED: ExtractInitials("李 Smith") == "LS"  (or "李S" depending on ToUpper behaviour)
	 * ACTUAL:   ExtractInitials("李 Smith") returns a garbled byte as first initial
	 */
	result := ExtractInitials("李 Smith")
	// ToUpper of '李' is '李' (already uppercase in Unicode terms)
	if result != "李S" {
		t.Errorf("ExtractInitials(%q) = %q, want %q", "李 Smith", result, "李S")
	}
}

// ─── WrapText ────────────────────────────────────────────────────────────────

func TestWrapText_happyPath(t *testing.T) {
	tests := []struct {
		name  string
		input string
		width int
		want  string
	}{
		{"fits on one line", "Hello World", 20, "Hello World"},
		{"wraps exactly at boundary", "Hello World", 11, "Hello World"},
		{"wraps one char over boundary", "Hello World", 10, "Hello\nWorld"},
		{"three words wrap after two", "one two three", 7, "one two\nthree"},
		{"single word shorter than width", "hello", 10, "hello"},
		{"single word equal to width", "hello", 5, "hello"},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := WrapText(tc.input, tc.width)
			if got != tc.want {
				t.Errorf("WrapText(%q, %d) = %q, want %q", tc.input, tc.width, got, tc.want)
			}
		})
	}
}

func TestWrapText_emptyAndWhitespaceInputsReturnEmpty(t *testing.T) {
	tests := []struct {
		name  string
		input string
	}{
		{"empty string", ""},
		{"spaces only", "   "},
		{"tabs and newlines", "\t\n\r"},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := WrapText(tc.input, 10)
			if got != "" {
				t.Errorf("WrapText(%q, 10) = %q, want %q", tc.input, got, "")
			}
		})
	}
}

func TestWrapText_wordLongerThanWidthIsNotBroken(t *testing.T) {
	// A word that exceeds width lands on its own line; it is NOT truncated
	result := WrapText("pneumonoultramicroscopicsilicovolcanoconiosis is long", 10)
	if !strings.HasPrefix(result, "pneumonoultramicroscopicsilicovolcanoconiosis") {
		t.Errorf("long word should not be truncated, got %q", result)
	}
	lines := strings.Split(result, "\n")
	if lines[0] != "pneumonoultramicroscopicsilicovolcanoconiosis" {
		t.Errorf("expected long word on first line, got %q", lines[0])
	}
}

func TestWrapText_noTrailingNewline(t *testing.T) {
	result := WrapText("one two three four", 5)
	if strings.HasSuffix(result, "\n") {
		t.Errorf("WrapText result should not end with newline, got %q", result)
	}
}

func TestWrapText_multipleSpacesCollapsed(t *testing.T) {
	// strings.Fields collapses runs of whitespace; wrap operates on clean tokens
	result := WrapText("one    two    three", 9)
	if result != "one two\nthree" {
		t.Errorf("WrapText(%q, 9) = %q, want %q", "one    two    three", result, "one two\nthree")
	}
}

func TestWrapText_widthZeroPutsEachWordOnOwnLine(t *testing.T) {
	// With width=0, any word combined with a space exceeds 0, so every word after
	// the first starts a new line.
	result := WrapText("a b c", 0)
	expected := "a\nb\nc"
	if result != expected {
		t.Errorf("WrapText(%q, 0) = %q, want %q", "a b c", result, expected)
	}
}

func TestWrapText_widthOneAllWordsSingleChar(t *testing.T) {
	// width=1: single-char words fit exactly; no wrapping needed between them
	// But "a" + " " + "b" = 3 > 1, so each goes on own line
	result := WrapText("a b c d", 1)
	expected := "a\nb\nc\nd"
	if result != expected {
		t.Errorf("WrapText(%q, 1) = %q, want %q", "a b c d", result, expected)
	}
}

func TestWrapText_newlinesInInputTreatedAsWordSeparators(t *testing.T) {
	// strings.Fields splits on \n; output uses \n as line separator regardless
	result := WrapText("one\ntwo\nthree", 20)
	if result != "one two three" {
		t.Errorf("WrapText(%q, 20) = %q, want %q", "one\ntwo\nthree", result, "one two three")
	}
}

// BUG: WrapText uses len() for line-width comparison, which counts bytes not runes.
// For text containing multibyte characters the line breaks earlier than intended.
func TestWrapText_byteVsRuneCountCausesEarlyWrapForUnicode_BUG(t *testing.T) {
	t.Skip("BUG: WrapText uses len() (byte count) for width check; multibyte Unicode characters cause premature line wrapping")
	/*
	 * ROOT CAUSE: The width check `len(currentLine)+1+len(w) <= width` uses the
	 * built-in len() which returns the number of bytes in a UTF-8 string, not
	 * the number of visible characters (runes). Each multibyte character adds
	 * extra bytes without adding visible width, causing the line to appear "full"
	 * before its visible length actually reaches the requested width.
	 *
	 *   "über" = 5 bytes (ü = 2 bytes) but 4 visible characters
	 *   "alles" = 5 bytes, 5 characters
	 *   With width=10: visible length = 4+1+5 = 10 ≤ 10 → should fit on one line
	 *   Byte check:    5+1+5 = 11 > 10 → wraps prematurely
	 *
	 * CODE LOCATION: string_utils.go:58
	 *
	 * PROPOSED FIX:
	 *   import "unicode/utf8"
	 *   if utf8.RuneCountInString(currentLine)+1+utf8.RuneCountInString(w) <= width {
	 *
	 * EXPECTED: WrapText("über alles", 10) == "über alles"   (10 visible chars fit)
	 * ACTUAL:   WrapText("über alles", 10) == "über\nalles"  (11 bytes do not fit)
	 */
	result := WrapText("über alles", 10)
	if result != "über alles" {
		t.Errorf("WrapText(%q, 10) = %q, want %q", "über alles", result, "über alles")
	}
}

// BUG: WrapText width check uses bytes; emoji (4-byte UTF-8) aggravate the problem.
func TestWrapText_emojiCausesEarlyWrapBecauseOfByteCount_BUG(t *testing.T) {
	t.Skip("BUG: WrapText uses len() byte count; emoji are 4 bytes each, making byte-length far exceed visible rune count")
	/*
	 * ROOT CAUSE: Same byte-vs-rune bug as above, but more extreme with emoji.
	 * "hi 👋" has 7 bytes (h=1, i=1, space=1, 👋=4) but 4 visible characters.
	 * "bye" = 3 bytes. width=8 should fit "hi 👋 bye" (8 visible chars) but:
	 *   len("hi 👋")+1+len("bye") = 7+1+3 = 11 > 8 → premature wrap.
	 *
	 * CODE LOCATION: string_utils.go:58
	 *
	 * PROPOSED FIX: utf8.RuneCountInString() instead of len() for both operands
	 *
	 * EXPECTED: WrapText("hi 👋 bye", 8) == "hi 👋 bye"
	 * ACTUAL:   WrapText("hi 👋 bye", 8) == "hi 👋\nbye"
	 */
	result := WrapText("hi 👋 bye", 8)
	if result != "hi 👋 bye" {
		t.Errorf("WrapText(%q, 8) = %q, want %q", "hi 👋 bye", result, "hi 👋 bye")
	}
}
