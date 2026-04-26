package sortedset

import "testing"

func TestInsert(t *testing.T) {
	s := New()
	if !s.Insert(5) {
		t.Fatal("expected first insert to return true")
	}
	if s.Insert(5) {
		t.Fatal("expected duplicate insert to return false")
	}
	if s.Len() != 1 {
		t.Fatalf("expected len 1, got %d", s.Len())
	}
}

func TestContains(t *testing.T) {
	s := New()
	s.Insert(3)
	if !s.Contains(3) {
		t.Fatal("expected Contains(3) to be true")
	}
	if s.Contains(4) {
		t.Fatal("expected Contains(4) to be false")
	}
}

func TestRange(t *testing.T) {
	s := New()
	for _, v := range []int{1, 3, 5, 7, 9} {
		s.Insert(v)
	}
	got := s.Range(3, 7)
	expected := []int{3, 5, 7}
	if len(got) != len(expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
	for i := range got {
		if got[i] != expected[i] {
			t.Fatalf("expected %v, got %v", expected, got)
		}
	}
}
