"""
Derive which speech sounds (phonemes) need practice from pronunciation metrics.
"""
from typing import Any, Dict, List, Tuple


# Phoneme scores at or below this threshold are flagged for extra practice
PHONEME_PRACTICE_THRESHOLD = 75.0


def _collect_phoneme_averages(metrics: List[dict]) -> Dict[str, float]:
    phoneme_scores: Dict[str, List[float]] = {}
    for m in metrics or []:
        for word in m.get("phoneme_scores") or []:
            for p in word.get("phonemes") or []:
                ph = str(p.get("phoneme", "")).strip()
                if not ph:
                    continue
                try:
                    score = float(p.get("score", 0))
                except (TypeError, ValueError):
                    continue
                phoneme_scores.setdefault(ph, []).append(score)
    return {ph: sum(vals) / len(vals) for ph, vals in phoneme_scores.items()}


def analyze_sound_focus(metrics: List[dict]) -> Dict[str, Any]:
    """
    Returns:
      all_good: bool
      practice_sounds: list of phoneme symbols (worst first), capped for readability
      summary_line: short line for UI
      detail_paragraph: longer text for PDF
    """
    averages = _collect_phoneme_averages(metrics)

    if not averages:
        # No phoneme-level data — fall back to aggregate pronunciation skill
        if not metrics:
            return {
                "all_good": True,
                "practice_sounds": [],
                "summary_line": "No pronunciation recordings were analyzed.",
                "detail_paragraph": "No phoneme-level scores were available for this session.",
            }
        try:
            avg_p = sum(float(m.get("pronunciation", 0) or 0) for m in metrics) / len(metrics)
        except Exception:
            avg_p = 0.0
        if avg_p >= 80:
            return {
                "all_good": True,
                "practice_sounds": [],
                "summary_line": "Overall pronunciation looks strong — keep practicing all sounds!",
                "detail_paragraph": (
                    "Phoneme-level detail was not available; overall pronunciation score is strong. "
                    "Continue balanced practice across vowels and consonants."
                ),
            }
        return {
            "all_good": False,
            "practice_sounds": [],
            "summary_line": "Overall pronunciation could use more practice across several sounds.",
            "detail_paragraph": (
                "Detailed phoneme scores were not returned for this session; "
                "the overall pronunciation score suggests continued practice with clear articulation "
                "and listening to model speech."
            ),
        }

    weak = [(ph, sc) for ph, sc in averages.items() if sc < PHONEME_PRACTICE_THRESHOLD]
    weak.sort(key=lambda x: x[1])

    if not weak:
        return {
            "all_good": True,
            "practice_sounds": [],
            "summary_line": "All measured sounds are on track — great job!",
            "detail_paragraph": (
                "Based on phoneme scores across the read-aloud sentences, every sound measured "
                f"met or exceeded our practice target ({int(PHONEME_PRACTICE_THRESHOLD)}+). "
                "No specific sounds need extra focus right now."
            ),
        }

    practice = [ph for ph, _ in weak[:12]]
    worst_labels = ", ".join(f"{ph} ({int(round(averages[ph]))})" for ph in practice[:8])
    if len(practice) > 8:
        worst_labels += ", …"

    return {
        "all_good": False,
        "practice_sounds": practice,
        "summary_line": f"Focus extra practice on: {', '.join(practice[:6])}"
        + (" …" if len(practice) > 6 else ""),
        "detail_paragraph": (
            "Based on average scores for each speech sound (phoneme) in your recordings, "
            f"these sounds scored below {int(PHONEME_PRACTICE_THRESHOLD)} and deserve targeted practice: "
            f"{worst_labels}. "
            "Try minimal-pair listening, slow repetition, and mirroring a clear model for these sounds."
        ),
    }
