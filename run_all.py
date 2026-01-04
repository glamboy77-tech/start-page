import os
import sys
import subprocess
from pathlib import Path

"""
Orchestrates the full chart update:
1) Runs ChartScanner pipeline (captures PNGs and converts to JSON via Gemini) -> homepage/data
2) Runs homepage/trends_engine.py to refresh rank_data.js
"""

ROOT = Path(__file__).resolve().parent
CHARTSCANNER_DIR = ROOT / "ChartScanner"
HOMEPAGE_DIR = ROOT / "homepage"
OUTPUT_DIR = HOMEPAGE_DIR / "data"

CHART_PIPELINE_JS = CHARTSCANNER_DIR / "scripts" / "chart_pipeline.js"
TRENDS_ENGINE_PY = HOMEPAGE_DIR / "trends_engine.py"

EXPECTED_JSONS = [
    "shazam_viral_korea.json",
    "shazam_viral_global.json",
    "youtube_shorts_korea.json",
    "youtube_shorts_global.json",
]


def run(cmd, cwd=None):
    print(f"\n[run_all] Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def ensure_paths():
    if not CHART_PIPELINE_JS.exists():
        raise FileNotFoundError(f"Missing chart_pipeline.js at {CHART_PIPELINE_JS}")
    if not TRENDS_ENGINE_PY.exists():
        raise FileNotFoundError(f"Missing trends_engine.py at {TRENDS_ENGINE_PY}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    ensure_paths()

    # 1) Run ChartScanner pipeline (Node -> Python -> Gemini)
    run(["node", str(CHART_PIPELINE_JS)], cwd=CHARTSCANNER_DIR)

    # Optional: sanity check for expected JSON outputs
    missing = [name for name in EXPECTED_JSONS if not (OUTPUT_DIR / name).exists()]
    if missing:
        print(f"[run_all] WARNING: Missing JSON files after pipeline: {missing}")

    # 2) Run trends_engine.py to refresh aggregated rank_data
    run([sys.executable, str(TRENDS_ENGINE_PY)], cwd=HOMEPAGE_DIR)

    print("\n[run_all] Done.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"[run_all] Command failed with exit code {e.returncode}: {e}")
        sys.exit(e.returncode)
    except Exception as e:
        print(f"[run_all] Error: {e}")
        sys.exit(1)
