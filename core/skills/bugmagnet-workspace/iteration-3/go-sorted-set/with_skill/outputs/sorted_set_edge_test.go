package sortedset

import (
	"math"
	"testing"
)

// ─── Empty set ───────────────────────────────────────────────────────────────

func TestContainsOnEmptySet(t *testing.T) {
	s := New()
	if s.Contains(0) {
		t.Fatal("Contains on empty set should return false")
	}
}

func TestRemoveOnEmptySet(t *testing.T) {
	s := New()
	if s.Remove(42) {
		t.Fatal("Remove on empty set should return false")
	}
}

func TestRankOnEmptySet(t *testing.T) {
	s := New()
	if s.Rank(0) != -1 {
		t.Fatal("Rank on empty set should return -1")
	}
}

func TestRangeOnEmptySet(t *testing.T) {
	s := New()
	got := s.Range(1, 5)
	if got != nil {
		t.Fatalf("Range on empty set should return nil, got %v", got)
	}
}

func TestMinOnEmptySet(t *testing.T) {
	s := New()
	_, ok := s.Min()
	if ok {
		t.Fatal("Min on empty set should return ok=false")
	}
}

func TestMaxOnEmptySet(t *testing.T) {
	s := New()
	_, ok := s.Max()
	if ok {
		t.Fatal("Max on empty set should return ok=false")
	}
}

func TestLenOnEmptySet(t *testing.T) {
	s := New()
	if s.Len() != 0 {
		t.Fatalf("Len on empty set should be 0, got %d", s.Len())
	}
}

func TestValuesOnEmptySet(t *testing.T) {
	s := New()
	got := s.Values()
	if len(got) != 0 {
		t.Fatalf("Values on empty set should be empty, got %v", got)
	}
}

// ─── Single element ───────────────────────────────────────────────────────────

func TestSingleElementAllOperations(t *testing.T) {
	s := New()
	s.Insert(7)

	if !s.Contains(7) {
		t.Fatal("Contains should find the single element")
	}
	if s.Len() != 1 {
		t.Fatalf("Len should be 1, got %d", s.Len())
	}
	if s.Rank(7) != 0 {
		t.Fatalf("Rank of single element should be 0, got %d", s.Rank(7))
	}
	min, ok := s.Min()
	if !ok || min != 7 {
		t.Fatalf("Min should be (7, true), got (%d, %v)", min, ok)
	}
	max, ok := s.Max()
	if !ok || max != 7 {
		t.Fatalf("Max should be (7, true), got (%d, %v)", max, ok)
	}
	got := s.Values()
	if len(got) != 1 || got[0] != 7 {
		t.Fatalf("Values should be [7], got %v", got)
	}
}

// ─── Insert ──────────────────────────────────────────────────────────────────

func TestInsertMaintainsSortedOrder(t *testing.T) {
	s := New()
	inputs := []int{5, 3, 8, 1, 4, 7, 2, 6}
	for _, v := range inputs {
		s.Insert(v)
	}
	vals := s.Values()
	for i := 1; i < len(vals); i++ {
		if vals[i] <= vals[i-1] {
			t.Fatalf("Values not sorted at index %d: %v", i, vals)
		}
	}
}

func TestInsertDuplicateReturnsFalse(t *testing.T) {
	s := New()
	s.Insert(10)
	if s.Insert(10) {
		t.Fatal("inserting duplicate should return false")
	}
	if s.Len() != 1 {
		t.Fatalf("Len should remain 1 after duplicate insert, got %d", s.Len())
	}
}

func TestInsertZero(t *testing.T) {
	s := New()
	if !s.Insert(0) {
		t.Fatal("inserting zero should return true")
	}
	if !s.Contains(0) {
		t.Fatal("should contain zero after insert")
	}
}

