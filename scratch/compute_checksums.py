import hashlib
from pathlib import Path

PROJECT_ROOT = Path("c:/Users/venka/Downloads/final year project main")

def sha256_of_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

files_to_check = [
    PROJECT_ROOT / "reports" / "stage6m" / "stage6m_data_feasibility_audit.md",
    PROJECT_ROOT / "reports" / "stage6m" / "stage6m_protocol_proposal.md",
    PROJECT_ROOT / "reports" / "stage6m" / "stage6m_v1_2_0_changelog.md",
    PROJECT_ROOT / "scripts" / "update_stage6m_reports.py",
    PROJECT_ROOT / "reports" / "stage6m" / "test_execution_research_validity_full.log",
    PROJECT_ROOT / "reports" / "stage6m" / "test_execution_stage6m_proposal.log",
    # Untouched baseline files
    PROJECT_ROOT / "reports" / "stage6m" / "stage6m_power_analysis.md",
    PROJECT_ROOT / "reports" / "stage6m" / "stage6m_data_integrity_audit.md",
    PROJECT_ROOT / "reports" / "stage6m" / "stage6m_sample_size_decision.md",
    PROJECT_ROOT / "reports" / "stage6m" / "stage6m_signoff_checklist.md",
    PROJECT_ROOT / "reports" / "stage6m" / "stage6m_temporal_estimands.md",
    PROJECT_ROOT / "reports" / "stage6m" / "stage6m_replay_vault_spec.md",
    PROJECT_ROOT / "reports" / "stage6m" / "power_simulation_results.json",
    PROJECT_ROOT / "reports" / "stage5" / "external_speaker_inventory.csv",
    PROJECT_ROOT / "datasets" / "splits" / "stage5_external_eval.csv",
    PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel.csv",
    PROJECT_ROOT / "datasets" / "splits" / "stage5_sentinel_panel_manifest.json",
    PROJECT_ROOT / "datasets" / "splits" / "stage4_characterization.csv",
    PROJECT_ROOT / "datasets" / "splits" / "calibration.csv",
    PROJECT_ROOT / "datasets" / "external" / "common_voice_27" / "validated.tsv",
]

for p in files_to_check:
    if p.exists():
        size = p.stat().st_size
        h = sha256_of_file(p)
        rel = p.relative_to(PROJECT_ROOT)
        print(f"{rel} | {size} bytes | {h}")
    else:
        print(f"MISSING: {p}")
