"""Canonical content adapter for the current static prototype (not the future Zod schema)."""
from pathlib import Path
from datetime import date
import json

ROOT = Path(__file__).resolve().parents[1]


def load_content():
    issues = {p.stem: json.loads(p.read_text()) for p in sorted((ROOT / 'content/days').glob('*.json'))}
    if not issues:
        raise ValueError('No real editions; demo-data.json must never be used as a publication fallback')
    dates = sorted(issues)
    today = dates[-1]
    raw_projects = json.loads((ROOT / 'content/projects' / f'{today}.json').read_text())['projects']

    # Published snapshots are immutable. Richer, iterable editorial profiles live in a
    # separate layer and are merged in by stable owner/repo identity.
    profile_path = ROOT / 'content/profiles' / f'{today}.json'
    profiles, editorial_note = {}, ''
    if profile_path.is_file():
        profile_doc = json.loads(profile_path.read_text())
        profiles = {p['name']: p for p in profile_doc['profiles']}
        editorial_note = profile_doc.get('editorialNote', '')

    snapshots = {}
    for path in (ROOT / 'content/snapshots').glob(f'{today}-*.json'):
        snap = json.loads(path.read_text())
        snapshots[snap['repo']] = snap

    # Same layering rule as profiles: decision-first reading advice is editorial
    # and iterable, keyed by issue date; the published edition body is untouched.
    decisions = {}
    for path in (ROOT / 'content/decisions').glob('*.json'):
        doc = json.loads(path.read_text())
        decisions[doc['date']] = doc

    # Keep the current renderer vocabulary private; stored fields use the editorial contract.
    projects = [
        {**p, **profiles.get(p['name'], {}), 'not': p['notFor'], 'why': p['whyToday']}
        for p in raw_projects
    ]
    wd = {dt: '周' + '一二三四五六日'[date.fromisoformat(dt).weekday()] for dt in dates}
    return dict(DATES=dates, ISSUES=issues, PROJECTS=projects, WD=wd,
                SNAPSHOTS=snapshots, EDITORIAL_NOTE=editorial_note,
                DECISIONS=decisions)
