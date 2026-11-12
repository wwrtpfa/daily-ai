#!/usr/bin/env python3
"""Re-runnable daily gate chain (docs/05 §5). Content authoring stays with the Agent.

Usage: python3 scripts/run-daily.py [--check-links]
Stops at the first failing gate; never rewrites published bodies by itself.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def gate(args):
    print(f'== {" ".join(args)}', flush=True)
    result = subprocess.run(args, cwd=ROOT)
    if result.returncode != 0:
        print(f'FAIL: gate exited {result.returncode}; fix content before retrying. Previous edition stays published.', flush=True)
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-links', action='store_true', help='also verify live source HTTP status')
    opts = parser.parse_args()
    py = sys.executable
    gate([py, 'scripts/validate-content.py', '--write-history'])
    gate([py, 'scripts/validate-content.py'])
    if opts.check_links:
        gate([py, 'scripts/validate-content.py', '--check-links'])
    gate([py, 'scripts/build-prototype.py'])
    gate([py, 'scripts/check-prototype.py'])
    gate(['node', '--check', 'prototype/app.js'])
    gate([py, 'scripts/test-content-validation.py'])
    print('PASS: all daily gates green. Review git diff, then commit chore(daily): <date> [skip ci].')


if __name__ == '__main__':
    main()