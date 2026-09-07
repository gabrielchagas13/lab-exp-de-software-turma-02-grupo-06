from solution import weekly_spending


def test_single_week_obvious_winner():
    purchases = [
        {"item": "a", "value": 10.0, "day": 0},
        {"item": "b", "value": 5.0, "day": 8},
    ]
    assert weekly_spending(purchases) == (0, 10.0)


def test_multiple_purchases_same_week():
    purchases = [
        {"item": "a", "value": 10.0, "day": 1},
        {"item": "b", "value": 15.0, "day": 3},
        {"item": "c", "value": 1.0, "day": 20},
    ]
    assert weekly_spending(purchases) == (0, 25.0)


def test_winner_in_last_week():
    purchases = [
        {"item": "a", "value": 5.0, "day": 0},
        {"item": "b", "value": 5.0, "day": 8},
        {"item": "c", "value": 100.0, "day": 27},
    ]
    assert weekly_spending(purchases) == (3, 100.0)


def test_tie_returns_lowest_week_index():
    purchases = [
        {"item": "a", "value": 50.0, "day": 2},
        {"item": "b", "value": 50.0, "day": 16},
    ]
    assert weekly_spending(purchases) == (0, 50.0)


def test_week_boundaries():
    purchases = [
        {"item": "a", "value": 1.0, "day": 6},   # semana 0
        {"item": "b", "value": 2.0, "day": 7},   # semana 1
        {"item": "c", "value": 2.0, "day": 13},  # semana 1
        {"item": "d", "value": 1.0, "day": 14},  # semana 2
    ]
    assert weekly_spending(purchases) == (1, 4.0)
