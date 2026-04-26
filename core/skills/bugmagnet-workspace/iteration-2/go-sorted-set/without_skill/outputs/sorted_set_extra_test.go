package sortedset

import (
	"math"
	"reflect"
	"testing"
)

// --- Insert edge cases ---

func TestInsert_OrderMaintainedAscending(t *testing.T) {
	s := New()
	for _, v := range []int{5, 3, 1, 4, 2} {
		s.Insert(v)
	}
	got := s.Values()
	want := []int{1, 2, 3, 4, 5}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("expected %v, got %v", want, got)
	}
}

func TestInsert_OrderMaintainedDescending(t *testing.T) {
	s := New()
	for _, v := range []int{9, 7, 5, 3, 1} {
		s.Insert(v)
	}
	got := s.Values()
	want := []int{1, 3, 5, 7, 9}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("expected %v, got %v", want, got)
	}
}

func TestInsert_NegativeNumbers(t *testing.T) {
	s := New()
	for _, v := range []int{-3, -1, -5, 0, 2} {
		s.Insert(v)
	}
	got := s.Values()
	want := []int{-5, -3, -1, 0, 2}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("expected %v, got %v", want, got)
	}
}

func TestInsert_Zero(t *testing.T) {
	s := New()
	if !s.Insert(0) {
		t.Fatal("expected Insert(0) to return true")
	}
	if s.Insert(0) {
		t.Fatal("expected second Insert(0) to return false")
	}
	if s.Len() != 1 {
		t.Fatalf("expected len 1, got %d", s.Len())
	}
}

func TestInsert_MaxInt(t *testing.T) {
	s := New()
	if !s.Insert(math.MaxInt) {
		t.Fatal("expected Insert(MaxInt) to return true")
	}
	if !s.Contains(math.MaxInt) {
		t.Fatal("expected Contains(MaxInt) to be true")
	}
}

func TestInsert_MinInt(t *testing.T) {
	s := New()
	if !s.Insert(math.MinInt) {
		t.Fatal("expected Insert(MinInt) to return true")
	}
	if !s.Contains(math.MinInt) {
		t.Fatal("expected Contains(MinInt) to be true")
	}
}

func TestInsert_LenIncreasesOnNewValues(t *testing.T) {
	s := New()
	for i := 0; i < 10; i++ {
		s.Insert(i)
		if s.Len() != i+1 {
			t.Fatalf("after %d inserts expected len %d, got %d", i+1, i+1, s.Len())
		}
	}
}

func TestInsert_LenUnchangedOnDuplicate(t *testing.T) {
	s := New()
	s.Insert(42)
	s.Insert(42)
	if s.Len() != 1 {
		t.Fatalf("expected len 1 after duplicate insert, got %d", s.Len())
	}
}

// --- Remove edge cases ---

func TestRemove_EmptySet(t *testing.T) {
	s := New()
	if s.Remove(5) {
		t.Fatal("expected Remove on empty set to return false")
	}
}

func TestRemove_NotPresent(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(2)
	if s.Remove(99) {
		t.Fatal("expected Remove of absent value to return false")
	}
	if s.Len() != 2 {
		t.Fatalf("expected len 2 unchanged, got %d", s.Len())
	}
}

func TestRemove_OnlyElement(t *testing.T) {
	s := New()
	s.Insert(7)
	if !s.Remove(7) {
		t.Fatal("expected Remove of existing value to return true")
	}
	if s.Len() != 0 {
		t.Fatalf("expected len 0 after removing only element, got %d", s.Len())
	}
	if s.Contains(7) {
		t.Fatal("expected Contains(7) to be false after removal")
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
	got := s.Values()
	want := []int{2, 3}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("expected %v, got %v", want, got)
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
	got := s.Values()
	want := []int{1, 2}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("expected %v, got %v", want, got)
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
	got := s.Values()
	want := []int{1, 3}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("expected %v, got %v", want, got)
	}
}

func TestRemove_TwiceReturnsFalseSecondTime(t *testing.T) {
	s := New()
	s.Insert(5)
	s.Remove(5)
	if s.Remove(5) {
		t.Fatal("expected second Remove(5) to return false")
	}
}

func TestRemove_ThenReinsert(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	s.Remove(2)
	if !s.Insert(2) {
		t.Fatal("expected re-insert after remove to return true")
	}
	got := s.Values()
	want := []int{1, 2, 3}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("expected %v after re-insert, got %v", want, got)
	}
}

// --- Contains edge cases ---

