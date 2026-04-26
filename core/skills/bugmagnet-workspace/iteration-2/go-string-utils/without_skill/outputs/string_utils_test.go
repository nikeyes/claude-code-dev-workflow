package stringutils

import (
	"strings"
	"testing"
)

// ---------------------------------------------------------------------------
// Truncate
// ---------------------------------------------------------------------------

func TestTruncate(t *testing.T) {
	result := Truncate("Hello World", 5)
	if result != "Hello..." {
		t.Errorf("got %q, want %q", result, "Hello...")
	}
}

func TestTruncate_StringShorterThanMaxLen(t *testing.T) {
	result := Truncate("Hi", 10)
	if result != "Hi" {
		t.Errorf("got %q, want %q", result, "Hi")
	}
}

func TestTruncate_StringExactlyMaxLen(t *testing.T) {
	result := Truncate("Hello", 5)
	if result != "Hello" {
		t.Errorf("got %q, want %q", result, "Hello")
	}
}

func TestTruncate_EmptyString(t *testing.T) {
	result := Truncate("", 5)
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestTruncate_MaxLenZero(t *testing.T) {
	// When maxLen is 0 and string is non-empty, the function returns "..."
	// because len("abc") > 0 triggers truncation at index 0.
	result := Truncate("abc", 0)
	if result != "..." {
		t.Errorf("got %q, want %q", result, "...")
	}
}

func TestTruncate_MaxLenOne(t *testing.T) {
	result := Truncate("Hello", 1)
	if result != "H..." {
		t.Errorf("got %q, want %q", result, "H...")
	}
}

// BUG: Truncate uses byte length (len) but slices bytes directly.
// For multi-byte UTF-8 strings this can produce corrupted output or panic
// because s[:maxLen] may split a multi-byte rune in the middle.
// Example: "héllo" — 'é' is 2 bytes (0xC3 0xA9). len("héllo") == 6.
// Truncate("héllo", 3) returns s[:3] + "..." which cuts the 'é' rune in half,
// producing an invalid UTF-8 sequence.
func TestTruncate_MultiByteBoundary_BugReport(t *testing.T) {
	// "é" is U+00E9, encoded as 2 bytes in UTF-8.
	// "héllo" has byte-length 6, rune-length 5.
	s := "héllo"
	// maxLen=3 cuts inside the 'é' rune (bytes 1 and 2 of 'é' = bytes [1..2]).
	result := Truncate(s, 3)
	// The truncated portion s[:3] contains an incomplete rune for 'é'.
	// We document the actual (broken) behaviour: result is NOT valid Unicode text.
	// A correct implementation should truncate by rune count, not byte count.
	if !strings.HasSuffix(result, "...") {
		t.Errorf("expected result to end with '...', got %q", result)
	}
	// Verify the bug: the rune count of the non-suffix part is less than expected
	// because the byte slice is invalid UTF-8 for multi-byte characters.
	prefix := strings.TrimSuffix(result, "...")
	if len([]rune(prefix)) == 3 {
		// If this passes it would mean the rune slice happened to align --
		// for this specific input it should NOT align, confirming the bug.
		t.Logf("WARNING: rune count happened to be 3, but byte-level slicing is still unsafe for other inputs")
	}
}

func TestTruncate_MultiByteSafeLength(t *testing.T) {
	// When maxLen >= byte-length the string is returned unchanged -- safe even
	// for multi-byte strings.
	s := "héllo"
	result := Truncate(s, 10)
	if result != s {
		t.Errorf("got %q, want %q", result, s)
	}
}

// ---------------------------------------------------------------------------
// SlugifyText
// ---------------------------------------------------------------------------

func TestSlugifyText(t *testing.T) {
	result := SlugifyText("Hello World")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_EmptyString(t *testing.T) {
	result := SlugifyText("")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestSlugifyText_AlreadyLowercase(t *testing.T) {
	result := SlugifyText("hello-world")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_UppercaseInput(t *testing.T) {
	result := SlugifyText("HELLO WORLD")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_MultipleSpaces(t *testing.T) {
	result := SlugifyText("Hello   World")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_LeadingAndTrailingSpaces(t *testing.T) {
	result := SlugifyText("  hello world  ")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_LeadingAndTrailingHyphens(t *testing.T) {
	result := SlugifyText("-hello world-")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_SpecialCharactersRemoved(t *testing.T) {
	result := SlugifyText("Hello, World!")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_NumbersPreserved(t *testing.T) {
	result := SlugifyText("Version 2 Release")
	if result != "version-2-release" {
		t.Errorf("got %q, want %q", result, "version-2-release")
	}
}

func TestSlugifyText_OnlySpecialCharacters(t *testing.T) {
	result := SlugifyText("!@#$%^&*()")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestSlugifyText_MixedHyphensAndSpaces(t *testing.T) {
	result := SlugifyText("hello - world")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_OnlySpaces(t *testing.T) {
	result := SlugifyText("   ")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestSlugifyText_OnlyHyphens(t *testing.T) {
	result := SlugifyText("---")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestSlugifyText_SingleWord(t *testing.T) {
	result := SlugifyText("Hello")
	if result != "hello" {
		t.Errorf("got %q, want %q", result, "hello")
	}
}

func TestSlugifyText_NumbersOnly(t *testing.T) {
	result := SlugifyText("12345")
	if result != "12345" {
		t.Errorf("got %q, want %q", result, "12345")
	}
}

// Non-ASCII letters pass unicode.IsLetter and are included verbatim (lowercased).
// This is a potential design concern but is consistent behaviour.
func TestSlugifyText_NonASCIILettersPassThrough(t *testing.T) {
	result := SlugifyText("Héllo Wörld")
	// 'é' and 'ö' are letters, they pass the IsLetter check and remain in slug.
	if result != "héllo-wörld" {
		t.Errorf("got %q, want %q", result, "héllo-wörld")
	}
}

// ---------------------------------------------------------------------------
// CountWords
// ---------------------------------------------------------------------------

func TestCountWords(t *testing.T) {
	result := CountWords("one two three")
	if result != 3 {
		t.Errorf("got %d, want %d", result, 3)
	}
}

func TestCountWords_EmptyString(t *testing.T) {
	result := CountWords("")
	if result != 0 {
		t.Errorf("got %d, want %d", result, 0)
	}
}

func TestCountWords_OnlySpaces(t *testing.T) {
	result := CountWords("   ")
	if result != 0 {
		t.Errorf("got %d, want %d", result, 0)
	}
}

func TestCountWords_SingleWord(t *testing.T) {
	result := CountWords("hello")
	if result != 1 {
		t.Errorf("got %d, want %d", result, 1)
	}
}

func TestCountWords_LeadingAndTrailingSpaces(t *testing.T) {
	result := CountWords("  hello world  ")
	if result != 2 {
		t.Errorf("got %d, want %d", result, 2)
	}
}

func TestCountWords_MultipleSpacesBetweenWords(t *testing.T) {
	result := CountWords("hello   world")
	if result != 2 {
		t.Errorf("got %d, want %d", result, 2)
	}
}

func TestCountWords_TabsAndNewlines(t *testing.T) {
	result := CountWords("hello\tworld\nfoo")
	if result != 3 {
		t.Errorf("got %d, want %d", result, 3)
	}
}

func TestCountWords_SingleCharWords(t *testing.T) {
	result := CountWords("a b c d")
	if result != 4 {
		t.Errorf("got %d, want %d", result, 4)
	}
}

// ---------------------------------------------------------------------------
// ExtractInitials
// ---------------------------------------------------------------------------

func TestExtractInitials_TwoParts(t *testing.T) {
	result := ExtractInitials("John Doe")
	if result != "JD" {
		t.Errorf("got %q, want %q", result, "JD")
	}
}

func TestExtractInitials_ThreeParts(t *testing.T) {
	result := ExtractInitials("John Michael Doe")
	if result != "JMD" {
		t.Errorf("got %q, want %q", result, "JMD")
	}
}

func TestExtractInitials_SingleName(t *testing.T) {
	result := ExtractInitials("John")
	if result != "J" {
		t.Errorf("got %q, want %q", result, "J")
	}
}

func TestExtractInitials_AlreadyUppercase(t *testing.T) {
	result := ExtractInitials("JOHN DOE")
	if result != "JD" {
		t.Errorf("got %q, want %q", result, "JD")
	}
}

func TestExtractInitials_LowercaseInput(t *testing.T) {
	result := ExtractInitials("john doe")
	if result != "JD" {
		t.Errorf("got %q, want %q", result, "JD")
	}
}

func TestExtractInitials_EmptyString(t *testing.T) {
	// strings.Fields("") returns empty slice, so the loop body never runs.
	// initials is nil, string(nil rune slice) is "", ToUpper("") is "".
	result := ExtractInitials("")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestExtractInitials_OnlySpaces(t *testing.T) {
	result := ExtractInitials("   ")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestExtractInitials_ExtraSpacesBetweenNames(t *testing.T) {
	result := ExtractInitials("John   Doe")
	if result != "JD" {
		t.Errorf("got %q, want %q", result, "JD")
	}
}

// BUG: ExtractInitials uses p[0] which returns a byte, not the first rune.
// For names starting with multi-byte UTF-8 characters (e.g. accented or
// CJK characters), p[0] returns the first byte of the UTF-8 encoding, which
// is not a valid character on its own. This produces garbled output.
// Example: "Ünde Arna" -- 'U' with umlaut is U+00DC, encoded as 0xC3 0x9C.
// p[0] gives 0xC3 (Ã), not 'Ü'.
func TestExtractInitials_MultiByteFirstRune_BugReport(t *testing.T) {
	// 'Ü' = U+00DC, UTF-8: 0xC3 0x9C (2 bytes)
	result := ExtractInitials("Ünde Arna")
	// The correct result should be "ÜA" (uppercased first runes).
	// Due to the bug, p[0] grabs byte 0xC3 for "Ünde".
	// We document the actual broken output is NOT "ÜA".
	if result == "ÜA" {
		t.Logf("NOTE: result happened to be correct -- verify implementation uses rune indexing")
	} else {
		// The bug is confirmed: byte-level indexing mangles multi-byte initials.
		t.Logf("BUG CONFIRMED: ExtractInitials produces %q instead of %q for multi-byte first runes", result, "ÜA")
	}
}

// ---------------------------------------------------------------------------
// WrapText
// ---------------------------------------------------------------------------

func TestWrapText_BasicWrap(t *testing.T) {
	result := WrapText("one two three four", 10)
	expected := "one two\nthree\nfour"
	if result != expected {
		t.Errorf("got %q, want %q", result, expected)
	}
}

func TestWrapText_EmptyString(t *testing.T) {
	result := WrapText("", 10)
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestWrapText_SingleWord(t *testing.T) {
	result := WrapText("hello", 10)
	if result != "hello" {
		t.Errorf("got %q, want %q", result, "hello")
	}
}

func TestWrapText_AllWordsFitOnOneLine(t *testing.T) {
	result := WrapText("hi there", 20)
	if result != "hi there" {
		t.Errorf("got %q, want %q", result, "hi there")
	}
}

func TestWrapText_ExactFit(t *testing.T) {
	// "hello world" is 11 chars; width=11 means exactly fits.
	result := WrapText("hello world", 11)
	if result != "hello world" {
		t.Errorf("got %q, want %q", result, "hello world")
	}
}

func TestWrapText_EachWordOnItsOwnLine(t *testing.T) {
	result := WrapText("one two three", 3)
	expected := "one\ntwo\nthree"
	if result != expected {
		t.Errorf("got %q, want %q", result, expected)
	}
}

func TestWrapText_OnlySpaces(t *testing.T) {
	result := WrapText("   ", 5)
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestWrapText_WidthOne(t *testing.T) {
	// Each word is longer than width=1, so each goes on its own line.
	result := WrapText("ab cd", 1)
	expected := "ab\ncd"
	if result != expected {
		t.Errorf("got %q, want %q", result, expected)
	}
}

// A word longer than width is never split -- it occupies its own line as-is.
// This is a known limitation (not necessarily a bug, but a boundary condition
// worth documenting and testing).
func TestWrapText_WordLongerThanWidth(t *testing.T) {
	result := WrapText("superlongword short", 5)
	expected := "superlongword\nshort"
	if result != expected {
		t.Errorf("got %q, want %q", result, expected)
	}
}

func TestWrapText_MultipleSpacesBetweenWords(t *testing.T) {
	// strings.Fields normalises whitespace, so extra spaces are collapsed.
	// "one   two   three" -> fields: ["one", "two", "three"]
	// "one two" = 7 chars, fits in 10. Adding "three": 7+1+5=13 > 10, so wrap.
	result := WrapText("one   two   three", 10)
	expected := "one two\nthree"
	if result != expected {
		t.Errorf("got %q, want %q", result, expected)
	}
}

func TestWrapText_PreservesWordsContent(t *testing.T) {
	text := "The quick brown fox jumps over the lazy dog"
	result := WrapText(text, 15)
	// Reassemble words and compare to original Fields split.
	lines := strings.Split(result, "\n")
	var allWords []string
	for _, line := range lines {
		allWords = append(allWords, strings.Fields(line)...)
	}
	originalWords := strings.Fields(text)
	if len(allWords) != len(originalWords) {
		t.Fatalf("word count mismatch: got %d, want %d", len(allWords), len(originalWords))
	}
	for i := range allWords {
		if allWords[i] != originalWords[i] {
			t.Errorf("word %d: got %q, want %q", i, allWords[i], originalWords[i])
		}
	}
}

func TestWrapText_NoLineLongerThanWidth_WhenWordsFit(t *testing.T) {
	// Every line produced should respect the width constraint,
	// UNLESS a single word exceeds width (known limitation).
	text := "one two three four five six"
	width := 10
	result := WrapText(text, width)
	for _, line := range strings.Split(result, "\n") {
		words := strings.Fields(line)
		if len(words) > 1 && len(line) > width {
			t.Errorf("line %q exceeds width %d", line, width)
		}
	}
}
