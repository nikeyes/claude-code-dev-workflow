package sortedset

import (
	"math"
	"testing"
)

// ---------------------------------------------------------------------------
// Insert edge cases
// ---------------------------------------------------------------------------

func TestInsert_NegativeValues(t *testing.T) {
	s := New()
	if !s.Insert(-1) {
		t.Fatal("expected Insert(-1) to return true")
	}
	if !s.Contains(-1) {
		t.Fatal("expected set to contain -1 after Insert")
	}
}

func TestInsert_Zero(t *testing.T) {
	s := New()
	if !s.Insert(0) {
		t.Fatal("expected Insert(0) to return true")
	}
	if !s.Contains(0) {
		t.Fatal("expected set to contain 0 after Insert")
	}
}

func TestInsert_MaintainsSortedOrder_OutOfOrderInserts(t *testing.T) {
	s := New()
	for _, v := range []int{5, 3, 7, 1, 9, 2, 8, 4, 6, 0} {
		s.Insert(v)
	}
	vals := s.Values()
	for i := 1; i < len(vals); i++ {
		if vals[i] <= vals[i-1] {
			t.Fatalf("values not sorted at index %d: %v", i, vals)
		}
	}
}

func TestInsert_DuplicateAfterRemove(t *testing.T) {
	s := New()
	s.Insert(10)
	s.Remove(10)
	if !s.Insert(10) {
		t.Fatal("expected Insert after Remove to return true")
	}
}

func TestInsert_MinInt(t *testing.T) {
	s := New()
	if !s.Insert(math.MinInt) {
		t.Fatal("expected Insert(MinInt) to return true")
	}
	if !s.Contains(math.MinInt) {
		t.Fatal("expected set to contain MinInt")
	}
}

func TestInsert_MaxInt(t *testing.T) {
	s := New()
	if !s.Insert(math.MaxInt) {
		t.Fatal("expected Insert(MaxInt) to return true")
	}
	if !s.Contains(math.MaxInt) {
		t.Fatal("expected set to contain MaxInt")
	}
}

func TestInsert_MinAndMaxInt_Together(t *testing.T) {
	s := New()
	s.Insert(math.MaxInt)
	s.Insert(math.MinInt)
	vals := s.Values()
	if len(vals) != 2 {
		t.Fatalf("expected 2 elements, got %d", len(vals))
	}
	if vals[0] != math.MinInt || vals[1] != math.MaxInt {
		t.Fatalf("expected [MinInt MaxInt], got %v", vals)
	}
}

// ---------------------------------------------------------------------------
// Remove edge cases
// ---------------------------------------------------------------------------

func TestRemove_FromEmptySet(t *testing.T) {
	s := New()
	if s.Remove(1) {
		t.Fatal("expected Remove from empty set to return false")
	}
}

func TestRemove_NonExistentValue(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(3)
	if s.Remove(2) {
		t.Fatal("expected Remove of absent value to return false")
	}
	if s.Len() != 2 {
		t.Fatalf("expected len 2 after failed Remove, got %d", s.Len())
	}
}

func TestRemove_OnlyElement(t *testing.T) {
	s := New()
	s.Insert(42)
	if !s.Remove(42) {
		t.Fatal("expected Remove of sole element to return true")
	}
	if s.Len() != 0 {
		t.Fatalf("expected len 0, got %d", s.Len())
	}
}

func TestRemove_FirstElement(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	if !s.Remove(1) {
		t.Fatal("expected Remove(1) to return true")
	}
	vals := s.Values()
	expected := []int{2, 3}
	if !slicesEqual(vals, expected) {
		t.Fatalf("expected %v, got %v", expected, vals)
	}
}

func TestRemove_LastElement(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	if !s.Remove(3) {
		t.Fatal("expected Remove(3) to return true")
	}
	vals := s.Values()
	expected := []int{1, 2}
	if !slicesEqual(vals, expected) {
		t.Fatalf("expected %v, got %v", expected, vals)
	}
}

