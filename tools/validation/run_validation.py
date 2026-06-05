"""
run_validation.py
=================
Runs every standalone (non-Maya) validation script as a subprocess,
aggregates exit codes, and exits 0 when all pass or 1 when any fail.

Scripts that require a live Maya / mayapy runtime are listed under
MAYAPY_ONLY and are not executed here; run them manually inside Maya
or via mayapy as documented in docs/testing/manual_test_checklist.md.
"""
import subprocess
import sys
from pathlib import Path

VALIDATION_DIR = Path(__file__).resolve().parent

STANDALONE_SCRIPTS = [
    "test23_report_path_validation.py",
    "test24_runresult_validation.py",
    "test25_ui_reporter_decoupling_validation.py",
    "test26_mel_bridge_validation.py",
    "test28_report_failure_signaling_validation.py",
    "test29_phase8a_group_creation_validation.py",
    "test30_phase8b_failed_parenting_validation.py",
]

MAYAPY_ONLY = [
    "test01_test02_maya_smoke_validation.py",
    "test03_scope_scanning_maya_validation.py",
    "test06_dry_run_production_mesh_validation.py",
    "test08_ignore_string_maya_validation.py",
    "test09_material_review_maya_validation.py",
    "test10_12_13_protected_content_maya_validation.py",
    "test11_selected_child_reference_maya_validation.py",
    "test14_scene_utilities_maya_validation.py",
    "test15_duplicate_long_names_maya_validation.py",
    "test17_parent_child_selected_maya_validation.py",
    "test19_leaf_reclassification_maya_validation.py",
    "test20_unclear_case_maya_validation.py",
]


def main():
    results = []
    for script_name in STANDALONE_SCRIPTS:
        script_path = VALIDATION_DIR / script_name
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        passed = proc.returncode == 0
        results.append((script_name, passed))
        print("{0}  {1}".format("PASS" if passed else "FAIL", script_name))
        if not passed and proc.stderr.strip():
            for line in proc.stderr.strip().splitlines():
                print("    {0}".format(line))

    failed = [name for name, passed in results if not passed]
    print()
    if failed:
        print("FAILED {0}/{1}: {2}".format(
            len(failed), len(results), ", ".join(failed),
        ))
        print()
        print("Skipped (mayapy only): {0}".format(len(MAYAPY_ONLY)))
        sys.exit(1)

    print("ALL PASS {0}/{0}".format(len(results)))
    print()
    print("Skipped (mayapy only): {0}".format(len(MAYAPY_ONLY)))
    sys.exit(0)


if __name__ == "__main__":
    main()
