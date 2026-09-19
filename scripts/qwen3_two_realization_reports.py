import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

OUT_DIR = _PROJECT_DIR / "research" / "contamination-bridge" / "qwen_embed"
REPORT_DIR = _PROJECT_DIR / "reports"


def main() -> int:
    d = json.loads((OUT_DIR / "two_realization_metrics.json").read_text(encoding="utf-8"))

    # Split the combined artifact into per-aspect reports.
    gate = {
        "reference_budget": d["reference_budget"],
        "baseline": d["baseline"],
        "verdict": d["verdict"],
        "gate_summary": d["gate_summary"],
        "realizations": {
            rid: {
                repo: {"gate": d["realizations"][rid]["repos"][repo]["gate"]}
                for repo in ("djangocms", "saleor")
            }
            for rid in ("A", "B")
        },
    }
    (REPORT_DIR / "qwen3_two_realization_gate.json").write_text(
        json.dumps(gate, indent=2), encoding="utf-8")

    (REPORT_DIR / "qwen3_two_realization_reproducibility.json").write_text(
        json.dumps(d["reproducibility"], indent=2), encoding="utf-8")

    print("verdict:", d["verdict"])
    print("wrote gate + reproducibility reports")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
