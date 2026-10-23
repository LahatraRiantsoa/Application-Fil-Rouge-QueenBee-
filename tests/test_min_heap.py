import random

import pytest

from queenbee_routing.min_heap import MinHeap


def test_pop_returns_elements_in_increasing_order():
    rng = random.Random(1)
    values = [rng.randint(0, 1000) for _ in range(500)]
    heap = MinHeap()
    for v in values:
        heap.push(v, f"item-{v}")

    popped = [heap.pop()[0] for _ in range(len(values))]

    assert popped == sorted(values)
    assert heap.is_empty()


def test_peek_does_not_remove():
    heap = MinHeap()
    heap.push(5, "a")
    heap.push(2, "b")
    assert heap.peek() == (2, "b")
    assert len(heap) == 2


def test_duplicate_priorities_are_all_kept():
    heap = MinHeap()
    for name in "abc":
        heap.push(1, name)
    assert sorted(heap.pop()[1] for _ in range(3)) == ["a", "b", "c"]


def test_pop_on_empty_heap_raises():
    with pytest.raises(IndexError):
        MinHeap().pop()
