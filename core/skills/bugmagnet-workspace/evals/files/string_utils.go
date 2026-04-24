package stringutils

import (
	"strings"
	"unicode"
)

// Truncate shortens a string to maxLen characters, appending "..." if truncated.
func Truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen] + "..."
}

// SlugifyText converts text to a URL-friendly slug.
func SlugifyText(text string) string {
	text = strings.ToLower(text)
	var result []rune
	for _, r := range text {
		if unicode.IsLetter(r) || unicode.IsDigit(r) {
			result = append(result, r)
		} else if r == ' ' || r == '-' {
			result = append(result, '-')
		}
	}
	slug := string(result)
	for strings.Contains(slug, "--") {
		slug = strings.ReplaceAll(slug, "--", "-")
	}
	return strings.Trim(slug, "-")
}

// CountWords returns the number of words in text.
func CountWords(text string) int {
	return len(strings.Fields(text))
}

// ExtractInitials returns uppercase initials from a name.
func ExtractInitials(name string) string {
	parts := strings.Fields(name)
	var initials []rune
	for _, p := range parts {
		initials = append(initials, rune(p[0]))
	}
	return strings.ToUpper(string(initials))
}

// WrapText wraps text at the specified line width.
func WrapText(text string, width int) string {
	words := strings.Fields(text)
	if len(words) == 0 {
		return ""
	}
	var lines []string
	currentLine := words[0]
	for _, w := range words[1:] {
		if len(currentLine)+1+len(w) <= width {
			currentLine += " " + w
		} else {
			lines = append(lines, currentLine)
			currentLine = w
		}
	}
	lines = append(lines, currentLine)
	return strings.Join(lines, "\n")
}
