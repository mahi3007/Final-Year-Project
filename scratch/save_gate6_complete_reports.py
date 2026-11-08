import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

from dsg_ctta.evaluation.paired_cluster_inference_v15 import (
    run_confirmatory_paired_cluster_inference_v15,
    FIVE_STRATUM_CONFIRMATORY_ACCENTS
)
from scripts.score_stage6m_cohort3_offline_gate6 import main as run_scoring

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def main():
    conf_report, speaker_records = run_scoring()
    
    # Save JSON report
    report_dict = conf_report.to_dict()
    report_dict["report_id"] = "STAGE6M-GATE6-OFFLINE-SCORING-REPORT"
    report_dict["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    report_dict["governing_authorization"] = "STAGE6M-GATE6-AUTH-DECISION-20261108"
    report_dict["evaluation_cohort_scale"] = {
        "total_clips": 16500,
        "total_speakers": 1100,
        "clips_per_speaker": 15,
        "total_reference_words": sum(s["wc"] for s in speaker_records),
        "confirmatory_strata": sorted(list(FIVE_STRATUM_CONFIRMATORY_ACCENTS))
    }
    
    json_path = Path("reports/stage6m/stage6m_gate6_offline_scoring_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2)
    print(f"Wrote JSON report to {json_path}")
    
    # Generate Output Catalogue
    cat = {
        "catalogue_id": "STAGE6M-GATE6-OUTPUT-CATALOGUE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifacts": {
            "stage6m_gate6_offline_scoring_report.json": {
                "rel_path": "reports/stage6m/stage6m_gate6_offline_scoring_report.json",
                "bytes": json_path.stat().st_size,
                "sha256": compute_sha256(json_path)
            }
        }
    }
    cat_path = Path("reports/stage6m/stage6m_gate6_output_catalogue.json")
    with open(cat_path, "w", encoding="utf-8") as f:
        json.dump(cat, f, indent=2)
    print(f"Wrote Output Catalogue to {cat_path}")

if __name__ == "__main__":
    main()
