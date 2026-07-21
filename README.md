# RedBeaver

A small, dependency-free Python script that generates a blank engagement
folder/file skeleton for a pentest / red team activity. Run it once per
activity, then copy the vulnerability template folder for every finding you
discover.

## Requirements

- Python 3.8+ (no third-party packages required)
- Windows, Linux or macOS

## Quick start

```bash
python redbeaver.py
```

The script will ask three questions. Press Enter on any of them to accept
the default shown in brackets:

```
Client name [Client_Name]:
Activity number [01]:
Activity type/name [Activity_Type]:
```

It then creates the structure inside the current directory:

```
Client_Name/
└── 01_Activity_Type/
    ├── README.md
    ├── Information_Gathering/
    │   ├── Service_Enumeration/
    │   │   ├── HTTP/
    │   │   ├── SSH/
    │   │   ├── FTP/
    │   │   ├── SMB/
    │   │   ├── RDP/
    │   │   ├── SNMP/
    │   │   └── DNS/
    │   ├── Authentication/
    │   │   ├── found-credentials.txt
    │   │   ├── password-policy.txt
    │   │   └── other.txt
    │   ├── Automated_Scans/
    │   │   ├── nuclei/
    │   │   └── nmap/
    │   └── Other/
    └── Vulnerabilities/
        └── _Vuln_Template/
            ├── Discovery/
            ├── Verification/
            ├── Impact/
            └── notes.md
```

## Non-interactive usage

Useful for scripting, batch files, or generating several activities at once
without typing anything.

```bash
python redbeaver.py --client "Acme Corp" --activity-number 02 --activity-name "External Pentest"
```

### CLI flags

| Flag                | Description                                             | Default              |
|----------------------|----------------------------------------------------------|-----------------------|
| `--client`           | Client name                                              | prompts interactively |
| `--activity-number`  | Activity number (e.g. `01`, `02`)                        | prompts interactively |
| `--activity-name`    | Activity type/name (e.g. `Internal Pentest`)             | prompts interactively |
| `--output-dir`       | Directory in which the `Client_Name` folder is created   | current directory     |

Any flag you omit falls back to an interactive prompt (which itself falls
back to the default value on Enter), so you can mix and match, e.g. supply
`--client` on the command line and get prompted only for the rest.

If the target activity folder already exists and is not empty, the script
warns you and asks for confirmation before writing into it, so you won't
accidentally merge two unrelated runs by mistake.

## Adding a new vulnerability

`Vulnerabilities/_Vuln_Template/` is a blank template, not a real finding.
For every vulnerability you discover:

1. Copy `_Vuln_Template` into a new folder under `Vulnerabilities/`.
2. Rename it to the vulnerability name (e.g. `Reflected_XSS_Login_Form`).
3. Fill in `notes.md` and drop evidence into `Discovery/`, `Verification/`
   and `Impact/`.

Evidence files should follow a `<step>-<description>.<ext>` naming
convention so the order of actions is obvious at a glance, e.g.:

```
01-login-page.png
02-user-a-request.txt
03-sqlmap-output.txt
```

## Customizing the template

Everything you're likely to want to change lives in one config block near
the top of `redbeaver.py` — no need to touch the rest of the script.

### Add a tool to Automated_Scans

```python
AUTOMATED_SCAN_TOOLS = [
    "nuclei",
    "nmap",
    "ffuf",          # <- just add a new entry
]
```

### Add/remove a protocol under Service_Enumeration

```python
SERVICE_ENUMERATION_PROTOCOLS = [
    "HTTP",
    "SSH",
    "FTP",
    "SMB",
    "RDP",
    "SNMP",
    "DNS",
    "LDAP",          # <- just add a new entry
]
```

### Add a brand new top-level section

Sections are defined in `build_structure()` as a nested dict. Each level
supports:

- `"_dirs": [names...]` — plain empty subfolders
- `"_files": {filename: content}` — files, optionally pre-filled with text
- any other key — a nested subfolder, recursed into with the same rules

Example: adding a `Reporting/` section as a sibling of
`Information_Gathering` and `Vulnerabilities`:

```python
def build_structure() -> dict:
    return {
        "Information_Gathering": { ... },
        "Vulnerabilities": { ... },
        "Reporting": {
            "_dirs": ["Drafts", "Final"],
        },
    }
```

### Change default values

```python
DEFAULT_CLIENT_NAME = "Client_Name"
DEFAULT_ACTIVITY_NUMBER = "01"
DEFAULT_ACTIVITY_NAME = "Activity_Type"
```

### Change the vuln template's subfolders or notes.md content

```python
VULN_SUBFOLDERS = ["Discovery", "Verification", "Impact"]

VULN_NOTES_TEMPLATE = """# {vuln_name}

## Summary
...
"""
```

## Notes on folder/file naming

Windows doesn't allow the characters `< > : " / \ | ? *` in file or folder
names. Whatever you type for the client name or activity name is
automatically stripped of these characters before folders are created, so
you don't need to sanitize input yourself.

## Possible extensions (not implemented)

- A flag to auto-create a named vulnerability folder from
  `_Vuln_Template` (e.g. `--new-vuln "Reflected XSS"`) instead of copying it
  by hand.
- Loading the config block from an external JSON/YAML file instead of
  editing the Python script directly, for sharing presets across a team.
- Auto-initializing a git repo in the activity folder for change tracking.
