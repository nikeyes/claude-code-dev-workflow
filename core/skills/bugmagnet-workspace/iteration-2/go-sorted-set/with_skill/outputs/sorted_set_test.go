package sortedset

import (
	"math"
	"testing"
)

// ---- Original tests (preserved) ----

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

// ---- Phase 3: Gap Coverage Tests ----

// --- Remove ---

func TestRemove_returnsTrueWhenElementExists(t *testing.T) {
	s := New()
	s.Insert(10)

	removed := s.Remove(10)

	if !removed {
		t.Fatal("expected Remove(10) to return true when element exists")
	}
}

func TestRemove_returnsFalseWhenElementAbsent(t *testing.T) {
	s := New()

	removed := s.Remove(99)

	if removed {
		t.Fatal("expected Remove(99) to return false when element is not present")
	}
}

func TestRemove_decreasesLenByOne(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(2)
	s.Insert(3)

	s.Remove(2)

	if s.Len() != 2 {
		t.Fatalf("expected Len 2 after removing one element, got %d", s.Len())
	}
}

func TestRemove_elementNoLongerFoundAfterRemoval(t *testing.T) {
	s := New()
	s.Insert(7)

	s.Remove(7)

	if s.Contains(7) {
		t.Fatal("expected Contains(7) to be false after Remove(7)")
	}
}

