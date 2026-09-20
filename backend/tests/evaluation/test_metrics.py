from evaluation.metrics import normalize_for_evaluation, score_text


def test_metrics_are_zero_for_equivalent_whitespace():
    result = score_text("A clean\ninvoice", "A   clean invoice")
    assert result.cer == 0
    assert result.wer == 0


def test_metrics_count_a_single_character_substitution():
    result = score_text("invoice", "lnvoice")
    assert result.character_substitutions == 1
    assert result.cer == 1 / 7


def test_normalization_does_not_hide_case_or_punctuation():
    assert normalize_for_evaluation("A.\nB") == "A. B"
    assert score_text("A.", "a").cer > 0
