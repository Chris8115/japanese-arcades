"""Check tracked files for local paths, private metadata, and accidental dev output.

Run before publishing: python scripts/check_public_repository.py
Reports filenames and issue categories only, never matching private values.
"""
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
HOME_PATH = re.compile(rb"(?i)(?:[a-z]:[\\/]+Users[\\/]+|/(?:home|Users)/)[^\\/\s]+")
CLIPBOARD_ID = re.compile(rb"codex-clipboard-[0-9a-f-]{36}", re.I)
KEY = re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")
TOKEN = re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[A-Z0-9]{16})")


def png_has_private_metadata(data):
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        return False
    offset = 8
    while offset + 12 <= len(data):
        size = struct.unpack('>I', data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        if kind in (b'tEXt', b'zTXt', b'iTXt', b'eXIf'):
            return True
        offset += size + 12
    return False


def main():
    paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    issues = []
    checked = 0
    for relative in filter(None, paths):
        path = ROOT / relative
        if not path.is_file():
            continue
        checked += 1
        if (relative.startswith(('build/', 'runs/', '.gradle/'))
                or path.suffix.lower() in ('.blend', '.blend1', '.blend2', '.bundle', '.pem', '.key', '.p12', '.pfx')
                or path.name == 'dev.local.json' or path.name == '.env'):
            issues.append((relative, 'local-only file'))
        data = path.read_bytes()
        if HOME_PATH.search(data):
            issues.append((relative, 'absolute user-directory path'))
        if CLIPBOARD_ID.search(data):
            issues.append((relative, 'local clipboard identifier'))
        if KEY.search(data) or TOKEN.search(data):
            issues.append((relative, 'credential-like content'))
        if png_has_private_metadata(data):
            issues.append((relative, 'PNG metadata; strip metadata without changing pixels'))

    emails = subprocess.check_output(
        ['git', 'log', '-1', '--format=%ae%n%ce'], cwd=ROOT).decode().splitlines()
    if any(not email.endswith('@users.noreply.github.com') for email in emails):
        issues.append(('HEAD', 'use a GitHub no-reply author/committer email'))
    for path, reason in issues:
        print(f'{path}: {reason}')
    print(f'Checked {checked} tracked files; {len(issues)} publication issues.')
    return bool(issues)


if __name__ == '__main__':
    sys.exit(main())