func TestInsertNegativeNumbers(t *testing.T) {
	s := New()
	s.Insert(-5)
	s.Insert(-1)
	s.Insert(-10)
	vals := s.Values()
	expected := []int{-10, -5, -1}
	for i, v := range vals {
		if v != expected[i] {
			t.Fatalf("expected %v, got %v", expected, vals)
		}
	}
}

func TestInsertMinInt(t *testing.T) {
	s := New()
	if !s.Insert(math.MinInt) {
		t.Fatal("inserting math.MinInt should return true")
	}
	if !s.Contains(math.MinInt) {
		t.Fatal("should contain math.MinInt after insert")
	}
	if s.Rank(math.MinInt) != 0 {
		t.Fatalf("Rank(math.MinInt) should be 0, got %d", s.Rank(math.MinInt))
	}
}

func TestInsertMaxInt(t *testing.T) {
	s := New()
	if !s.Insert(math.MaxInt) {
		t.Fatal("inserting math.MaxInt should return true")
	}
	if !s.Contains(math.MaxInt) {
		t.Fatal("should contain math.MaxInt after insert")
	}
}

func TestInsertMixedNegativePositive(t *testing.T) {
	s := New()
	for _, v := range []int{-3, 0, 3, -1, 1} {
		s.Insert(v)
	}
	vals := s.Values()
	expected := []int{-3, -1, 0, 1, 3}
	for i, v := range vals {
		if v != expected[i] {
			t.Fatalf("expected %v, got %v", expected, vals)
		}
	}
}

// ─── Remove ──────────────────────────────────────────────────────────────────

func TestRemoveAbsentElementReturnsFalse(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(2)
	if s.Remove(99) {
		t.Fatal("removing absent element should return false")
	}
	if s.Len() != 2 {
		t.Fatalf("Len should remain 2, got %d", s.Len())
	}
}

func TestRemoveOnlyElement(t *testing.T) {
	s := New()
	s.Insert(42)
	if !s.Remove(42) {
		t.Fatal("removing existing element should return true")
	}
	if s.Len() != 0 {
		t.Fatalf("Len should be 0 after removing only element, got %d", s.Len())
	}
	if s.Contains(42) {
		t.Fatal("should not contain element after removal")
	}
}

func TestRemoveFirstElement(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	if !s.Remove(1) {
		t.Fatal("removing first element should return true")
	}
	if s.Contains(1) {
		t.Fatal("should not contain removed element")
	}
	vals := s.Values()
	expected := []int{2, 3}
	for i, v := range vals {
		if v != expected[i] {
			t.Fatalf("expected %v, got %v", expected, vals)
		}
	}
}

func TestRemoveLastElement(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	if !s.Remove(3) {
		t.Fatal("removing last element should return true")
	}
	if s.Contains(3) {
		t.Fatal("should not contain removed element")
	}
	vals := s.Values()
	expected := []int{1, 2}
	for i, v := range vals {
		if v != expected[i] {
			t.Fatalf("expected %v, got %v", expected, vals)
		}
	}
}

func TestRemoveMiddleElement(t *testing.T) {
	s := New()
	for _, v := range []int{10, 20, 30} {
		s.Insert(v)
	}
	if !s.Remove(20) {
		t.Fatal("removing middle element should return true")
	}
	vals := s.Values()
	expected := []int{10, 30}
	for i, v := range vals {
		if v != expected[i] {
			t.Fatalf("expected %v, got %v", expected, vals)
		}
	}
}

func TestRemoveAndReinsert(t *testing.T) {
	s := New()
	s.Insert(5)
	s.Remove(5)
	if !s.Insert(5) {
		t.Fatal("reinserting a removed element should return true")
	}
	if !s.Contains(5) {
		t.Fatal("should contain element after reinsertion")
	}
}

// ─── Contains ────────────────────────────────────────────────────────────────

func TestContainsNegativeNumber(t *testing.T) {
	s := New()
	s.Insert(-42)
	if !s.Contains(-42) {
		t.Fatal("should contain -42 after insert")
	}
	if s.Contains(-43) {
		t.Fatal("should not contain -43")
	}
}

