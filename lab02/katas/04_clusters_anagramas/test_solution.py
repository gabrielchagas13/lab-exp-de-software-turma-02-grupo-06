from solution import anagram_clusters


def test_example_from_kata():
    words = ["ola", "lao", "gato", "toga"]
    assert anagram_clusters(words) == [["gato", "toga"], ["lao", "ola"]]


def test_singletons_form_own_groups():
    words = ["abc", "xyz"]
    assert anagram_clusters(words) == [["abc"], ["xyz"]]


def test_all_same_word_repeated():
    words = ["aab", "aba", "baa"]
    assert anagram_clusters(words) == [["aab", "aba", "baa"]]


def test_tie_in_group_size_orders_by_first_word():
    words = ["ba", "ab", "dc", "cd"]
    assert anagram_clusters(words) == [["ab", "ba"], ["cd", "dc"]]


def test_mixed_sizes_sorted_by_size_desc():
    words = ["a", "listen", "silent", "enlist", "z"]
    assert anagram_clusters(words) == [
        ["enlist", "listen", "silent"],
        ["a"],
        ["z"],
    ]
