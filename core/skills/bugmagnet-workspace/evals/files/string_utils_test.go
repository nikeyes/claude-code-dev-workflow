package stringutils

import "testing"

func TestTruncate(t *testing.T) {
	result := Truncate("Hello World", 5)
	if result != "Hello..." {
		t.Errorf("got %q, want %q", result, "Hello...")
	}
}

func TestSlugifyText(t *testing.T) {
	result := SlugifyText("Hello World")
	if result != "hello-world" {
		t.Errorf("got %q, want %q", result, "hello-world")
	}
}

func TestCountWords(t *testing.T) {
	result := CountWords("one two three")
	if result != 3 {
		t.Errorf("got %d, want %d", result, 3)
	}
}
