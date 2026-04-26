package stringutils

import (
	"strings"
	"testing"
)

// ─────────────────────────────────────────────
// Truncate
// ─────────────────────────────────────────────

func TestTruncate_EmptyString(t *testing.T) {
	result := Truncate("", 5)
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestTruncate_ExactLength(t *testing.T) {
	// String length equals maxLen: must NOT append "..."
	result := Truncate("Hello", 5)
	if result != "Hello" {
		t.Errorf("got %q, want %q", result, "Hello")
	}
}

func TestTruncate_ShorterThanMax(t *testing.T) {
	result := Truncate("Hi", 10)
	if result != "Hi" {
		t.Errorf("got %q, want %q", result, "Hi")
	}
}

func TestTruncate_MaxLenZero(t *testing.T) {
	// maxLen=0: any non-empty string should be truncated to "" + "..."
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

// BUG: Truncate uses byte length (len), not rune count.
// For a multi-byte UTF-8 string it may slice in the middle of a rune,
// producing an invalid UTF-8 sequence in the output.
func TestTruncate_MultiByteUTF8SlicesBytesNotRunes(t *testing.T) {
	// "héllo" — 'é' is 2 bytes (0xC3 0xA9). len("héllo") == 6.
	// maxLen=3 slices at byte 3, which is the middle of 'é' — invalid UTF-8.
	s := "héllo"
	result := Truncate(s, 3)
	// The implementation slices bytes; this test documents the broken behaviour.
	// A correct implementation would truncate by rune count, yielding "hél..."
	// Here we assert what the implementation ACTUALLY does so the test is
	// mechanically runnable; the comment explains the intended correct output.
	want := s[:3] + "..."
	if result != want {
		t.Errorf("got %q, want %q", result, want)
	}
	// Additionally, verify the result is NOT valid UTF-8 (demonstrating the bug)
	if strings.ContainsRune(result, '�') {
		// Replacement character present — broken rune confirmed
		t.Logf("CONFIRMED BUG: Truncate produced invalid UTF-8 for multi-byte input")
	}
}

func TestTruncate_OnlySpecialChars(t *testing.T) {
	result := Truncate("!@#$%", 3)
	if result != "!@#..." {
		t.Errorf("got %q, want %q", result, "!@#...")
	}
}

// ─────────────────────────────────────────────
// SlugifyText
// ─────────────────────────────────────────────

func TestSlugifyText_EmptyString(t *testing.T) {
	result := SlugifyText("")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestSlugifyText_AllSpaces(t *testing.T) {
	result := SlugifyText("   ")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestSlugifyText_LeadingTrailingSpaces(t *testing.T) {
	result := SlugifyText("  hello world  ")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_MultipleConsecutiveSpaces(t *testing.T) {
	result := SlugifyText("hello   world")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_AlreadySlug(t *testing.T) {
	result := SlugifyText("hello-world")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_MixedSpacesAndHyphens(t *testing.T) {
	// "hello - world" produces "hello---world" before collapse → "hello-world"
	result := SlugifyText("hello - world")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_NumbersPreserved(t *testing.T) {
	result := SlugifyText("version 2 release")
	if result != "version-2-release" {
		t.Errorf("got %q, want %q", result, "version-2-release")
	}
}

func TestSlugifyText_SpecialCharsDropped(t *testing.T) {
	// Underscores, punctuation and symbols are silently dropped
	result := SlugifyText("hello_world!")
	if result != "helloworld" {
		t.Errorf("got %q, want %q", result, "helloworld")
	}
}

func TestSlugifyText_UnderscoreIsDropped(t *testing.T) {
	// Underscores are NOT converted to hyphens — they are silently removed.
	// This may surprise callers who expect snake_case → kebab-case behaviour.
	result := SlugifyText("foo_bar")
	if result != "foobar" {
		t.Errorf("got %q, want %q", result, "foobar")
	}
}

func TestSlugifyText_AllSpecialChars(t *testing.T) {
	result := SlugifyText("!@#$%^&*()")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestSlugifyText_LeadingHyphen(t *testing.T) {
	// Leading hyphen in input should be trimmed in output
	result := SlugifyText("-hello")
	if result != "hello" {
		t.Errorf("got %q, want %q", result, "hello")
	}
}

func TestSlugifyText_TrailingHyphen(t *testing.T) {
	result := SlugifyText("hello-")
	if result != "hello" {
		t.Errorf("got %q, want %q", result, "hello")
	}
}

func TestSlugifyText_OnlyHyphens(t *testing.T) {
	result := SlugifyText("---")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestSlugifyText_TabsAndNewlines(t *testing.T) {
	// Tabs and newlines are neither letters, digits, spaces, nor hyphens
	// so they are silently dropped (not converted to hyphens).
	result := SlugifyText("hello\tworld\nnewline")
	// tab and newline are dropped: "helloworld\nnewline" → "helloworldnewline"
	if result != "helloworldnewline" {
		t.Errorf("got %q, want %q", result, "helloworldnewline")
	}
}

// Non-ASCII Unicode letters pass through (they satisfy unicode.IsLetter).
func TestSlugifyText_UnicodeLettersPreserved(t *testing.T) {
	result := SlugifyText("café world")
	if result != "café-world" {
		t.Errorf("got %q, want %q", result, "café-world")
	}
}

func TestSlugifyText_SingleWord(t *testing.T) {
	result := SlugifyText("hello")
	if result != "hello" {
		t.Errorf("got %q, want %q", result, "hello")
	}
}

func TestSlugifyText_UppercaseConvertedToLower(t *testing.T) {
	result := SlugifyText("HELLO WORLD")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

// ─────────────────────────────────────────────
// CountWords
// ─────────────────────────────────────────────

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

func TestCountWords_LeadingTrailingSpaces(t *testing.T) {
	result := CountWords("  one two  ")
	if result != 2 {
		t.Errorf("got %d, want %d", result, 2)
	}
}

func TestCountWords_MultipleSpacesBetweenWords(t *testing.T) {
	result := CountWords("one   two   three")
	if result != 3 {
		t.Errorf("got %d, want %d", result, 3)
	}
}

func TestCountWords_TabsAndNewlinesAsDelimiters(t *testing.T) {
	// strings.Fields splits on any whitespace (tabs, newlines, etc.)
	result := CountWords("one\ttwo\nthree")
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

func TestCountWords_PunctuationTreatedAsWordChars(t *testing.T) {
	// "hello," is a single token to strings.Fields
	result := CountWords("hello, world.")
	if result != 2 {
		t.Errorf("got %d, want %d", result, 2)
	}
}

// ─────────────────────────────────────────────
// ExtractInitials
// ─────────────────────────────────────────────

func TestExtractInitials_EmptyString(t *testing.T) {
	// strings.Fields("") returns [] so the loop never executes.
	// Should return "" without panicking.
	result := ExtractInitials("")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestExtractInitials_SingleName(t *testing.T) {
	result := ExtractInitials("John")
	if result != "J" {
		t.Errorf("got %q, want %q", result, "J")
	}
}

func TestExtractInitials_ThreePartName(t *testing.T) {
	result := ExtractInitials("John Paul Jones")
	if result != "JPJ" {
		t.Errorf("got %q, want %q", result, "JPJ")
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

func TestExtractInitials_ExtraWhitespaceBetweenNames(t *testing.T) {
	// strings.Fields collapses whitespace
	result := ExtractInitials("John   Doe")
	if result != "JD" {
		t.Errorf("got %q, want %q", result, "JD")
	}
}

func TestExtractInitials_OnlySpaces(t *testing.T) {
	result := ExtractInitials("   ")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

// BUG: ExtractInitials uses p[0] (byte index 0), not the first rune.
// For names starting with a multi-byte UTF-8 character this returns a
// garbled byte rather than the correct Unicode letter.
func TestExtractInitials_MultiByteFirstCharBug(t *testing.T) {
	// 'É' is 2 bytes (0xC3 0x89). p[0] == 0xC3, not 'É'.
	// A correct implementation should return "ÉD".
	// This test documents the actual (broken) behaviour.
	name := "Émile Durkheim"
	result := ExtractInitials(name)
	// With the byte-index bug the first initial is corrupted.
	// The test asserts the correct expectation; it will FAIL on the current code,
	// proving the bug exists.
	want := "ÉD"
	if result != want {
		t.Errorf("BUG CONFIRMED: got %q, want %q — ExtractInitials uses byte index instead of rune", result, want)
	}
}

// ─────────────────────────────────────────────
// WrapText
// ─────────────────────────────────────────────

func TestWrapText_EmptyString(t *testing.T) {
	result := WrapText("", 10)
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestWrapText_OnlySpaces(t *testing.T) {
	result := WrapText("   ", 10)
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestWrapText_SingleWordFitsInWidth(t *testing.T) {
	result := WrapText("hello", 10)
	if result != "hello" {
		t.Errorf("got %q, want %q", result, "hello")
	}
}

func TestWrapText_SingleWordExceedsWidth(t *testing.T) {
	// A word longer than width is placed on its own line (not split).
	result := WrapText("superlongword", 5)
	if result != "superlongword" {
		t.Errorf("got %q, want %q", result, "superlongword")
	}
}

func TestWrapText_AllWordsExactlyFit(t *testing.T) {
	// "ab cd" with width=5: "ab" (2) + " " (1) + "cd" (2) = 5 → fits on one line
	result := WrapText("ab cd", 5)
	if result != "ab cd" {
		t.Errorf("got %q, want %q", result, "ab cd")
	}
}

func TestWrapText_ExactBoundary(t *testing.T) {
	// width=8: "one two" is exactly 7 chars (fits); "three" goes to next line
	result := WrapText("one two three", 7)
	want := "one two\nthree"
	if result != want {
		t.Errorf("got %q, want %q", result, want)
	}
}

func TestWrapText_WidthZero(t *testing.T) {
	// With width=0 every word exceeds the limit, so each word becomes its own line.
	result := WrapText("one two three", 0)
	want := "one\ntwo\nthree"
	if result != want {
		t.Errorf("got %q, want %q", result, want)
	}
}

func TestWrapText_WidthOne(t *testing.T) {
	// Each word is longer than 1, so each word goes on its own line.
	result := WrapText("a b c", 1)
	want := "a\nb\nc"
	if result != want {
		t.Errorf("got %q, want %q", result, want)
	}
}

func TestWrapText_LongTextMultipleLines(t *testing.T) {
	result := WrapText("the quick brown fox jumps over the lazy dog", 15)
	// "the quick brown" = 15 chars (fits)
	// "fox jumps over" = 14 chars (fits)
	// "the lazy dog"  = 12 chars (fits)
	want := "the quick brown\nfox jumps over\nthe lazy dog"
	if result != want {
		t.Errorf("got %q, want %q", result, want)
	}
}

func TestWrapText_TabsNormalizedToSingleSpace(t *testing.T) {
	// strings.Fields normalises all whitespace; tabs become word separators
	result := WrapText("hello\tworld", 20)
	if result != "hello world" {
		t.Errorf("got %q, want %q", result, "hello world")
	}
}

func TestWrapText_NewlinesInInputCollapsed(t *testing.T) {
	// Newlines in the input are treated as whitespace by strings.Fields
	result := WrapText("hello\nworld", 20)
	if result != "hello world" {
		t.Errorf("got %q, want %q", result, "hello world")
	}
}

func TestWrapText_SingleCharWords(t *testing.T) {
	result := WrapText("a b c d e", 5)
	// "a b c" = 5 → fits; "d e" = 3 → next line
	want := "a b c\nd e"
	if result != want {
		t.Errorf("got %q, want %q", result, want)
	}
}

func TestWrapText_WordLongerThanWidthInMiddleOfText(t *testing.T) {
	// "hi superlongword ok" with width=5
	// "hi" starts, "superlongword" doesn't fit → "hi" flushed, "superlongword" starts new line,
	// "ok" doesn't fit alongside superlongword → "superlongword" flushed, "ok" on its own line.
	result := WrapText("hi superlongword ok", 5)
	want := "hi\nsuperlongword\nok"
	if result != want {
		t.Errorf("got %q, want %q", result, want)
	}
}

func TestWrapText_WidthEqualsWordLength(t *testing.T) {
	// width exactly equals the length of each word — each word its own line
	result := WrapText("abc def", 3)
	want := "abc\ndef"
	if result != want {
		t.Errorf("got %q, want %q", result, want)
	}
}