func TestContains_EmptySet(t *testing.T) {
	s := New()
	if s.Contains(0) {
		t.Fatal("expected Contains on empty set to be false")
	}
}

func TestContains_NegativeValue(t *testing.T) {
	s := New()
	s.Insert(-10)
	if !s.Contains(-10) {
		t.Fatal("expected Contains(-10) to be true")
	}
	if s.Contains(-9) {
		t.Fatal("expected Contains(-9) to be false")
	}
}

func TestContains_AfterRemoval(t *testing.T) {
	s := New()
	s.Insert(3)
	s.Remove(3)
	if s.Contains(3) {
		t.Fatal("expected Contains(3) to be false after removal")
	}
}

// --- Rank edge cases ---

func TestRank_EmptySet(t *testing.T) {
	s := New()
	if s.Rank(5) != -1 {
		t.Fatal("expected Rank on empty set to be -1")
	}
}

func TestRank_NotPresent(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(3)
	if s.Rank(2) != -1 {
		t.Fatal("expected Rank(2) to be -1 when 2 not in set")
	}
}

func TestRank_FirstElement(t *testing.T) {
	s := New()
	for _, v := range []int{10, 20, 30} {
		s.Insert(v)
	}
	if s.Rank(10) != 0 {
		t.Fatalf("expected Rank(10) == 0, got %d", s.Rank(10))
	}
}

func TestRank_LastElement(t *testing.T) {
	s := New()
	for _, v := range []int{10, 20, 30} {
		s.Insert(v)
	}
	if s.Rank(30) != 2 {
		t.Fatalf("expected Rank(30) == 2, got %d", s.Rank(30))
	}
}

func TestRank_MiddleElement(t *testing.T) {
	s := New()
	for _, v := range []int{10, 20, 30} {
		s.Insert(v)
	}
	if s.Rank(20) != 1 {
		t.Fatalf("expected Rank(20) == 1, got %d", s.Rank(20))
	}
}

func TestRank_ShiftsAfterInsert(t *testing.T) {
	s := New()
	s.Insert(10)
	s.Insert(30)
	if s.Rank(30) != 1 {
		t.Fatalf("expected Rank(30) == 1, got %d", s.Rank(30))
	}
	s.Insert(20) // inserted between 10 and 30
	if s.Rank(30) != 2 {
		t.Fatalf("expected Rank(30) == 2 after inserting 20, got %d", s.Rank(30))
	}
}

func TestRank_ShiftsAfterRemove(t *testing.T) {
	s := New()
	for _, v := range []int{10, 20, 30} {
		s.Insert(v)
	}
	if s.Rank(30) != 2 {
		t.Fatalf("expected Rank(30) == 2, got %d", s.Rank(30))
	}
	s.Remove(10)
	if s.Rank(30) != 1 {
		t.Fatalf("expected Rank(30) == 1 after removing 10, got %d", s.Rank(30))
	}
}

func TestRank_NegativeValues(t *testing.T) {
	s := New()
	for _, v := range []int{-10, -5, 0, 5} {
		s.Insert(v)
	}
	if s.Rank(-10) != 0 {
		t.Fatalf("expected Rank(-10) == 0, got %d", s.Rank(-10))
	}
	if s.Rank(0) != 2 {
		t.Fatalf("expected Rank(0) == 2, got %d", s.Rank(0))
	}
}

// --- Range edge cases ---

func TestRange_EmptySet(t *testing.T) {
	s := New()
	got := s.Range(1, 10)
	if got != nil {
		t.Fatalf("expected nil for Range on empty set, got %v", got)
	}
}

func TestRange_LowGreaterThanHigh(t *testing.T) {
	s := New()
	s.Insert(5)
	got := s.Range(10, 5)
	if got != nil {
		t.Fatalf("expected nil when low > high, got %v", got)
	}
}

func TestRange_LowEqualsHigh_Present(t *testing.T) {
	s := New()
	for _, v := range []int{1, 3, 5, 7} {
		s.Insert(v)
	}
	got := s.Range(3, 3)
	want := []int{3}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("expected %v for Range(3,3), got %v", want, got)
	}
}

func TestRange_LowEqualsHigh_NotPresent(t *testing.T) {
	s := New()
	for _, v := range []int{1, 3, 5, 7} {
		s.Insert(v)
	}
	got := s.Range(4, 4)
	if got != nil {
		t.Fatalf("expected nil for Range(4,4) when 4 not in set, got %v", got)
	}
}

