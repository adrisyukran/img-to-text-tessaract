import re
from dataclasses import asdict, dataclass

from jiwer import process_characters, process_words


@dataclass(frozen=True)
class TextMetrics:
    cer: float
    wer: float
    character_insertions: int
    character_deletions: int
    character_substitutions: int
    word_insertions: int
    word_deletions: int
    word_substitutions: int

    def as_dict(self) -> dict[str, float | int]:
        return asdict(self)


def normalize_for_evaluation(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\r\n", "\n").replace("\r", "\n")).strip()


def score_text(reference: str, hypothesis: str) -> TextMetrics:
    normalized_reference = normalize_for_evaluation(reference)
    normalized_hypothesis = normalize_for_evaluation(hypothesis)
    characters = process_characters(normalized_reference, normalized_hypothesis)
    words = process_words(normalized_reference, normalized_hypothesis)
    return TextMetrics(
        cer=float(characters.cer),
        wer=float(words.wer),
        character_insertions=int(characters.insertions),
        character_deletions=int(characters.deletions),
        character_substitutions=int(characters.substitutions),
        word_insertions=int(words.insertions),
        word_deletions=int(words.deletions),
        word_substitutions=int(words.substitutions),
    )
