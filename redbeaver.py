#!/usr/bin/env python3
"""
RedBeaver
=========
Generates a blank engagement folder/file skeleton for a pentest/red team
activity, ready to be filled in as findings come up.

Usage (interactive):
    python redbeaver.py

Usage (non-interactive, e.g. from another script or a batch file), creates
a single activity numbered 01:
    python redbeaver.py --client "Acme Corp" --activity-name "Internal Pentest"

Run "python redbeaver.py -h" for all options.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# =====================================================================
# USER CONFIGURATION - edit this section to customize the template.
# No need to touch anything below unless you want to change the tool's
# core logic.
# =====================================================================

# Protocol/service subfolders under Information_Gathering/Service_Enumeration.
# Kept to a single example entry on purpose - add your own protocols here
# following the same naming pattern (e.g. "SSH", "SMB", "LDAP", ...).
SERVICE_ENUMERATION_PROTOCOLS = [
    "HTTP",
]

# Tool subfolders under Information_Gathering/Automated_Scans
# Just add/remove strings here to change what gets created.
AUTOMATED_SCAN_TOOLS = [
    "nuclei",
    "nmap",
]

# Empty text files created under Information_Gathering/Authentication
AUTHENTICATION_FILES = {
    "found-credentials.txt": "",
    "password-policy.txt": "",
    "other.txt": "",
}

# Hosts under Information_Gathering/Local_Enumeration, each gets its own
# folder with a notes.md file. Use this to keep track of enumeration
# performed on compromised local systems (one folder per host).
LOCAL_ENUMERATION_HOSTS = [
    "Host1",
]

# Content of each host's notes.md under Local_Enumeration. {host_name} is
# substituted automatically.
LOCAL_ENUMERATION_NOTES_TEMPLATE = """# {host_name} - Local Enumeration

## System Info


## Users & Privileges


## Network


## Installed Software / Services


## Interesting Findings

"""

# Name of the placeholder vulnerability folder created under Vulnerabilities/.
# Copy-paste this folder and rename it for every new finding.
VULN_TEMPLATE_FOLDER_NAME = "Vuln_Template"

# Mock/example evidence files dropped directly into the vuln template
# folder, illustrating the "<Step>-<Description>.<ext>" naming convention.
# Remove or add entries here if you want different examples.
VULN_EXAMPLE_FILES = [
    "<Step>-<Description>.<ext>",
    "01-login-page.png",
    "02-user-a-request.txt",
]

# Default values used when the user just presses Enter
DEFAULT_CLIENT_NAME = "Client_Name"
DEFAULT_ACTIVITY_NAME = "Activity_Type"
DEFAULT_OUTPUT_DIR = "."

# Content of notes.md inside the vulnerability template. {vuln_name} is
# substituted automatically.
VULN_NOTES_TEMPLATE = """# {vuln_name}

## Summary


## CVSS Score
- Vector:
- Score:

## Affected Assets


## Steps to Reproduce


## Impact


## Remediation


## References

"""

# =====================================================================
# CORE LOGIC - shouldn't normally need editing.
# =====================================================================

# Characters not allowed in Windows file/folder names.
_INVALID_CHARS_RE = re.compile(r'[<>:"/\\|?*]')


def sanitize_name(name: str) -> str:
    """Strip characters that Windows doesn't allow in file/folder names."""
    cleaned = _INVALID_CHARS_RE.sub("", name).strip().rstrip(".")
    return cleaned or "Unnamed"


def prompt(question: str, default: str) -> str:
    """Ask a question on the terminal, returning `default` on empty input."""
    answer = input(f"{question} [{default}]: ").strip()
    return answer if answer else default


def _build_local_enumeration_section() -> dict:
    """Builds the Local_Enumeration/<Host>/notes.md section."""
    return {
        host: {
            "_files": {
                "notes.md": LOCAL_ENUMERATION_NOTES_TEMPLATE.format(host_name=host)
            }
        }
        for host in LOCAL_ENUMERATION_HOSTS
    }


