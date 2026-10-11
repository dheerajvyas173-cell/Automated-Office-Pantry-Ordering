"""Packs the Copilot Studio agent workspace into PantrySupplyAssistant.zip using the Power Platform CLI.

Run: PAC=/path/to/pac python3 copilot-agent/build_agent.py
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(HERE, "PantrySupplyAssistant.zip")


def main():
    pac = os.environ.get("PAC", "pac")
    with tempfile.TemporaryDirectory() as out:
        result = subprocess.run(
            [pac, "copilot", "pack", "--publisher-prefix", "cr",
             "--project-dir", os.path.join(HERE, "workspace"),
             "--solution-name", "PantrySupplyAssistant", "--output-path", out],
            capture_output=True, text=True)
        print(result.stdout, result.stderr)
        packed = [f for f in os.listdir(out) if f.endswith(".zip")]
        if result.returncode != 0 or len(packed) != 1:
            sys.exit(1)
        shutil.copyfile(os.path.join(out, packed[0]), OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