func TestRange_AllElements(t *testing.T) {
	s := New()
	for _, v := range []int{2, 4, 6, 8} {
		s.Insert(v)
	}
	got := s.Range(1, 10)
	want := []int{2, 4, 6, 8}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("expected %v, got %v", want, got)
	}
}

func TestRange_NoElementsInRange(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 8, 9} {
		s.Insert(v)
	}
	got := s.Range(3, 7)
	if got != nil {
		t.Fatalf("expected nil when no elements in range [3,7], got %v", got)
	}
}

func TestRange_BoundaryValuesIncluded(t *testing.T) {
	s := New()
	for _, v := range []int{1, 5, 10, 15, 20} {
		s.Insert(v)
	}
	got := s.Range(5, 15)
	want := []int{5, 10, 15}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("expected boundary values inclusive %v, got %v", want, got)
	}
}

func TestRange_RangeAboveAllElements(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	got := s.Range(10, 20)
	if got != nil {
		t.Fatalf("expected nil when range is above all elements, got %v", got)
	}
}

func TestRange_RangeBelowAllElements(t *testing.T) {
	s := New()
	for _, v := range []int{10, 20, 30} {
		s.Insert(v)
	}
	got := s.Range(1, 5)
	if got != nil {
		t.Fatalf("expected nil when range is below all elements, got %v", got)
	}
}

func TestRange_NegativeValues(t *testing.T) {
	s := New()
	for _, v := range []int{-10, -5, 0, 5, 10} {
		s.Insert(v)
	}
	got := s.Range(-7, 3)
	want := []int{-5, 0}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("expected %v, got %v", want, got)
	}
}

func TestRange_NegativeLowAndHigh(t *testing.T) {
	s := New()
	for _, v := range []int{-20, -10, -5, -1, 0} {
		s.Insert(v)
	}
	got := s.Range(-12, -3)
	want := []int{-10, -5}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("expected %v, got %v", want, got)
	}
}

func TestRange_DoesNotMutateSet(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	got := s.Range(1, 3)
	got[0] = 999
	if s.Contains(999) {
		t.Fatal("mutating Range result should not affect the set")
	}
}

// BUG: Range with high == math.MaxInt overflows (high+1 wraps to math.MinInt),
// causing sort.SearchInts to return 0 for the end index.
// This makes the Range return nil even when elements are in range.
// See summary.md for full details.
func TestRange_MaxIntHigh_OverflowBug(t *testing.T) {
	s := New()
	for _, v := range []int{1, 100, 1000} {
		s.Insert(v)
	}
	// BUG: this currently returns nil due to integer overflow in high+1
	got := s.Range(1, math.MaxInt)
	want := []int{1, 100, 1000}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("BUG (overflow): expected %v for Range(1, MaxInt), got %v", want, got)
	}
}

// --- Min / Max edge cases ---

func TestMin_EmptySet(t *testing.T) {
	s := New()
	val, ok := s.Min()
	if ok {
		t.Fatal("expected ok=false for Min on empty set")
	}
	if val != 0 {
		t.Fatalf("expected zero value 0 for empty Min, got %d", val)
	}
}

func TestMax_EmptySet(t *testing.T) {
	s := New()
	val, ok := s.Max()
	if ok {
		t.Fatal("expected ok=false for Max on empty set")
	}
	if val != 0 {
		t.Fatalf("expected zero value 0 for empty Max, got %d", val)
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
		t.Fatalf("expected Min == 42, got %d", val)
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
		t.Fatalf("expected Max == 42, got %d", val)
	}
}

func TestMin_MultipleElements(t *testing.T) {
	s := New()
	for _, v := range []int{5, 3, 8, 1, 7} {
		s.Insert(v)
	}
	val, ok := s.Min()
	if !ok || val != 1 {
		t.Fatalf("expected Min == 1, got %d (ok=%v)", val, ok)
	}
}

func TestMax_MultipleElements(t *testing.T) {
	s := New()
	for _, v := range []int{5, 3, 8, 1, 7} {
		s.Insert(v)
	}
	val, ok := s.Max()
	if !ok || val != 8 {
		t.Fatalf("expected Max == 8, got %d (ok=%v)", val, ok)
	}
}

func TestMin_NegativeValues(t *testing.T) {
	s := New()
	for _, v := range []int{-1, -5, 3, 0} {
		s.Insert(v)
	}
	val, ok := s.Min()
	if !ok || val != -5 {
		t.Fatalf("expected Min == -5, got %d (ok=%v)", val, ok)
	}
}