func TestRemove_MiddleElement(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	if !s.Remove(2) {
		t.Fatal("expected Remove(2) to return true")
	}
	vals := s.Values()
	expected := []int{1, 3}
	if !slicesEqual(vals, expected) {
		t.Fatalf("expected %v, got %v", expected, vals)
	}
}

// TestRemove_DoesNotCorruptPreviousValuesSlice verifies that a Values() snapshot
// taken before a Remove is not silently modified by the remove operation.
// This tests a known Go slice-aliasing hazard in the append-based Remove.
func TestRemove_DoesNotCorruptPreviousValuesSlice(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	snapshot := s.Values()
	snapshotCopy := make([]int, len(snapshot))
	copy(snapshotCopy, snapshot)

	s.Remove(2)

	for i, v := range snapshot {
		if v != snapshotCopy[i] {
			t.Fatalf("Values() snapshot was mutated by Remove: index %d changed from %d to %d", i, snapshotCopy[i], v)
		}
	}
}

// ---------------------------------------------------------------------------
// Contains edge cases
// ---------------------------------------------------------------------------

func TestContains_EmptySet(t *testing.T) {
	s := New()
	if s.Contains(0) {
		t.Fatal("expected Contains on empty set to return false")
	}
}

func TestContains_NegativeValue(t *testing.T) {
	s := New()
	s.Insert(-5)
	if !s.Contains(-5) {
		t.Fatal("expected Contains(-5) to be true")
	}
	if s.Contains(-4) {
		t.Fatal("expected Contains(-4) to be false")
	}
}

func TestContains_AfterRemove(t *testing.T) {
	s := New()
	s.Insert(7)
	s.Remove(7)
	if s.Contains(7) {
		t.Fatal("expected Contains(7) to be false after Remove")
	}
}

// ---------------------------------------------------------------------------
// Rank edge cases
// ---------------------------------------------------------------------------

func TestRank_AbsentValue_ReturnsNegativeOne(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(3)
	if got := s.Rank(2); got != -1 {
		t.Fatalf("expected Rank of absent value to be -1, got %d", got)
	}
}

func TestRank_EmptySet(t *testing.T) {
	s := New()
	if got := s.Rank(0); got != -1 {
		t.Fatalf("expected Rank on empty set to be -1, got %d", got)
	}
}

func TestRank_FirstElement(t *testing.T) {
	s := New()
	s.Insert(10)
	s.Insert(20)
	s.Insert(30)
	if got := s.Rank(10); got != 0 {
		t.Fatalf("expected Rank(10) == 0, got %d", got)
	}
}

func TestRank_LastElement(t *testing.T) {
	s := New()
	s.Insert(10)
	s.Insert(20)
	s.Insert(30)
	if got := s.Rank(30); got != 2 {
		t.Fatalf("expected Rank(30) == 2, got %d", got)
	}
}

func TestRank_AfterRemove_ShiftsDown(t *testing.T) {
	s := New()
	s.Insert(10)
	s.Insert(20)
	s.Insert(30)
	// 20 has rank 1; after removing 10, 20 should have rank 0
	s.Remove(10)
	if got := s.Rank(20); got != 0 {
		t.Fatalf("expected Rank(20) == 0 after removing 10, got %d", got)
	}
}

func TestRank_NegativeValue(t *testing.T) {
	s := New()
	s.Insert(-10)
	s.Insert(0)
	s.Insert(10)
	if got := s.Rank(-10); got != 0 {
		t.Fatalf("expected Rank(-10) == 0, got %d", got)
	}
}

// ---------------------------------------------------------------------------
// Range edge cases
// ---------------------------------------------------------------------------

func TestRange_LowGreaterThanHigh_ReturnsNil(t *testing.T) {
	s := New()
	s.Insert(5)
	got := s.Range(10, 3)
	if got != nil {
		t.Fatalf("expected nil when low > high, got %v", got)
	}
}

