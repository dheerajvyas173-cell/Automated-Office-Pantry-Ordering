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


def pack(src_dir=os.path.join(HERE, "Src"), output=OUTPUT, properties=None, replace=None):
    """Packs src_dir (*.pa.yaml) with the shell.

    `properties` overrides keys in shell/Properties.json; `replace` maps shell paths to new file content.
    """
    replace = replace or {}
    pac = os.environ.get("PAC", "pac")
    with tempfile.TemporaryDirectory() as work:
        sources = os.path.join(work, "app")
        shutil.copytree(src_dir, os.path.join(sources, "Src"))
        with zipfile.ZipFile(os.path.join(sources, "PantrySupplyOrdering.msapr"), "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("msapr-header.json", json.dumps({
                "MsaprStructureVersion": "0.1",
                "UnpackedConfiguration": {"ContentTypes": ["PaYamlSourceCode"]},
            }, indent=2))
            shell = os.path.join(HERE, "shell")
            for folder, _, files in os.walk(shell):
                for name in files:
                    path = os.path.join(folder, name)
                    arcname = "msapp/" + os.path.relpath(path, shell).replace(os.sep, "/")
                    if arcname[len("msapp/"):] in replace:
                        zf.writestr(arcname, replace[arcname[len("msapp/"):]])
                    elif arcname == "msapp/Properties.json" and properties:
                        with open(path) as f:
                            props = json.load(f)
                        props.update(properties)
                        zf.writestr(arcname, json.dumps(props, indent=2))
                    else:
                        zf.write(path, arcname)
        result = subprocess.run(
            [pac, "canvas", "pack", "--sources", sources, "--msapp", output, "--layout", "SourceCode", "--overwrite"],
            capture_output=True, text=True)
        print(result.stdout, result.stderr)
        if result.returncode != 0 or "Packing succeeded" not in result.stdout:
            sys.exit(1)
    print(f"Wrote {output}")


if __name__ == "__main__":
    pack()