func TestContainsAdjacentValues(t *testing.T) {
	s := New()
	s.Insert(5)
	if s.Contains(4) {
		t.Fatal("should not contain 4 (only 5 inserted)")
	}
	if s.Contains(6) {
		t.Fatal("should not contain 6 (only 5 inserted)")
	}
}

// ─── Rank ────────────────────────────────────────────────────────────────────

func TestRankReturnsCorrectIndex(t *testing.T) {
	s := New()
	for _, v := range []int{10, 20, 30, 40, 50} {
		s.Insert(v)
	}
	cases := []struct {
		val      int
		expected int
	}{
		{10, 0},
		{20, 1},
		{30, 2},
		{40, 3},
		{50, 4},
	}
	for _, tc := range cases {
		if got := s.Rank(tc.val); got != tc.expected {
			t.Fatalf("Rank(%d) = %d, want %d", tc.val, got, tc.expected)
		}
	}
}

func TestRankOfAbsentElement(t *testing.T) {
	s := New()
	for _, v := range []int{1, 3, 5} {
		s.Insert(v)
	}
	if s.Rank(2) != -1 {
		t.Fatalf("Rank of absent element should be -1, got %d", s.Rank(2))
	}
	if s.Rank(0) != -1 {
		t.Fatalf("Rank of value below min should be -1, got %d", s.Rank(0))
	}
	if s.Rank(6) != -1 {
		t.Fatalf("Rank of value above max should be -1, got %d", s.Rank(6))
	}
}

func TestRankAfterRemoval(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	s.Remove(1)
	if s.Rank(2) != 0 {
		t.Fatalf("after removing 1, Rank(2) should be 0, got %d", s.Rank(2))
	}
	if s.Rank(3) != 1 {
		t.Fatalf("after removing 1, Rank(3) should be 1, got %d", s.Rank(3))
	}
}

// ─── Range ────────────────────────────────────────────────────────────────────

func TestRangeInvertedBoundsReturnsNil(t *testing.T) {
	s := New()
	s.Insert(5)
	got := s.Range(10, 1)
	if got != nil {
		t.Fatalf("Range with low > high should return nil, got %v", got)
	}
}

func TestRangeSingleElementBoundary(t *testing.T) {
	s := New()
	for _, v := range []int{1, 3, 5, 7} {
		s.Insert(v)
	}
	got := s.Range(3, 3)
	if len(got) != 1 || got[0] != 3 {
		t.Fatalf("Range(3,3) should return [3], got %v", got)
	}
}

func TestRangeElementNotPresentExactBounds(t *testing.T) {
	s := New()
	for _, v := range []int{1, 5, 9} {
		s.Insert(v)
	}
	got := s.Range(3, 3)
	if got != nil {
		t.Fatalf("Range(3,3) when 3 not in set should return nil, got %v", got)
	}
}

func TestRangeExcludesOutOfBoundsValues(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3, 4, 5} {
		s.Insert(v)
	}
	got := s.Range(2, 4)
	expected := []int{2, 3, 4}
	if len(got) != len(expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
	for i, v := range got {
		if v != expected[i] {
			t.Fatalf("expected %v, got %v", expected, got)
		}
	}
}