func TestRange_EmptySet(t *testing.T) {
	s := New()
	got := s.Range(1, 10)
	if got != nil {
		t.Fatalf("expected nil on empty set, got %v", got)
	}
}

func TestRange_SingleValueRange_ValueExists(t *testing.T) {
	s := New()
	s.Insert(5)
	got := s.Range(5, 5)
	expected := []int{5}
	if !slicesEqual(got, expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
}

func TestRange_SingleValueRange_ValueAbsent(t *testing.T) {
	s := New()
	s.Insert(3)
	s.Insert(7)
	got := s.Range(5, 5)
	if got != nil {
		t.Fatalf("expected nil when single-value range has no match, got %v", got)
	}
}

func TestRange_BoundariesNotInSet(t *testing.T) {
	s := New()
	for _, v := range []int{2, 4, 6, 8} {
		s.Insert(v)
	}
	// Range(3, 7) — 3 and 7 not in set; should return 4, 6
	got := s.Range(3, 7)
	expected := []int{4, 6}
	if !slicesEqual(got, expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
}

func TestRange_AllElementsInRange(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3, 4, 5} {
		s.Insert(v)
	}
	got := s.Range(0, 10)
	expected := []int{1, 2, 3, 4, 5}
	if !slicesEqual(got, expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
}

func TestRange_NoElementsInRange(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	got := s.Range(10, 20)
	if got != nil {
		t.Fatalf("expected nil when no elements fall in range, got %v", got)
	}
}

func TestRange_NegativeValues(t *testing.T) {
	s := New()
	for _, v := range []int{-5, -3, -1, 0, 1} {
		s.Insert(v)
	}
	got := s.Range(-3, 0)
	expected := []int{-3, -1, 0}
	if !slicesEqual(got, expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
}

func TestRange_LowEqualsHigh_EqualLowBoundary(t *testing.T) {
	// low == high == smallest element in set
	s := New()
	s.Insert(1)
	s.Insert(2)
	got := s.Range(1, 1)
	expected := []int{1}
	if !slicesEqual(got, expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
}

func TestRange_LowEqualsHigh_EqualHighBoundary(t *testing.T) {
	// low == high == largest element in set
	s := New()
	s.Insert(1)
	s.Insert(2)
	got := s.Range(2, 2)
	expected := []int{2}
	if !slicesEqual(got, expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
}

func TestRange_DoesNotMutateInternalState(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	result := s.Range(1, 3)
	// Mutate the returned slice
	for i := range result {
		result[i] = 999
	}
	// The set itself must be unaffected
	vals := s.Values()
	expected := []int{1, 2, 3}
	if !slicesEqual(vals, expected) {
		t.Fatalf("mutating Range result corrupted set internal state: %v", vals)
	}
}

// ---------------------------------------------------------------------------
// Min / Max edge cases
// ---------------------------------------------------------------------------

func TestMin_EmptySet(t *testing.T) {
	s := New()
	val, ok := s.Min()
	if ok {
		t.Fatal("expected ok=false for Min on empty set")
	}
	if val != 0 {
		t.Fatalf("expected zero value 0, got %d", val)
	}
}

func TestMax_EmptySet(t *testing.T) {
	s := New()
	val, ok := s.Max()
	if ok {
		t.Fatal("expected ok=false for Max on empty set")
	}
	if val != 0 {
		t.Fatalf("expected zero value 0, got %d", val)
	}
}

func TestMin_SingleElement(t *testing.T) {
	s := New()
	s.Insert(42)
	val, ok := s.Min()
	if !ok {
		t.Fatal("expected ok=true for Min on single-element set")
	}
	if val != 42 {
		t.Fatalf("expected 42, got %d", val)
	}
}

func TestMax_SingleElement(t *testing.T) {
	s := New()
	s.Insert(42)
	val, ok := s.Max()
	if !ok {
		t.Fatal("expected ok=true for Max on single-element set")
	}
	if val != 42 {
		t.Fatalf("expected 42, got %d", val)
	}
}

func TestMin_NegativeValues(t *testing.T) {
	s := New()
	for _, v := range []int{-3, -1, 0, 2} {
		s.Insert(v)
	}
	val, ok := s.Min()
	if !ok || val != -3 {
		t.Fatalf("expected Min=-3, ok=true; got %d, %v", val, ok)
	}
}

func TestMax_NegativeValues(t *testing.T) {
	s := New()
	for _, v := range []int{-3, -1, 0, 2} {
		s.Insert(v)
	}
	val, ok := s.Max()
	if !ok || val != 2 {
		t.Fatalf("expected Max=2, ok=true; got %d, %v", val, ok)
	}
}

func TestMin_UpdatesAfterRemovingMinElement(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(2)
	s.Insert(3)
	s.Remove(1)
	val, ok := s.Min()
	if !ok || val != 2 {
		t.Fatalf("expected new Min=2 after removing 1, got %d ok=%v", val, ok)
	}
}

func TestMax_UpdatesAfterRemovingMaxElement(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(2)
	s.Insert(3)
	s.Remove(3)
	val, ok := s.Max()
	if !ok || val != 2 {
		t.Fatalf("expected new Max=2 after removing 3, got %d ok=%v", val, ok)
	}
}

// ---------------------------------------------------------------------------
// Values edge cases
// ---------------------------------------------------------------------------

func TestValues_EmptySet(t *testing.T) {
	s := New()
	vals := s.Values()
	if vals == nil {
		t.Fatal("expected Values() to return non-nil empty slice, got nil")
	}
	if len(vals) != 0 {
		t.Fatalf("expected empty slice, got %v", vals)
	}
}

// TestValues_IsolationFromInternalState verifies that mutating the returned
// slice does not corrupt the set's internal data.
func TestValues_IsolationFromInternalState(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(2)
	s.Insert(3)

	vals := s.Values()
	vals[0] = 999

	// Set internal state must be unchanged
	if s.Contains(999) {
		t.Fatal("mutating Values() result should not affect set contents")
	}
	if !s.Contains(1) {
		t.Fatal("set should still contain 1 after Values() mutation")
	}
}

// ---------------------------------------------------------------------------
// Len edge cases
// ---------------------------------------------------------------------------

func TestLen_EmptySet(t *testing.T) {
	s := New()
	if s.Len() != 0 {
		t.Fatalf("expected Len 0 for new set, got %d", s.Len())
	}
}

func TestLen_AfterInsertAndRemove(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(2)
	s.Insert(3)
	s.Remove(2)
	if s.Len() != 2 {
		t.Fatalf("expected Len 2, got %d", s.Len())
	}
}

func TestLen_DuplicateInsertDoesNotIncreaseLen(t *testing.T) {
	s := New()
	s.Insert(5)
	s.Insert(5)
	if s.Len() != 1 {
		t.Fatalf("expected Len 1 after duplicate Insert, got %d", s.Len())
	}
}

func TestLen_RemoveNonExistentDoesNotDecreaseLen(t *testing.T) {
	s := New()
	s.Insert(5)
	s.Remove(99)
	if s.Len() != 1 {
		t.Fatalf("expected Len 1 after failed Remove, got %d", s.Len())
	}
}

// ---------------------------------------------------------------------------
// Sorted ordering invariant
// ---------------------------------------------------------------------------

func TestSortedInvariant_AfterMixedOperations(t *testing.T) {
	s := New()
	ops := []int{50, 10, 90, 30, 70, 20, 80, 40, 60}
	for _, v := range ops {
		s.Insert(v)
	}
	s.Remove(30)
	s.Remove(70)
	s.Insert(35)

	vals := s.Values()
	for i := 1; i < len(vals); i++ {
		if vals[i] <= vals[i-1] {
			t.Fatalf("sorted invariant violated at index %d: %v", i, vals)
		}
	}
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

func slicesEqual(a, b []int) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}
