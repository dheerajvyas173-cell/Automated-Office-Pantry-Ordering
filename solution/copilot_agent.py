"""Merges the Copilot Studio agent packed by `pac copilot pack` (copilot-agent/PantrySupplyAssistant.zip)."""
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKED = os.path.join(ROOT, "copilot-agent", "PantrySupplyAssistant.zip")


def build():
    """Returns {zip path: content} for the agent's bots/ and botcomponents/ parts."""
    with zipfile.ZipFile(PACKED) as zf:
        return {name: zf.read(name) for name in zf.namelist()
                if name.startswith(("bots/", "botcomponents/")) and not name.endswith("/")}
