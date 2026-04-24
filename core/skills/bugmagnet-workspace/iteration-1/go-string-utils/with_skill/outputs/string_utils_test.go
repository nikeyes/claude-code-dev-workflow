package stringutils

import (
	"strings"
	"testing"
)

// =============================================================================
// Truncate tests
// =============================================================================

func TestTruncate_returnsOriginalStringWhenShorterThanMaxLen(t *testing.T) {
	result := Truncate("Hi", 10)
	if result != "Hi" {
		t.Errorf("got %q, want %q", result, "Hi")
	}
}

func TestTruncate_returnsOriginalStringWhenExactlyMaxLen(t *testing.T) {
	result := Truncate("Hello", 5)
	if result != "Hello" {
		t.Errorf("got %q, want %q", result, "Hello")
	}
}

func TestTruncate_appendsEllipsisWhenLongerThanMaxLen(t *testing.T) {
	result := Truncate("Hello World", 5)
	if result != "Hello..." {
		t.Errorf("got %q, want %q", result, "Hello...")
	}
}

func TestTruncate_returnsEmptyStringWhenInputIsEmpty(t *testing.T) {
	result := Truncate("", 5)
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestTruncate_returnsEmptyStringWhenInputIsEmptyAndMaxLenIsZero(t *testing.T) {
	result := Truncate("", 0)
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestTruncate_returnsEllipsisWhenMaxLenIsZeroAndStringIsNonEmpty(t *testing.T) {
	result := Truncate("Hi", 0)
	if result != "..." {
		t.Errorf("got %q, want %q", result, "...")
	}
}

func TestTruncate_truncatesSingleCharacterString(t *testing.T) {
	result := Truncate("A", 0)
	if result != "..." {
		t.Errorf("got %q, want %q", result, "...")
	}
}

func TestTruncate_handlesMaxLenOfOne(t *testing.T) {
	result := Truncate("Hello", 1)
	if result != "H..." {
		t.Errorf("got %q, want %q", result, "H...")
	}
}

func TestTruncate_handlesVeryLongString(t *testing.T) {
	long := strings.Repeat("x", 10000)
	result := Truncate(long, 5)
	if result != "xxxxx..." {
		t.Errorf("got length %d, want %q", len(result), "xxxxx...")
	}
}

func TestTruncate_handlesStringWithWhitespace(t *testing.T) {
	result := Truncate("  spaces  ", 3)
	if result != "  s..." {
		t.Errorf("got %q, want %q", result, "  s...")
	}
}

// BUG: Truncate uses byte-length (len) instead of rune count.
// For multibyte UTF-8 characters, s[:maxLen] can split a rune in the middle,
// producing invalid UTF-8 output.
//
// ROOT CAUSE: Line 10 uses len(s) (byte length) and line 13 uses s[:maxLen]
// (byte slice). For ASCII this is fine; for multibyte Unicode it is wrong.
//
// CODE LOCATION: string_utils.go:10 and string_utils.go:13
//
// CURRENT CODE:
//   if len(s) <= maxLen {
//       return s
//   }
//   return s[:maxLen] + "..."
//
// PROPOSED FIX:
//   runes := []rune(s)
//   if len(runes) <= maxLen {
//       return s
//   }
//   return string(runes[:maxLen]) + "..."
//
// EXPECTED: Truncate("héllo", 3) == "hél..."
// ACTUAL:   Truncate("héllo", 3) produces s[:3] which splits the 2-byte é at offset 2,
//           yielding invalid UTF-8 bytes + "..."
func TestTruncate_returnsCorrectResultForMultibyteUnicodeCharacters_BUG(t *testing.T) {
	t.Skip("BUG: Truncate uses byte indexing instead of rune indexing for UTF-8 strings")
	// "héllo" in UTF-8: h=1 byte, é=2 bytes, l=1, l=1, o=1 → total 6 bytes
	// maxLen=3 means "keep 3 characters": h, é, l → "hél..."
	result := Truncate("héllo", 3)
	if result != "hél..." {
		t.Errorf("got %q, want %q", result, "hél...")
	}
}

func TestTruncate_returnsOriginalForMultibyteStringWithinLimit_BUG(t *testing.T) {
	t.Skip("BUG: Truncate uses len() (byte length) not rune count for the length check")
	// "héllo" has 5 runes but 6 bytes. maxLen=5 should return the full string.
	result := Truncate("héllo", 5)
	if result != "héllo" {
		t.Errorf("got %q, want %q", result, "héllo")
	}
}

// =============================================================================
// SlugifyText tests
// =============================================================================

func TestSlugifyText_convertsSpacesToHyphens(t *testing.T) {
	result := SlugifyText("Hello World")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_lowercasesInput(t *testing.T) {
	result := SlugifyText("HELLO WORLD")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_returnsEmptyStringForEmptyInput(t *testing.T) {
	result := SlugifyText("")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestSlugifyText_returnsEmptyStringForWhitespaceOnlyInput(t *testing.T) {
	result := SlugifyText("   ")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestSlugifyText_stripsLeadingAndTrailingHyphens(t *testing.T) {
	result := SlugifyText(" hello world ")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_collapsesMultipleConsecutiveSpaces(t *testing.T) {
	result := SlugifyText("hello  world")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_preservesExistingHyphens(t *testing.T) {
	result := SlugifyText("already-slugified")
	if result != "already-slugified" {
		t.Errorf("got %q, want %q", result, "already-slugified")
	}
}

func TestSlugifyText_collapsesMultipleConsecutiveHyphens(t *testing.T) {
	result := SlugifyText("hello---world")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_stripsSpecialCharacters(t *testing.T) {
	result := SlugifyText("Hello, World!")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_handlesNumbersInText(t *testing.T) {
	result := SlugifyText("post 42 title")
	if result != "post-42-title" {
		t.Errorf("got %q, want %q", result, "post-42-title")
	}
}

func TestSlugifyText_handlesSingleWord(t *testing.T) {
	result := SlugifyText("hello")
	if result != "hello" {
		t.Errorf("got %q, want %q", result, "hello")
	}
}

func TestSlugifyText_handlesSingleCharacter(t *testing.T) {
	result := SlugifyText("a")
	if result != "a" {
		t.Errorf("got %q, want %q", result, "a")
	}
}

func TestSlugifyText_handlesTabsAndNewlines(t *testing.T) {
	// Tabs and newlines are not spaces or hyphens, so they get dropped
	// "hello\tworld" → after toLower: "hello\tworld", tab is not letter/digit/space/hyphen → dropped → "helloworld"
	result := SlugifyText("hello\tworld")
	if result != "helloworld" {
		t.Errorf("got %q, want %q", result, "helloworld")
	}
}

func TestSlugifyText_handlesVeryLongString(t *testing.T) {
	long := strings.Repeat("a", 10000)
	result := SlugifyText(long)
	if len(result) != 10000 {
		t.Errorf("got length %d, want 10000", len(result))
	}
}

// The underscore character is silently dropped, potentially merging surrounding words.
// This may be surprising to users who expect underscore to act as a word separator.
func TestSlugifyText_dropsUnderscoresWithoutSeparating(t *testing.T) {
	result := SlugifyText("hello_world")
	// Underscore is not a letter, digit, space, or hyphen, so it is dropped.
	// "hello_world" → "helloworld" (words merged, no hyphen separator)
	if result != "helloworld" {
		t.Errorf("got %q, want %q", result, "helloworld")
	}
}

func TestSlugifyText_handlesApostropheInWord(t *testing.T) {
	// Apostrophe is not letter/digit/space/hyphen, so it is dropped
	result := SlugifyText("it's a test")
	if result != "its-a-test" {
		t.Errorf("got %q, want %q", result, "its-a-test")
	}
}

func TestSlugifyText_handlesAllPunctuation(t *testing.T) {
	result := SlugifyText("!@#$%^&*()")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestSlugifyText_handlesUnicodeLetters(t *testing.T) {
	// unicode.IsLetter returns true for accented letters, so they are kept
	result := SlugifyText("café")
	if result != "café" {
		t.Errorf("got %q, want %q", result, "café")
	}
}

func TestSlugifyText_handlesHyphenAtStartAndEnd(t *testing.T) {
	result := SlugifyText("-hello-world-")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

// =============================================================================
// CountWords tests
// =============================================================================

func TestCountWords_returnsCorrectCountForNormalSentence(t *testing.T) {
	result := CountWords("one two three")
	if result != 3 {
		t.Errorf("got %d, want %d", result, 3)
	}
}

func TestCountWords_returnsZeroForEmptyString(t *testing.T) {
	result := CountWords("")
	if result != 0 {
		t.Errorf("got %d, want %d", result, 0)
	}
}

func TestCountWords_returnsZeroForWhitespaceOnlyString(t *testing.T) {
	result := CountWords("   ")
	if result != 0 {
		t.Errorf("got %d, want %d", result, 0)
	}
}

func TestCountWords_returnsOneForSingleWord(t *testing.T) {
	result := CountWords("hello")
	if result != 1 {
		t.Errorf("got %d, want %d", result, 1)
	}
}

func TestCountWords_returnsOneForSingleCharacter(t *testing.T) {
	result := CountWords("a")
	if result != 1 {
		t.Errorf("got %d, want %d", result, 1)
	}
}

func TestCountWords_handlesLeadingAndTrailingSpaces(t *testing.T) {
	result := CountWords("  hello world  ")
	if result != 2 {
		t.Errorf("got %d, want %d", result, 2)
	}
}

func TestCountWords_handlesMultipleSpacesBetweenWords(t *testing.T) {
	result := CountWords("hello   world")
	if result != 2 {
		t.Errorf("got %d, want %d", result, 2)
	}
}

func TestCountWords_handlesTabsAndNewlines(t *testing.T) {
	result := CountWords("hello\tworld\none")
	if result != 3 {
		t.Errorf("got %d, want %d", result, 3)
	}
}

func TestCountWords_handlesVeryLongText(t *testing.T) {
	words := strings.Repeat("word ", 1000)
	result := CountWords(strings.TrimRight(words, " "))
	if result != 1000 {
		t.Errorf("got %d, want %d", result, 1000)
	}
}

func TestCountWords_countsPunctuationAsPartOfWord(t *testing.T) {
	// strings.Fields splits on whitespace; "hello," is one token
	result := CountWords("hello, world.")
	if result != 2 {
		t.Errorf("got %d, want %d", result, 2)
	}
}

// =============================================================================
// ExtractInitials tests
// =============================================================================

func TestExtractInitials_returnsUppercaseInitialsForFullName(t *testing.T) {
	result := ExtractInitials("John Doe")
	if result != "JD" {
		t.Errorf("got %q, want %q", result, "JD")
	}
}

func TestExtractInitials_returnsEmptyStringForEmptyInput(t *testing.T) {
	result := ExtractInitials("")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestExtractInitials_returnsEmptyStringForWhitespaceOnlyInput(t *testing.T) {
	result := ExtractInitials("   ")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestExtractInitials_returnsSingleInitialForSingleName(t *testing.T) {
	result := ExtractInitials("Alice")
	if result != "A" {
		t.Errorf("got %q, want %q", result, "A")
	}
}

func TestExtractInitials_uppercasesLowercaseInitials(t *testing.T) {
	result := ExtractInitials("john doe")
	if result != "JD" {
		t.Errorf("got %q, want %q", result, "JD")
	}
}

func TestExtractInitials_handlesThreePartName(t *testing.T) {
	result := ExtractInitials("Mary Jane Watson")
	if result != "MJW" {
		t.Errorf("got %q, want %q", result, "MJW")
	}
}

func TestExtractInitials_handlesMultipleSpacesBetweenNameParts(t *testing.T) {
	result := ExtractInitials("John   Doe")
	if result != "JD" {
		t.Errorf("got %q, want %q", result, "JD")
	}
}

func TestExtractInitials_handlesLeadingAndTrailingSpaces(t *testing.T) {
	result := ExtractInitials("  John Doe  ")
	if result != "JD" {
		t.Errorf("got %q, want %q", result, "JD")
	}
}

func TestExtractInitials_handlesSingleCharacterName(t *testing.T) {
	result := ExtractInitials("A B")
	if result != "AB" {
		t.Errorf("got %q, want %q", result, "AB")
	}
}

// BUG: ExtractInitials uses p[0] (byte index) instead of []rune(p)[0] for the
// first character of each name part. For names with multibyte UTF-8 first
// characters (e.g. accented letters, non-Latin scripts), p[0] returns the
// first byte of the multibyte sequence, not the actual character. This produces
// incorrect or garbled output.
//
// ROOT CAUSE: string_utils.go:44 — `rune(p[0])` takes a byte value and casts
// it to rune. For ASCII characters this is equivalent to the first rune, but
// for multibyte UTF-8 (any code point > 127) this is wrong.
//
// CODE LOCATION: string_utils.go:44
//
// CURRENT CODE:
//   initials = append(initials, rune(p[0]))
//
// PROPOSED FIX:
//   runes := []rune(p)
//   initials = append(initials, runes[0])
//
// EXPECTED: ExtractInitials("Åsa Björk") == "ÅB"
// ACTUAL:   ExtractInitials("Åsa Björk") produces garbled bytes from the
//           multibyte UTF-8 sequences for Å and B.
func TestExtractInitials_returnsCorrectInitialsForAccentedFirstCharacters_BUG(t *testing.T) {
	t.Skip("BUG: ExtractInitials uses p[0] (byte) instead of []rune(p)[0] for multibyte UTF-8 names")
	result := ExtractInitials("Åsa Björk")
	if result != "ÅB" {
		t.Errorf("got %q, want %q", result, "ÅB")
	}
}

func TestExtractInitials_returnsCorrectInitialsForChineseCharacters_BUG(t *testing.T) {
	t.Skip("BUG: ExtractInitials uses p[0] (byte) instead of []rune(p)[0]; Chinese characters are 3-byte UTF-8")
	// "李 明" — two Chinese characters as separate name parts
	result := ExtractInitials("李 明")
	if result != "李明" {
		t.Errorf("got %q, want %q", result, "李明")
	}
}

// =============================================================================
// WrapText tests
// =============================================================================

func TestWrapText_returnsEmptyStringForEmptyInput(t *testing.T) {
	result := WrapText("", 10)
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestWrapText_returnsEmptyStringForWhitespaceOnlyInput(t *testing.T) {
	result := WrapText("   ", 10)
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

func TestWrapText_returnsSingleWordUnchangedWhenWithinWidth(t *testing.T) {
	result := WrapText("hello", 10)
	if result != "hello" {
		t.Errorf("got %q, want %q", result, "hello")
	}
}

func TestWrapText_joinsTwoWordsOnSameLineWhenTheyFit(t *testing.T) {
	result := WrapText("hi there", 10)
	if result != "hi there" {
		t.Errorf("got %q, want %q", result, "hi there")
	}
}

func TestWrapText_wrapsToNewLineWhenWordExceedsWidth(t *testing.T) {
	result := WrapText("hello world", 7)
	if result != "hello\nworld" {
		t.Errorf("got %q, want %q", result, "hello\nworld")
	}
}

func TestWrapText_wrapsAtExactWidthBoundary(t *testing.T) {
	// "hello" is 5 chars; " world" would make it 11, exceeding width=10
	result := WrapText("hello world", 10)
	if result != "hello\nworld" {
		t.Errorf("got %q, want %q", result, "hello\nworld")
	}
}

func TestWrapText_fitsExactlyAtWidth(t *testing.T) {
	// "hello" (5) + " " (1) + "world" (5) = 11 = width=11 → fits on one line
	result := WrapText("hello world", 11)
	if result != "hello world" {
		t.Errorf("got %q, want %q", result, "hello world")
	}
}

func TestWrapText_wrapsMultipleLines(t *testing.T) {
	result := WrapText("one two three four five", 9)
	// "one two" = 7, then "three" = 5 (7+1+5=13 > 9), wrap
	// "three" = 5, "four" (5+1+4=10 > 9), wrap
	// "four" = 4, "five" (4+1+4=9 == 9), fits
	expected := "one two\nthree\nfour five"
	if result != expected {
		t.Errorf("got %q, want %q", result, expected)
	}
}

func TestWrapText_putsSingleWordOnItsOwnLineWhenLongerThanWidth(t *testing.T) {
	// A single word longer than width cannot be broken; it stays on its own line
	result := WrapText("superlongword", 5)
	if result != "superlongword" {
		t.Errorf("got %q, want %q", result, "superlongword")
	}
}

func TestWrapText_handlesSingleWordExactlyAtWidth(t *testing.T) {
	result := WrapText("hello", 5)
	if result != "hello" {
		t.Errorf("got %q, want %q", result, "hello")
	}
}

func TestWrapText_handlesLeadingAndTrailingSpacesInInput(t *testing.T) {
	// strings.Fields strips leading/trailing whitespace
	result := WrapText("  hello world  ", 20)
	if result != "hello world" {
		t.Errorf("got %q, want %q", result, "hello world")
	}
}

func TestWrapText_handlesVeryNarrowWidth(t *testing.T) {
	// width=1: every word that is longer than 1 char goes on its own line
	result := WrapText("a b c", 1)
	if result != "a\nb\nc" {
		t.Errorf("got %q, want %q", result, "a\nb\nc")
	}
}

func TestWrapText_handlesVeryWideWidth(t *testing.T) {
	result := WrapText("hello world how are you", 1000)
	if result != "hello world how are you" {
		t.Errorf("got %q, want %q", result, "hello world how are you")
	}
}

func TestWrapText_handlesWidthOfZero(t *testing.T) {
	// With width=0, no word fits (len(currentLine)+1+len(w) is always > 0),
	// so every word after the first goes on its own line.
	result := WrapText("one two three", 0)
	if result != "one\ntwo\nthree" {
		t.Errorf("got %q, want %q", result, "one\ntwo\nthree")
	}
}

func TestWrapText_handlesManyWords(t *testing.T) {
	// 100 single-character words at width=3: "a b" fits (3), "a b c" would be 5, so wrap after 2
	words := strings.Repeat("a ", 100)
	result := WrapText(strings.TrimRight(words, " "), 3)
	lines := strings.Split(result, "\n")
	for _, line := range lines {
		if len(line) > 3 {
			t.Errorf("line %q exceeds width 3", line)
		}
	}
}

// =============================================================================
// Bugmagnet session 2026-04-25 — advanced edge cases
// =============================================================================

// --- Truncate: boundary arithmetic ---

func TestTruncate_resultCanBeLongerThanMaxLenDueToEllipsis(t *testing.T) {
	// The function guarantees the prefix is maxLen chars, but appends "..."
	// so the total result length is maxLen+3, not maxLen.
	result := Truncate("Hello World", 5)
	// Prefix "Hello" (5 chars) + "..." (3 chars) = 8 chars total
	if len(result) != 8 {
		t.Errorf("got length %d, want 8", len(result))
	}
}

func TestTruncate_handlesNegativeMaxLen(t *testing.T) {
	// len(s) is always >= 0, so len(s) <= -1 is always false for non-empty strings.
	// This means any non-empty string with a negative maxLen will try s[:-1] which panics.
	// For empty string, len("") = 0 <= -1 is false, so it returns s[:−1] which also panics.
	// Actually: the function will try s[:-1] which panics with "index out of range".
	// This test documents that negative maxLen causes a panic.
	defer func() {
		if r := recover(); r == nil {
			t.Error("expected panic for negative maxLen but did not get one")
		}
	}()
	Truncate("hello", -1)
}

// --- SlugifyText: consecutive separator characters ---

func TestSlugifyText_mixedHyphensAndSpacesCollapsedCorrectly(t *testing.T) {
	result := SlugifyText("hello - world")
	// "hello - world" → toLower: "hello - world"
	// ' ' → '-', '-' → '-', ' ' → '-' → result runes: h,e,l,l,o,-,-,-,w,o,r,l,d
	// slug = "hello---world" → collapsed to "hello-world"
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestSlugifyText_tabCharacterIsDroppedNotTreatedAsSeparator(t *testing.T) {
	// Tab (\t) is not a space, hyphen, letter, or digit → dropped silently
	result := SlugifyText("hello\tworld")
	if result != "helloworld" {
		t.Errorf("got %q, want %q", result, "helloworld")
	}
}

func TestSlugifyText_onlyHyphensAfterStrippingReturnsEmpty(t *testing.T) {
	result := SlugifyText("---")
	if result != "" {
		t.Errorf("got %q, want %q", result, "")
	}
}

// --- ExtractInitials: name variants ---

func TestExtractInitials_handlesNameWithHyphen(t *testing.T) {
	// strings.Fields splits only on whitespace; "Mary-Jane" is one token
	// p[0] = 'M', so initial is 'M'
	result := ExtractInitials("Mary-Jane Watson")
	if result != "MW" {
		t.Errorf("got %q, want %q", result, "MW")
	}
}

func TestExtractInitials_preservesAlreadyUppercaseInitials(t *testing.T) {
	result := ExtractInitials("JOHN DOE")
	if result != "JD" {
		t.Errorf("got %q, want %q", result, "JD")
	}
}

func TestExtractInitials_handlesVeryLongName(t *testing.T) {
	// A name part of 35+ characters
	result := ExtractInitials("Wolfeschlegelsteinhausenbergerdorff Jr")
	if result != "WJ" {
		t.Errorf("got %q, want %q", result, "WJ")
	}
}

func TestExtractInitials_handlesNameWithNumbersInPart(t *testing.T) {
	// "James 3rd" — "3rd" starts with '3', which is a valid byte/rune
	result := ExtractInitials("James 3rd")
	if result != "J3" {
		t.Errorf("got %q, want %q", result, "J3")
	}
}

// --- WrapText: newlines in input ---

func TestWrapText_treatsNewlinesAsWordSeparators(t *testing.T) {
	// strings.Fields splits on any whitespace including newlines
	result := WrapText("hello\nworld", 20)
	if result != "hello world" {
		t.Errorf("got %q, want %q", result, "hello world")
	}
}

func TestWrapText_handlesTwoWordsThatFitExactly(t *testing.T) {
	// "ab cd" = 5 chars; width=5 → "ab" (2) + " " + "cd" (2) = 5 ≤ 5 → fits
	result := WrapText("ab cd", 5)
	if result != "ab cd" {
		t.Errorf("got %q, want %q", result, "ab cd")
	}
}

func TestWrapText_handlesTwoWordsThatExceedByOne(t *testing.T) {
	// "ab cd" at width=4: 2+1+2=5 > 4 → wrap
	result := WrapText("ab cd", 4)
	if result != "ab\ncd" {
		t.Errorf("got %q, want %q", result, "ab\ncd")
	}
}