func TestMax_NegativeValues(t *testing.T) {
	s := New()
	for _, v := range []int{-1, -5, -3} {
		s.Insert(v)
	}
	val, ok := s.Max()
	if !ok || val != -1 {
		t.Fatalf("expected Max == -1, got %d (ok=%v)", val, ok)
	}
}

func TestMin_AfterRemovingMinimum(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	s.Remove(1)
	val, ok := s.Min()
	if !ok || val != 2 {
		t.Fatalf("expected Min == 2 after removing 1, got %d (ok=%v)", val, ok)
	}
}

func TestMax_AfterRemovingMaximum(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3} {
		s.Insert(v)
	}
	s.Remove(3)
	val, ok := s.Max()
	if !ok || val != 2 {
		t.Fatalf("expected Max == 2 after removing 3, got %d (ok=%v)", val, ok)
	}
}

func TestMinEqualsMaxForSingleElement(t *testing.T) {
	s := New()
	s.Insert(7)
	minVal, minOk := s.Min()
	maxVal, maxOk := s.Max()
	if !minOk || !maxOk {
		t.Fatal("expected both Min and Max to be ok for single element")
	}
	if minVal != maxVal {
		t.Fatalf("expected Min == Max for single element, got min=%d max=%d", minVal, maxVal)
	}
}

// --- Len edge cases ---

func TestLen_EmptySet(t *testing.T) {
	s := New()
	if s.Len() != 0 {
		t.Fatalf("expected Len 0 for new set, got %d", s.Len())
	}
}

func TestLen_AfterMixedOperations(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(2)
	s.Insert(3)
	s.Remove(2)
	s.Insert(4)
	s.Insert(3) // duplicate, should not increase len
	if s.Len() != 3 {
		t.Fatalf("expected Len 3 after mixed ops, got %d", s.Len())
	}
}

// --- Values edge cases ---

func TestValues_EmptySet(t *testing.T) {
	s := New()
	got := s.Values()
	if len(got) != 0 {
		t.Fatalf("expected empty slice for Values on empty set, got %v", got)
	}
}

func TestValues_ReturnsCopy(t *testing.T) {
	s := New()
	s.Insert(1)
	s.Insert(2)
	s.Insert(3)
	v := s.Values()
	v[0] = 999
	got := s.Values()
	if got[0] == 999 {
		t.Fatal("expected Values to return an independent copy, not a view")
	}
}

func TestValues_SortedOrder(t *testing.T) {
	s := New()
	for _, v := range []int{50, 10, 40, 20, 30} {
		s.Insert(v)
	}
	got := s.Values()
	want := []int{10, 20, 30, 40, 50}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("expected sorted %v, got %v", want, got)
	}
}

// --- Combined / integration scenarios ---

func TestInsertRemoveContainsCycle(t *testing.T) {
	s := New()
	vals := []int{-100, 0, 1, 50, 99}
	for _, v := range vals {
		s.Insert(v)
	}
	for _, v := range vals {
		if !s.Contains(v) {
			t.Fatalf("expected Contains(%d) after insert", v)
		}
	}
	for _, v := range vals {
		s.Remove(v)
	}
	for _, v := range vals {
		if s.Contains(v) {
			t.Fatalf("expected Contains(%d) to be false after remove", v)
		}
	}
	if s.Len() != 0 {
		t.Fatalf("expected Len 0 after removing all, got %d", s.Len())
	}
}

func TestInsertManyElementsPreservesOrder(t *testing.T) {
	s := New()
	// Insert in random-ish order
	inputs := []int{42, 7, 99, 1, 55, 3, 17, 88, 23, 64}
	for _, v := range inputs {
		s.Insert(v)
	}
	got := s.Values()
	for i := 1; i < len(got); i++ {
		if got[i] <= got[i-1] {
			t.Fatalf("expected sorted order, got %v", got)
		}
	}
}

func TestRankConsistentWithValues(t *testing.T) {
	s := New()
	for _, v := range []int{10, 30, 20, 40, 50} {
		s.Insert(v)
	}
	vals := s.Values()
	for i, v := range vals {
		r := s.Rank(v)
		if r != i {
			t.Fatalf("expected Rank(%d) == %d (position in sorted Values), got %d", v, i, r)
		}
	}
}

func TestRangeAfterRemovals(t *testing.T) {
	s := New()
	for _, v := range []int{1, 2, 3, 4, 5, 6, 7} {
		s.Insert(v)
	}
	s.Remove(3)
	s.Remove(5)
	got := s.Range(2, 6)
	want := []int{2, 4, 6}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("expected %v after removals, got %v", want, got)
	}
}
