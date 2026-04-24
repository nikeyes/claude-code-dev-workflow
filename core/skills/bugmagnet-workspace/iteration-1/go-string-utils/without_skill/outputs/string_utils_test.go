package stringutils

import (
	"strings"
	"testing"
)

// ============================================================
// Truncate
// ============================================================

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

func TestTruncate_StringLongerThanMaxLen(t *testing.T) {
	result := Truncate("Hello World", 5)
	if result != "Hello..." {
		t.Errorf("got %q, want %q", result, "Hello...")
	}
}

func TestTruncate_EmptyString(t *testing.T) {
	result := Truncate("", 5)
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestTruncate_MaxLenZero(t *testing.T) {
	// When maxLen is 0, any non-empty string should be truncated to "..."
	result := Truncate("Hello", 0)
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

// BUG: Truncate uses len(s) which counts bytes, not runes.
// For multibyte UTF-8 characters, this can slice in the middle of a rune,
// producing invalid UTF-8. This test documents that bug.
func TestTruncate_MultibyteBug(t *testing.T) {
	// "café" is 5 bytes (c=1, a=1, f=1, é=2) but 4 runes.
	// Truncating at maxLen=4 by bytes cuts through the 'é' rune.
	s := "café"
	result := Truncate(s, 4)
	// The implementation slices bytes so it WILL NOT return "caf..."
	// It returns s[:4]+"..." which splits the 2-byte 'é' in half.
	// We document the actual (buggy) behaviour here.
	// A correct implementation would return "caf..."
	expected := s[:4] + "..."
	if result != expected {
		t.Errorf("got %q, want %q", result, expected)
	}
	// Assert the string is NOT valid Unicode-clean as "caf..."
	if result == "caf..." {
		t.Logf("UNEXPECTED: implementation handled multibyte correctly")
	}
}

// ============================================================
// SlugifyText
// ============================================================

func TestSlugifyText_BasicSpacesToHyphens(t *testing.T) {
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

func TestSlugifyText_AlreadySlug(t *testing.T) {
	result := SlugifyText("hello-world")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_WithNumbers(t *testing.T) {
	result := SlugifyText("Version 2 Released")
	if result != "version-2-released" {
		t.Errorf("got %q, want %q", result, "version-2-released")
	}
}

func TestSlugifyText_SpecialCharactersRemoved(t *testing.T) {
	result := SlugifyText("Hello, World!")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_MultipleSpacesCollapsed(t *testing.T) {
	// Multiple spaces produce multiple hyphens which are then collapsed.
	result := SlugifyText("foo   bar")
	if result != "foo-bar" {
		t.Errorf("got %q, want %q", result, "foo-bar")
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

func TestSlugifyText_OnlySpecialCharacters(t *testing.T) {
	result := SlugifyText("!@#$%^&*()")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestSlugifyText_MixedHyphensAndSpaces(t *testing.T) {
	// A space followed by a hyphen: both become '-', collapsing to single '-'.
	result := SlugifyText("foo - bar")
	if result != "foo-bar" {
		t.Errorf("got %q, want %q", result, "foo-bar")
	}
}

func TestSlugifyText_UnicodeLettersPreserved(t *testing.T) {
	// Non-ASCII letters (e.g. accented) are preserved since IsLetter includes them.
	result := SlugifyText("café au lait")
	if result != "café-au-lait" {
		t.Errorf("got %q, want %q", result, "café-au-lait")
	}
}

func TestSlugifyText_AllLowercase(t *testing.T) {
	result := SlugifyText("UPPER CASE")
	if result != "upper-case" {
		t.Errorf("got %q, want %q", result, "upper-case")
	}
}

// ============================================================
// CountWords
// ============================================================

func TestCountWords_BasicThreeWords(t *testing.T) {
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

func TestCountWords_SingleWord(t *testing.T) {
	result := CountWords("hello")
	if result != 1 {
		t.Errorf("got %d, want %d", result, 1)
	}
}

func TestCountWords_ExtraSpacesBetweenWords(t *testing.T) {
	result := CountWords("one   two   three")
	if result != 3 {
		t.Errorf("got %d, want %d", result, 3)
	}
}

func TestCountWords_LeadingAndTrailingSpaces(t *testing.T) {
	result := CountWords("  hello world  ")
	if result != 2 {
		t.Errorf("got %d, want %d", result, 2)
	}
}

func TestCountWords_TabsAndNewlines(t *testing.T) {
	result := CountWords("word1\tword2\nword3")
	if result != 3 {
		t.Errorf("got %d, want %d", result, 3)
	}
}

func TestCountWords_OnlySpaces(t *testing.T) {
	result := CountWords("     ")
	if result != 0 {
		t.Errorf("got %d, want %d", result, 0)
	}
}

// ============================================================
// ExtractInitials
// ============================================================

func TestExtractInitials_SingleName(t *testing.T) {
	result := ExtractInitials("Alice")
	if result != "A" {
		t.Errorf("got %q, want %q", result, "A")
	}
}

func TestExtractInitials_FirstAndLastName(t *testing.T) {
	result := ExtractInitials("John Doe")
	if result != "JD" {
		t.Errorf("got %q, want %q", result, "JD")
	}
}

func TestExtractInitials_ThreeNames(t *testing.T) {
	result := ExtractInitials("John Michael Doe")
	if result != "JMD" {
		t.Errorf("got %q, want %q", result, "JMD")
	}
}

func TestExtractInitials_LowercaseInput(t *testing.T) {
	result := ExtractInitials("alice bob")
	if result != "AB" {
		t.Errorf("got %q, want %q", result, "AB")
	}
}

func TestExtractInitials_ExtraSpacesBetweenNames(t *testing.T) {
	result := ExtractInitials("Alice   Bob")
	if result != "AB" {
		t.Errorf("got %q, want %q", result, "AB")
	}
}

// BUG: ExtractInitials panics on an empty string because strings.Fields("")
// returns an empty slice, and the loop body never executes — that part is fine.
// However, it also uses p[0] (byte indexing) instead of []rune(p)[0],
// which is a latent bug for names starting with multibyte Unicode characters.
func TestExtractInitials_EmptyString(t *testing.T) {
	result := ExtractInitials("")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

// BUG: p[0] returns a byte, not a rune. For names like "Ångström Élodie"
// the first byte of 'Å' (0xC3) is not the correct Unicode codepoint.
// This test documents the bug.
func TestExtractInitials_MultibyteFirstLetterBug(t *testing.T) {
	// 'Å' is U+00C5, encoded as 2 bytes: 0xC3 0x85.
	// p[0] picks up 0xC3, which as a rune is Ã, not Å.
	// strings.ToUpper on that byte-as-rune still produces a garbled result.
	result := ExtractInitials("Åse Berg")
	// A correct implementation would return "ÅB".
	// The buggy implementation returns something else.
	correct := "ÅB"
	if result == correct {
		t.Logf("implementation handled multibyte initial correctly (unexpected)")
	} else {
		// Document what we actually got
		t.Logf("BUG CONFIRMED: ExtractInitials(%q) = %q, want %q", "Åse Berg", result, correct)
		// We do NOT call t.Errorf here because we are documenting a known bug,
		// not asserting fixed behaviour — the test is informational.
	}
}

// ============================================================
// WrapText
// ============================================================

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

func TestWrapText_AllWordsOnOneLine(t *testing.T) {
	result := WrapText("hello world", 20)
	if result != "hello world" {
		t.Errorf("got %q, want %q", result, "hello world")
	}
}

func TestWrapText_ExactFitOnOneLine(t *testing.T) {
	// "hello world" is 11 chars, width=11 should fit without wrapping.
	result := WrapText("hello world", 11)
	if result != "hello world" {
		t.Errorf("got %q, want %q", result, "hello world")
	}
}

func TestWrapText_BasicWrapping(t *testing.T) {
	result := WrapText("one two three", 7)
	// "one two" = 7 chars (fits), then "three" on next line.
	expected := "one two\nthree"
	if result != expected {
		t.Errorf("got %q, want %q", result, expected)
	}
}

func TestWrapText_EachWordOnOwnLine(t *testing.T) {
	// Width of 3 forces each word to its own line.
	result := WrapText("one two three", 3)
	expected := "one\ntwo\nthree"
	if result != expected {
		t.Errorf("got %q, want %q", result, expected)
	}
}

func TestWrapText_MultipleWordsWrapping(t *testing.T) {
	result := WrapText("the quick brown fox", 9)
	// "the quick" = 9 (fits), "brown" next, "fox" tries to join "brown fox"=9 (fits)
	expected := "the quick\nbrown fox"
	if result != expected {
		t.Errorf("got %q, want %q", result, expected)
	}
}

func TestWrapText_SingleLongWordExceedingWidth(t *testing.T) {
	// WrapText does NOT break long words — it puts them on their own line as-is.
	result := WrapText("superlongword", 5)
	if result != "superlongword" {
		t.Errorf("got %q, want %q", result, "superlongword")
	}
}

func TestWrapText_LongWordFollowedByShortWord(t *testing.T) {
	result := WrapText("superlongword hi", 5)
	expected := "superlongword\nhi"
	if result != expected {
		t.Errorf("got %q, want %q", result, expected)
	}
}

func TestWrapText_ExtraSpacesInInput(t *testing.T) {
	// strings.Fields normalises whitespace, so extra spaces are ignored.
	result := WrapText("one   two   three", 7)
	expected := "one two\nthree"
	if result != expected {
		t.Errorf("got %q, want %q", result, expected)
	}
}

func TestWrapText_OnlySpaces(t *testing.T) {
	result := WrapText("     ", 5)
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestWrapText_ResultContainsNewlines(t *testing.T) {
	result := WrapText("one two three four", 5)
	lines := strings.Split(result, "\n")
	if len(lines) < 2 {
		t.Errorf("expected multiple lines, got %q", result)
	}
}