func TestRangeBoundsNotInSet(t *testing.T) {
	s := New()
	for _, v := range []int{1, 3, 5, 7, 9} {
		s.Insert(v)
	}
	got := s.Range(2, 8)
	expected := []int{3, 5, 7}
	if len(got) != len(expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
	for i, v := range got {
		if v != expected[i] {
			t.Fatalf("expected %v, got %v", expected, got)
		}
	}
}

func TestRangeEntireSet(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	got := s.Range(1, 3)
	expected := []int{1, 2, 3}
	if len(got) != len(expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
}

func TestRangeAboveAllElements(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	got := s.Range(10, 20)
	if got != nil {
		t.Fatalf("Range above all elements should return nil, got %v", got)
	}
}

func TestRangeBelowAllElements(t *testing.T) {
	s := New()
	for _, v := range []int{10, 20, 30} {
		s.Insert(v)
	}
	got := s.Range(1, 5)
	if got != nil {
		t.Fatalf("Range below all elements should return nil, got %v", got)
	}
}

func TestRangeWithNegativeNumbers(t *testing.T) {
	s := New()
	for _, v := range []int{-5, -3, -1, 1, 3} {
		s.Insert(v)
	}
	got := s.Range(-3, 1)
	expected := []int{-3, -1, 1}
	if len(got) != len(expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
	for i, v := range got {
		if v != expected[i] {
			t.Fatalf("expected %v, got %v", expected, got)
		}
	}
}

func TestRangeEqualLowHigh_BUG(t *testing.T) {
	/*
	 * ROOT CAUSE: Range(low, high) computes end = sort.SearchInts(s.data, high+1).
	 *             When high = math.MaxInt, high+1 overflows to math.MinInt.
	 *             sort.SearchInts(s.data, math.MinInt) returns 0 (since MinInt ≤ all elements).
	 *             Therefore end = 0, and the guard "start >= end" is true for any start ≥ 0,
	 *             so Range returns nil even though elements ≤ math.MaxInt exist.
	 * CODE LOCATION: sorted_set.go:55 — end := sort.SearchInts(s.data, high+1)
	 * PROPOSED FIX: Special-case when high == math.MaxInt: set end = len(s.data)
	 *               instead of computing high+1.
	 * EXPECTED: Range(math.MaxInt, math.MaxInt) returns [math.MaxInt]
	 * ACTUAL:   Returns nil due to integer overflow of high+1
	 */
	t.Skip("BUG: Range(math.MaxInt, math.MaxInt) overflows high+1 — returns nil instead of [math.MaxInt]")
	s := New()
	s.Insert(math.MaxInt)
	got := s.Range(math.MaxInt, math.MaxInt)
	if len(got) != 1 || got[0] != math.MaxInt {
		t.Fatalf("Range(MaxInt, MaxInt) should return [MaxInt], got %v", got)
	}
}

func TestRangeWithMaxIntUpperBound_BUG(t *testing.T) {
	/*
	 * ROOT CAUSE: Same overflow issue as above. When high = math.MaxInt,
	 *             high+1 wraps to math.MinInt and SearchInts returns 0,
	 *             so no elements are returned.
	 * CODE LOCATION: sorted_set.go:55 — end := sort.SearchInts(s.data, high+1)
	 * PROPOSED FIX: When high == math.MaxInt, set end = len(s.data).
	 * EXPECTED: Range(1, math.MaxInt) returns [1, 2, 3] when those are in the set
	 * ACTUAL:   Returns nil due to integer overflow
	 */
	t.Skip("BUG: Range with high=math.MaxInt overflows high+1 — returns nil instead of matching elements")
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	got := s.Range(1, math.MaxInt)
	expected := []int{1, 2, 3}
	if len(got) != len(expected) {
		t.Fatalf("Range(1, MaxInt) should return %v, got %v", expected, got)
	}
}

// ─── Min / Max ────────────────────────────────────────────────────────────────

func TestMinAfterMultipleInserts(t *testing.T) {
	s := New()
	for _, v := range []int{5, 3, 8, 1, 9} {
		s.Insert(v)
	}
	min, ok := s.Min()
	if !ok || min != 1 {
		t.Fatalf("Min should be (1, true), got (%d, %v)", min, ok)
	}
}

func TestMaxAfterMultipleInserts(t *testing.T) {
	s := New()
	for _, v := range []int{5, 3, 8, 1, 9} {
		s.Insert(v)
	}
	max, ok := s.Max()
	if !ok || max != 9 {
		t.Fatalf("Max should be (9, true), got (%d, %v)", max, ok)
	}
}

func TestMinAfterRemovingMinimum(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	s.Remove(1)
	min, ok := s.Min()
	if !ok || min != 2 {
		t.Fatalf("Min after removing 1 should be (2, true), got (%d, %v)", min, ok)
	}
}

func TestMaxAfterRemovingMaximum(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	s.Remove(3)
	max, ok := s.Max()
	if !ok || max != 2 {
		t.Fatalf("Max after removing 3 should be (2, true), got (%d, %v)", max, ok)
	}
}

func TestMinMaxWithNegatives(t *testing.T) {
	s := New()
	for _, v := range []int{-10, -5, 0, 5, 10} {
		s.Insert(v)
	}
	min, _ := s.Min()
	max, _ := s.Max()
	if min != -10 {
		t.Fatalf("Min should be -10, got %d", min)
	}
	if max != 10 {
		t.Fatalf("Max should be 10, got %d", max)
	}
}

func TestMinMaxAfterRemoveAllButOne(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	s.Remove(1)
	s.Remove(3)
	min, okMin := s.Min()
	max, okMax := s.Max()
	if !okMin || min != 2 {
		t.Fatalf("Min should be (2, true), got (%d, %v)", min, okMin)
	}
	if !okMax || max != 2 {
		t.Fatalf("Max should be (2, true), got (%d, %v)", max, okMax)
	}
}

// ─── Values ───────────────────────────────────────────────────────────────────

func TestValuesMutationDoesNotAffectSet(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	vals := s.Values()
	vals[0] = 999
	if s.Contains(999) {
		t.Fatal("mutating Values() result should not affect the set")
	}
	if !s.Contains(1) {
		t.Fatal("original set element should still be present after mutating Values() result")
	}
}

func TestValuesReturnsSortedSlice(t *testing.T) {
	s := New()
	for _, v := range []int{9, 3, 7, 1, 5} {
		s.Insert(v)
	}
	vals := s.Values()
	expected := []int{1, 3, 5, 7, 9}
	for i, v := range vals {
		if v != expected[i] {
			t.Fatalf("expected sorted %v, got %v", expected, vals)
		}
	}
}

// ─── Idempotency and compound operations ─────────────────────────────────────

func TestInsertRemoveInsertCyclePreservesCorrectness(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3, 4, 5} {
		s.Insert(v)
	}
	s.Remove(3)
	s.Insert(3)
	if s.Len() != 5 {
		t.Fatalf("Len should be 5 after remove+reinsert cycle, got %d", s.Len())
	}
	if s.Rank(3) != 2 {
		t.Fatalf("Rank(3) should be 2, got %d", s.Rank(3))
	}
}

func TestRemoveAllElementsOneByOne(t *testing.T) {
	s := New()
	vals := []int{1, 2, 3, 4, 5}
	for _, v := range vals {
		s.Insert(v)
	}
	for _, v := range vals {
		if !s.Remove(v) {
			t.Fatalf("Remove(%d) should return true", v)
		}
	}
	if s.Len() != 0 {
		t.Fatalf("Len should be 0 after removing all elements, got %d", s.Len())
	}
	_, ok := s.Min()
	if ok {
		t.Fatal("Min on empty set should return ok=false")
	}
	_, ok = s.Max()
	if ok {
		t.Fatal("Max on empty set should return ok=false")
	}
}

func TestRangeAfterRemovals(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3, 4, 5} {
		s.Insert(v)
	}
	s.Remove(2)
	s.Remove(4)
	got := s.Range(1, 5)
	expected := []int{1, 3, 5}
	if len(got) != len(expected) {
		t.Fatalf("expected %v, got %v", expected, got)
	}
	for i, v := range got {
		if v != expected[i] {
			t.Fatalf("expected %v, got %v", expected, got)
		}
	}
}
