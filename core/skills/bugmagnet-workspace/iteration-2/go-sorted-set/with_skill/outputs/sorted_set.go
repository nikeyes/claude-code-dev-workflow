package sortedset

import "sort"

type SortedSet struct {
	data []int
}

func New() *SortedSet {
	return &SortedSet{}
}

func (s *SortedSet) search(val int) int {
	return sort.SearchInts(s.data, val)
}

func (s *SortedSet) Insert(val int) bool {
	i := s.search(val)
	if i < len(s.data) && s.data[i] == val {
		return false
	}
	s.data = append(s.data, 0)
	copy(s.data[i+1:], s.data[i:])
	s.data[i] = val
	return true
}

func (s *SortedSet) Remove(val int) bool {
	i := s.search(val)
	if i >= len(s.data) || s.data[i] != val {
		return false
	}
	s.data = append(s.data[:i], s.data[i+1:]...)
	return true
}

func (s *SortedSet) Contains(val int) bool {
	i := s.search(val)
	return i < len(s.data) && s.data[i] == val
}

func (s *SortedSet) Rank(val int) int {
	i := s.search(val)
	if i < len(s.data) && s.data[i] == val {
		return i
	}
	return -1
}

func (s *SortedSet) Range(low, high int) []int {
	if low > high {
		return nil
	}
	start := sort.SearchInts(s.data, low)
	end := sort.SearchInts(s.data, high+1)
	if start >= len(s.data) || start >= end {
		return nil
	}
	result := make([]int, end-start)
	copy(result, s.data[start:end])
	return result
}

func (s *SortedSet) Len() int {
	return len(s.data)
}

func (s *SortedSet) Min() (int, bool) {
	if len(s.data) == 0 {
		return 0, false
	}
	return s.data[0], true
}

func (s *SortedSet) Max() (int, bool) {
	if len(s.data) == 0 {
		return 0, false
	}
	return s.data[len(s.data)-1], true
}

func (s *SortedSet) Values() []int {
	result := make([]int, len(s.data))
	copy(result, s.data)
	return result
}
