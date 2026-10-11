"""Packs the canvas app (shell/ + Src/*.pa.yaml) into PantrySupplyOrdering.msapp using the Power Platform CLI.

Run: PAC=/path/to/pac python3 power-apps/canvas-app/build_msapp.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(HERE, "PantrySupplyOrdering.msapp")


def main():
    pac = os.environ.get("PAC", "pac")
    with tempfile.TemporaryDirectory() as work:
        sources = os.path.join(work, "app")
        shutil.copytree(os.path.join(HERE, "Src"), os.path.join(sources, "Src"))
        with zipfile.ZipFile(os.path.join(sources, "PantrySupplyOrdering.msapr"), "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("msapr-header.json", json.dumps({
                "MsaprStructureVersion": "0.1",
                "UnpackedConfiguration": {"ContentTypes": ["PaYamlSourceCode"]},
            }, indent=2))
            shell = os.path.join(HERE, "shell")
            for folder, _, files in os.walk(shell):
                for name in files:
                    path = os.path.join(folder, name)
                    zf.write(path, "msapp/" + os.path.relpath(path, shell).replace(os.sep, "/"))
        result = subprocess.run(
            [pac, "canvas", "pack", "--sources", sources, "--msapp", OUTPUT, "--layout", "SourceCode", "--overwrite"],
            capture_output=True, text=True)
        print(result.stdout, result.stderr)
        if result.returncode != 0 or "Packing succeeded" not in result.stdout:
            sys.exit(1)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
