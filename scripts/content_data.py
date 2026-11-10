"""Canonical content adapter for the current static prototype (not the future Zod schema)."""
from pathlib import Path
from datetime import date
import json

ROOT = Path(__file__).resolve().parents[1]

def load_content():
    issues = {p.stem: json.loads(p.read_text()) for p in sorted((ROOT/'content/days').glob('*.json'))}
    if not issues:
        raise ValueError('No real editions; demo-data.json must never be used as a publication fallback')
    dates = sorted(issues)
    projects = json.loads((ROOT/'content/projects'/f'{dates[-1]}.json').read_text())['projects']
    # Keep the current renderer vocabulary private; stored fields use the editorial contract.
    projects = [{**p, 'not': p['notFor'], 'why': p['whyToday']} for p in projects]
    wd = {dt: '周'+'一二三四五六日'[date.fromisoformat(dt).weekday()] for dt in dates}
    return dict(DATES=dates, ISSUES=issues, PROJECTS=projects, WD=wd)