def build_structure() -> dict:
    """
    Builds the folder/file spec as a nested dict.

    Format:
      - "_dirs": [names...]          -> plain empty subfolders
      - "_files": {name: content}    -> files with (optional) content
      - any other key -> nested dict, recursed into as a subfolder

    Add a new top-level section (a sibling of Information_Gathering /
    Vulnerabilities) by simply adding another key to the returned dict.
    """
    return {
        "Information_Gathering": {
            "_dirs": ["Other"],
            "Service_Enumeration": {
                "_dirs": SERVICE_ENUMERATION_PROTOCOLS,
            },
            "Authentication": {
                "_files": AUTHENTICATION_FILES,
            },
            "Automated_Scans": {
                "_dirs": AUTOMATED_SCAN_TOOLS,
            },
            "Local_Enumeration": _build_local_enumeration_section(),
        },
        "Vulnerabilities": {
            VULN_TEMPLATE_FOLDER_NAME: {
                "_files": {
                    "notes.md": VULN_NOTES_TEMPLATE.format(
                        vuln_name=VULN_TEMPLATE_FOLDER_NAME
                    ),
                    **{name: "" for name in VULN_EXAMPLE_FILES},
                },
            },
        },
        # Add more top-level sections here if needed, e.g.:
        # "Reporting": {"_dirs": ["Drafts", "Final"]},
    }


def create_from_spec(base: Path, spec: dict) -> None:
    """Recursively creates folders/files under `base` from `spec`."""
    for dirname in spec.get("_dirs", []):
        (base / sanitize_name(dirname)).mkdir(parents=True, exist_ok=True)

    for filename, content in spec.get("_files", {}).items():
        file_path = base / sanitize_name(filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            file_path.write_text(content, encoding="utf-8")

    for key, value in spec.items():
        if key in ("_dirs", "_files"):
            continue
        sub = base / sanitize_name(key)
        sub.mkdir(parents=True, exist_ok=True)
        create_from_spec(sub, value)


def print_tree(root: Path, prefix: str = "") -> None:
    """Prints a simple ASCII tree of the generated structure."""
    entries = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        print(f"{prefix}{connector}{entry.name}{'/' if entry.is_dir() else ''}")
        if entry.is_dir():
            extension = "    " if i == len(entries) - 1 else "│   "
            print_tree(entry, prefix + extension)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RedBeaver - generate a blank pentest activity folder structure."
    )
    parser.add_argument("--client", help="Client name")
    parser.add_argument(
        "--activity-name",
        help="Activity type/name. If given, a single activity (numbered 01) "
        "is created non-interactively and the 'add another activity?' "
        "prompt is skipped.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory in which the Client_Name folder is created "
        "(default: current directory). If omitted, you'll be prompted for it.",
    )
    return parser.parse_args()


def create_activity(client_path: Path, activity_number: int, activity_name: str) -> Path:
    """Creates a single numbered activity folder with the full structure."""
    activity_folder = sanitize_name(f"{activity_number:02d}_{activity_name}")
    activity_path = client_path / activity_folder

    if activity_path.exists() and any(activity_path.iterdir()):
        print(f"\nWarning: '{activity_path}' already exists and is not empty.")
        confirm = input("Continue and merge into it? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Skipped.")
            return activity_path

    activity_path.mkdir(parents=True, exist_ok=True)
    create_from_spec(activity_path, build_structure())

    print(f"\nStructure created at:\n{activity_path}\n")
    print_tree(activity_path)
    return activity_path


def main() -> None:
    args = parse_args()

    print("=== RedBeaver - Activity Structure Generator ===\n")

    client_name = args.client or prompt("Client name", DEFAULT_CLIENT_NAME)

    output_dir = (
        args.output_dir
        if args.output_dir is not None
        else prompt("Output directory", DEFAULT_OUTPUT_DIR)
    )
    client_path = Path(output_dir).resolve() / sanitize_name(client_name)

    if args.activity_name:
        # Non-interactive: create exactly one activity, numbered 01.
        create_activity(client_path, 1, args.activity_name)
    else:
        # Interactive: keep asking for activities until the user says no.
        activity_number = 1
        while True:
            ordinal = "first" if activity_number == 1 else f"#{activity_number}"
            activity_name = prompt(
                f"Name of activity {ordinal}",
                f"{DEFAULT_ACTIVITY_NAME}_{activity_number}",
            )
            create_activity(client_path, activity_number, activity_name)

            again = input("\nAdd another activity? [y/N]: ").strip().lower()
            if again != "y":
                break
            activity_number += 1

    print(
        f"\nDone. Copy '{VULN_TEMPLATE_FOLDER_NAME}' under each activity's "
        "Vulnerabilities/ folder and rename it for every finding."
    )


if __name__ == "__main__":
    main()
