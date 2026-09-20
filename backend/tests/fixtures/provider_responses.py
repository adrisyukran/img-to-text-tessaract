import json


def correction_response() -> dict[str, object]:
    payload = {
        "proposals": [
            {
                "candidate_id": "candidate-1",
                "original_text": "lnvoice",
                "replacement_text": "Invoice",
                "rationale": "Common OCR confusion.",
                "confidence": 0.98,
            }
        ]
    }
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(payload),
                }
            }
        ]
    }


def gemini_correction_response() -> dict[str, object]:
    payload = correction_response()["choices"][0]["message"]["content"]
    return {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": payload}],
                }
            }
        ]
    }