func TestRemove_maintainsSortedOrderAfterRemoval(t *testing.T) {
	s := New()
	for _, v := range []int{5, 3, 1, 4, 2} {
		s.Insert(v)
	}

	s.Remove(3)

	got := s.Values()
	expected := []int{1, 2, 4, 5}
	if len(got) != len(expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
	for i := range got {
		if got[i] != expected[i] {
			t.Fatalf("expected %v, got %v", expected, got)
		}
	}
}

func TestRemove_allowsReinsertionAfterRemoval(t *testing.T) {
	s := New()
	s.Insert(42)
	s.Remove(42)

	inserted := s.Insert(42)

	if !inserted {
		t.Fatal("expected Insert(42) to return true after removing it first")
	}
	if !s.Contains(42) {
		t.Fatal("expected Contains(42) to be true after reinsertion")
	}
}

// --- Rank ---

func TestRank_returnsZeroBasedIndexOfElement(t *testing.T) {
	s := New()
	s.Insert(10)
	s.Insert(20)
	s.Insert(30)

	if s.Rank(10) != 0 {
		t.Fatalf("expected Rank(10) = 0, got %d", s.Rank(10))
	}
	if s.Rank(20) != 1 {
		t.Fatalf("expected Rank(20) = 1, got %d", s.Rank(20))
	}
	if s.Rank(30) != 2 {
		t.Fatalf("expected Rank(30) = 2, got %d", s.Rank(30))
	}
}

func TestRank_returnsNegativeOneWhenElementAbsent(t *testing.T) {
	s := New()
	s.Insert(5)

	rank := s.Rank(99)

	if rank != -1 {
		t.Fatalf("expected Rank(99) = -1 for absent element, got %d", rank)
	}
}

func TestRank_returnsNegativeOneOnEmptySet(t *testing.T) {
	s := New()

	rank := s.Rank(0)

	if rank != -1 {
		t.Fatalf("expected Rank(0) = -1 on empty set, got %d", rank)
	}
}

func TestRank_updatesAfterInsertion(t *testing.T) {
	s := New()
	s.Insert(20)
	s.Insert(30)

	// Insert a smaller value, shifting ranks
	s.Insert(10)

	if s.Rank(10) != 0 {
		t.Fatalf("expected Rank(10) = 0 after inserting smaller value, got %d", s.Rank(10))
	}
	if s.Rank(20) != 1 {
		t.Fatalf("expected Rank(20) = 1 after inserting smaller value, got %d", s.Rank(20))
	}
	if s.Rank(30) != 2 {
		t.Fatalf("expected Rank(30) = 2 after inserting smaller value, got %d", s.Rank(30))
	}
}

func TestRank_updatesAfterRemoval(t *testing.T) {
	s := New()
	s.Insert(10)
	s.Insert(20)
	s.Insert(30)

	s.Remove(10)

	if s.Rank(20) != 0 {
		t.Fatalf("expected Rank(20) = 0 after removing 10, got %d", s.Rank(20))
	}
	if s.Rank(30) != 1 {
		t.Fatalf("expected Rank(30) = 1 after removing 10, got %d", s.Rank(30))
	}
}

// --- Min / Max ---

func TestMin_returnsFalseOnEmptySet(t *testing.T) {
	s := New()

	_, ok := s.Min()

	if ok {
		t.Fatal("expected Min to return ok=false on empty set")
	}
}

func TestMax_returnsFalseOnEmptySet(t *testing.T) {
	s := New()

	_, ok := s.Max()

	if ok {
		t.Fatal("expected Max to return ok=false on empty set")
	}
}

func TestMin_returnsSmallestElement(t *testing.T) {
	s := New()
	for _, v := range []int{5, 3, 8, 1, 6} {
		s.Insert(v)
	}

	min, ok := s.Min()

	if !ok {
		t.Fatal("expected Min to return ok=true for non-empty set")
	}
	if min != 1 {
		t.Fatalf("expected Min = 1, got %d", min)
	}
}

func TestMax_returnsLargestElement(t *testing.T) {
	s := New()
	for _, v := range []int{5, 3, 8, 1, 6} {
		s.Insert(v)
	}

	max, ok := s.Max()

	if !ok {
		t.Fatal("expected Max to return ok=true for non-empty set")
	}
	if max != 8 {
		t.Fatalf("expected Max = 8, got %d", max)
	}
}

func TestMin_returnsSingleElementWhenSetHasOneElement(t *testing.T) {
	s := New()
	s.Insert(42)

	min, ok := s.Min()

	if !ok {
		t.Fatal("expected Min to return ok=true")
	}
	if min != 42 {
		t.Fatalf("expected Min = 42, got %d", min)
	}
}

func TestMax_returnsSingleElementWhenSetHasOneElement(t *testing.T) {
	s := New()
	s.Insert(42)

	max, ok := s.Max()

	if !ok {
		t.Fatal("expected Max to return ok=true")
	}
	if max != 42 {
		t.Fatalf("expected Max = 42, got %d", max)
	}
}

func TestMin_updatesWhenMinimumIsRemoved(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(2)
	s.Insert(3)

	s.Remove(1)
	min, ok := s.Min()

	if !ok {
		t.Fatal("expected Min to return ok=true after partial removal")
	}
	if min != 2 {
		t.Fatalf("expected Min = 2 after removing 1, got %d", min)
	}
}

func TestMax_updatesWhenMaximumIsRemoved(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(2)
	s.Insert(3)

	s.Remove(3)
	max, ok := s.Max()

	if !ok {
		t.Fatal("expected Max to return ok=true after partial removal")
	}
	if max != 2 {
		t.Fatalf("expected Max = 2 after removing 3, got %d", max)
	}
}

// --- Values ---

func TestValues_returnsEmptySliceOnEmptySet(t *testing.T) {
	s := New()

	got := s.Values()

	if len(got) != 0 {
		t.Fatalf("expected empty slice from Values on empty set, got %v", got)
	}
}

func TestValues_returnsSortedElements(t *testing.T) {
	s := New()
	for _, v := range []int{5, 3, 8, 1, 6} {
		s.Insert(v)
	}

	got := s.Values()
	expected := []int{1, 3, 5, 6, 8}

	if len(got) != len(expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
	for i := range got {
		if got[i] != expected[i] {
			t.Fatalf("expected %v, got %v", expected, got)
		}
	}
}

func TestValues_returnsACopyNotAReference(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(2)
	s.Insert(3)

	got := s.Values()
	got[0] = 999 // mutate the returned slice

	// Internal state should be unchanged
	if s.Contains(999) {
		t.Fatal("expected mutation of Values() result not to affect internal set state")
	}
	if !s.Contains(1) {
		t.Fatal("expected original element 1 to still be present after mutating Values() result")
	}
}

// --- Contains on empty set ---

func TestContains_returnsFalseOnEmptySet(t *testing.T) {
	s := New()

	if s.Contains(0) {
		t.Fatal("expected Contains(0) to be false on empty set")
	}
}

// --- Len ---

func TestLen_returnsZeroOnNewSet(t *testing.T) {
	s := New()

	if s.Len() != 0 {
		t.Fatalf("expected Len = 0 on new set, got %d", s.Len())
	}
}

func TestLen_incrementsWithEachUniqueInsert(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(2)
	s.Insert(3)

	if s.Len() != 3 {
		t.Fatalf("expected Len = 3, got %d", s.Len())
	}
}

func TestLen_doesNotIncrementOnDuplicateInsert(t *testing.T) {
	s := New()
	s.Insert(5)
	s.Insert(5)

	if s.Len() != 1 {
		t.Fatalf("expected Len = 1 after duplicate insert, got %d", s.Len())
	}
}

// --- Insert maintains sorted order ---

func TestInsert_maintainsSortedOrderWithOutOfOrderInsertions(t *testing.T) {
	s := New()
	for _, v := range []int{9, 1, 5, 3, 7} {
		s.Insert(v)
	}

	got := s.Values()
	expected := []int{1, 3, 5, 7, 9}

	if len(got) != len(expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
	for i := range got {
		if got[i] != expected[i] {
			t.Fatalf("expected %v, got %v", expected, got)
		}
	}
}

// --- Range edge cases ---

func TestRange_returnsNilOnEmptySet(t *testing.T) {
	s := New()

	got := s.Range(1, 10)

	if got != nil {
		t.Fatalf("expected nil from Range on empty set, got %v", got)
	}
}

func TestRange_returnsNilWhenLowGreaterThanHigh(t *testing.T) {
	s := New()
	s.Insert(5)

	got := s.Range(10, 1)

	if got != nil {
		t.Fatalf("expected nil when low > high, got %v", got)
	}
}

func TestRange_returnsNilWhenNoElementsInRange(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}

	got := s.Range(10, 20)

	if got != nil {
		t.Fatalf("expected nil when no elements in range [10,20], got %v", got)
	}
}

func TestRange_includesBoundaryValues(t *testing.T) {
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

func TestRange_returnsSingleElementWhenLowEqualsHigh(t *testing.T) {
	s := New()
	for _, v := range []int{1, 5, 10} {
		s.Insert(v)
	}

	got := s.Range(5, 5)
	expected := []int{5}

	if len(got) != 1 || got[0] != 5 {
		t.Fatalf("expected %v, got %v", expected, got)
	}
}

func TestRange_returnsNilWhenSingleElementRangeHasNoMatch(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(3)

	got := s.Range(2, 2)

	if got != nil {
		t.Fatalf("expected nil when Range(2,2) and 2 is not in set, got %v", got)
	}
}

func TestRange_returnsAllElementsWhenAllAreInRange(t *testing.T) {
	s := New()
	for _, v := range []int{2, 4, 6} {
		s.Insert(v)
	}

	got := s.Range(1, 10)
	expected := []int{2, 4, 6}

	if len(got) != len(expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
	for i := range got {
		if got[i] != expected[i] {
			t.Fatalf("expected %v, got %v", expected, got)
		}
	}
}

// ---- Phase 4: Advanced Coverage (bugmagnet session 2026-04-26) ----

// --- Negative numbers ---

func TestInsert_acceptsNegativeNumbers(t *testing.T) {
	s := New()

	inserted := s.Insert(-5)

	if !inserted {
		t.Fatal("expected Insert(-5) to return true")
	}
	if !s.Contains(-5) {
		t.Fatal("expected Contains(-5) to be true after inserting -5")
	}
}

func TestInsert_maintainsSortedOrderWithNegativeNumbers(t *testing.T) {
	s := New()
	for _, v := range []int{3, -1, 0, -5, 2} {
		s.Insert(v)
	}

	got := s.Values()
	expected := []int{-5, -1, 0, 2, 3}

	if len(got) != len(expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
	for i := range got {
		if got[i] != expected[i] {
			t.Fatalf("expected %v, got %v", expected, got)
		}
	}
}

func TestMin_returnsCorrectValueWhenSetContainsNegativeNumbers(t *testing.T) {
	s := New()
	for _, v := range []int{3, -1, -5, 2} {
		s.Insert(v)
	}

	min, ok := s.Min()

	if !ok {
		t.Fatal("expected ok=true")
	}
	if min != -5 {
		t.Fatalf("expected Min = -5, got %d", min)
	}
}

func TestMax_returnsCorrectValueWhenSetContainsNegativeNumbers(t *testing.T) {
	s := New()
	for _, v := range []int{-3, -1, -5, -2} {
		s.Insert(v)
	}

	max, ok := s.Max()

	if !ok {
		t.Fatal("expected ok=true")
	}
	if max != -1 {
		t.Fatalf("expected Max = -1 for all-negative set, got %d", max)
	}
}

func TestRange_worksWithNegativeBoundaries(t *testing.T) {
	s := New()
	for _, v := range []int{-5, -3, -1, 1, 3} {
		s.Insert(v)
	}

	got := s.Range(-3, 1)
	expected := []int{-3, -1, 1}

	if len(got) != len(expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
	for i := range got {
		if got[i] != expected[i] {
			t.Fatalf("expected %v, got %v", expected, got)
		}
	}
}

func TestRank_returnsCorrectRankForNegativeNumbers(t *testing.T) {
	s := New()
	for _, v := range []int{-5, -3, -1} {
		s.Insert(v)
	}

	if s.Rank(-5) != 0 {
		t.Fatalf("expected Rank(-5) = 0, got %d", s.Rank(-5))
	}
	if s.Rank(-3) != 1 {
		t.Fatalf("expected Rank(-3) = 1, got %d", s.Rank(-3))
	}
	if s.Rank(-1) != 2 {
		t.Fatalf("expected Rank(-1) = 2, got %d", s.Rank(-1))
	}
}

// --- Zero ---

func TestInsert_acceptsZero(t *testing.T) {
	s := New()

	inserted := s.Insert(0)

	if !inserted {
		t.Fatal("expected Insert(0) to return true")
	}
	if !s.Contains(0) {
		t.Fatal("expected Contains(0) to be true after inserting 0")
	}
}

func TestRank_returnsCorrectRankForZero(t *testing.T) {
	s := New()
	s.Insert(-1)
	s.Insert(0)
	s.Insert(1)

	if s.Rank(0) != 1 {
		t.Fatalf("expected Rank(0) = 1, got %d", s.Rank(0))
	}
}

func TestMin_returnsZeroWhenZeroIsMinimum(t *testing.T) {
	s := New()
	s.Insert(0)
	s.Insert(1)
	s.Insert(2)

	min, ok := s.Min()

	if !ok {
		t.Fatal("expected ok=true")
	}
	if min != 0 {
		t.Fatalf("expected Min = 0, got %d", min)
	}
}

// --- Large integers ---

func TestInsert_acceptsMaxInt(t *testing.T) {
	s := New()

	inserted := s.Insert(math.MaxInt)

	if !inserted {
		t.Fatal("expected Insert(math.MaxInt) to return true")
	}
	if !s.Contains(math.MaxInt) {
		t.Fatal("expected Contains(math.MaxInt) to be true")
	}
}

func TestInsert_acceptsMinInt(t *testing.T) {
	s := New()

	inserted := s.Insert(math.MinInt)

	if !inserted {
		t.Fatal("expected Insert(math.MinInt) to return true")
	}
	if !s.Contains(math.MinInt) {
		t.Fatal("expected Contains(math.MinInt) to be true")
	}
}

func TestMin_returnsMinIntWhenItIsSmallest(t *testing.T) {
	s := New()
	s.Insert(math.MinInt)
	s.Insert(0)
	s.Insert(math.MaxInt)

	min, ok := s.Min()

	if !ok {
		t.Fatal("expected ok=true")
	}
	if min != math.MinInt {
		t.Fatalf("expected Min = math.MinInt, got %d", min)
	}
}

func TestMax_returnsMaxIntWhenItIsLargest(t *testing.T) {
	s := New()
	s.Insert(math.MinInt)
	s.Insert(0)
	s.Insert(math.MaxInt)

	max, ok := s.Max()

	if !ok {
		t.Fatal("expected ok=true")
	}
	if max != math.MaxInt {
		t.Fatalf("expected Max = math.MaxInt, got %d", max)
	}
}

func TestRange_worksWithExtremeIntBoundaries(t *testing.T) {
	s := New()
	s.Insert(math.MinInt)
	s.Insert(0)
	s.Insert(math.MaxInt)

	got := s.Range(math.MinInt, math.MaxInt)
	expected := []int{math.MinInt, 0, math.MaxInt}

	if len(got) != len(expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
	for i := range got {
		if got[i] != expected[i] {
			t.Fatalf("expected %v, got %v", expected, got)
		}
	}
}

// --- Large collections ---

func TestInsert_handlesOneHundredUniqueElements(t *testing.T) {
	s := New()
	for i := 0; i < 100; i++ {
		s.Insert(i)
	}

	if s.Len() != 100 {
		t.Fatalf("expected Len = 100 after inserting 100 unique elements, got %d", s.Len())
	}
	got := s.Values()
	for i := 0; i < 100; i++ {
		if got[i] != i {
			t.Fatalf("expected sorted values 0..99, mismatch at index %d: got %d", i, got[i])
		}
	}
}

func TestInsert_handlesOneHundredUniqueElementsInsertedInReverseOrder(t *testing.T) {
	s := New()
	for i := 99; i >= 0; i-- {
		s.Insert(i)
	}

	if s.Len() != 100 {
		t.Fatalf("expected Len = 100, got %d", s.Len())
	}
	got := s.Values()
	for i := 0; i < 100; i++ {
		if got[i] != i {
			t.Fatalf("expected sorted values 0..99 (inserted reverse), mismatch at index %d: got %d", i, got[i])
		}
	}
}

// --- Stateful operation edge cases ---

func TestRemove_returnsFalseOnAlreadyEmptySet(t *testing.T) {
	s := New()

	removed := s.Remove(5)

	if removed {
		t.Fatal("expected Remove on empty set to return false")
	}
}

func TestRemove_returnsFalseWhenRemovingSameElementTwice(t *testing.T) {
	s := New()
	s.Insert(5)
	s.Remove(5)

	removed := s.Remove(5)

	if removed {
		t.Fatal("expected second Remove(5) to return false")
	}
}

func TestRemove_thenLenIsZeroWhenLastElementRemoved(t *testing.T) {
	s := New()
	s.Insert(1)

	s.Remove(1)

	if s.Len() != 0 {
		t.Fatalf("expected Len = 0 after removing last element, got %d", s.Len())
	}
}

func TestContains_returnsFalseAfterRemovingOnlyElement(t *testing.T) {
	s := New()
	s.Insert(7)
	s.Remove(7)

	if s.Contains(7) {
		t.Fatal("expected Contains(7) to be false after removing only element")
	}
}

func TestRange_returnsNilAfterAllElementsRemoved(t *testing.T) {
	s := New()
	s.Insert(5)
	s.Remove(5)

	got := s.Range(1, 10)

	if got != nil {
		t.Fatalf("expected nil from Range on empty set after removal, got %v", got)
	}
}

// --- Interaction: repeated insert/remove cycles ---

func TestInsert_afterMultipleInsertRemoveCyclesMaintainsCorrectState(t *testing.T) {
	s := New()
	for i := 0; i < 5; i++ {
		s.Insert(10)
		s.Remove(10)
	}

	if s.Len() != 0 {
		t.Fatalf("expected empty set after 5 insert/remove cycles, got Len=%d", s.Len())
	}
	if s.Contains(10) {
		t.Fatal("expected Contains(10) to be false after final removal")
	}
}

// --- Range exact-boundary edge cases ---

func TestRange_lowerBoundExcludesElementJustBelowLow(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3, 4, 5} {
		s.Insert(v)
	}

	got := s.Range(3, 5)
	expected := []int{3, 4, 5}

	if len(got) != len(expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
	for i := range got {
		if got[i] != expected[i] {
			t.Fatalf("expected %v, got %v", expected, got)
		}
	}
}

func TestRange_upperBoundExcludesElementJustAboveHigh(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3, 4, 5} {
		s.Insert(v)
	}

	got := s.Range(1, 3)
	expected := []int{1, 2, 3}

	if len(got) != len(expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
	for i := range got {
		if got[i] != expected[i] {
			t.Fatalf("expected %v, got %v", expected, got)
		}
	}
}

// --- Domain constraint violations ---

func TestInsert_duplicateAfterBuildingLargeSet(t *testing.T) {
	s := New()
	for i := 0; i < 50; i++ {
		s.Insert(i)
	}

	// Try inserting a value already in the set
	inserted := s.Insert(25)

	if inserted {
		t.Fatal("expected Insert(25) to return false when 25 already in set of 50 elements")
	}
	if s.Len() != 50 {
		t.Fatalf("expected Len to stay 50 after duplicate insert, got %d", s.Len())
	}
}

func TestRange_returnsNilWhenLowEqualsHighAndValueNotPresent(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(3)
	s.Insert(5)

	got := s.Range(4, 4)

	if got != nil {
		t.Fatalf("expected nil when Range(4,4) and 4 not in set, got %v", got)
	}
}

func TestMin_andMax_equalWhenSetHasSingleElement(t *testing.T) {
	s := New()
	s.Insert(7)

	min, okMin := s.Min()
	max, okMax := s.Max()

	if !okMin || !okMax {
		t.Fatal("expected both Min and Max to return ok=true for single-element set")
	}
	if min != 7 {
		t.Fatalf("expected Min = 7, got %d", min)
	}
	if max != 7 {
		t.Fatalf("expected Max = 7, got %d", max)
	}
	if min != max {
		t.Fatalf("expected Min == Max for single-element set, got min=%d max=%d", min, max)
	}
}
