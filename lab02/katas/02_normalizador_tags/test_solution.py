from solution import normalize_tags


def test_case_and_whitespace_variants_merge():
    tags = ["Machine Learning", "machine-learning", "Machine   learning", "python"]
    result = normalize_tags(tags)
    assert result[0] == ("machine-learning", 3)


def test_top_three_ordered_desc():
    tags = ["python"] * 5 + ["java"] * 3 + ["go"] * 2 + ["rust"] * 1
    result = normalize_tags(tags)
    assert result == [("python", 5), ("java", 3), ("go", 2)]


def test_tie_breaks_alphabetically():
    tags = ["zeta", "alpha", "beta", "alpha", "zeta", "beta"]
    result = normalize_tags(tags)
    assert result == [("alpha", 2), ("beta", 2), ("zeta", 2)]


def test_trims_and_lowercases_single_word_tags():
    tags = ["  Python ", "PYTHON", "python "]
    result = normalize_tags(tags)
    assert result == [("python", 3)]


def test_repeated_separators_collapse_to_single_hyphen():
    tags = ["data   science", "data---science", "data-science"]
    result = normalize_tags(tags)
    assert result == [("data-science", 3)]
