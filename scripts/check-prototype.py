"""Check generated prototype links, fixture fidelity, resources and byte budgets."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
import xml.etree.ElementTree as ET
from content_data import load_content

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'prototype'

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.links, self.items = set(), [], 0
        self.feed(text)
    def handle_starttag(self, tag, pairs):
        a = dict(pairs)
        if 'id' in a:
            assert a['id'] not in self.ids, f'duplicate id: {a["id"]}'
            self.ids.add(a['id'])
        for key in ('href', 'src'):
            if key in a:
                self.links.append(a[key])
        if 'data-item' in a:
            self.items += 1

pages = {p.resolve(): Page(p.read_text()) for p in SITE.rglob('*.html')}
links = 0
for path, page in pages.items():
    for value in page.links:
        url = urlsplit(value)
        if url.scheme or url.netloc:
            continue
        target = (path.parent / unquote(url.path)).resolve() if url.path else path
        assert target.is_relative_to(SITE.resolve()), (path, value)
        assert target.is_file(), (path, 'missing file', value)
        if url.fragment:
            assert unquote(url.fragment) in pages[target].ids, (path, 'missing anchor', value)
        links += 1
fixture = load_content()
assert len(pages) == len(fixture['DATES']) + 5
for date, issue in fixture['ISSUES'].items():
    path = SITE / 'd' / f'{date}.html'
    assert pages[path.resolve()].items == len(issue['items'])
    text = path.read_text()
    for item in issue['items']:
        for field in ('facts', 'scenes'):
            for value in item[field]:
                from html import escape
                assert escape(value) in text, (date, value)
    assert (SITE / 'downloads' / f'{date}.md').is_file()
assert all(path.stat().st_size < 30 * 1024 for path in pages), 'HTML budget exceeded'
assert all('演示' not in path.read_text() for path in pages), 'demo leaked into published pages'
assert '127.0.0.1' not in (SITE/'feed.xml').read_text()
for dt,issue in fixture['ISSUES'].items():
    text=(SITE/'d'/f'{dt}.html').read_text()
    for item in issue['items']:
        for source in item['sources']:
            from html import escape
            assert escape(source['url'],quote=True) in text
assert (SITE/'app.js').stat().st_size < 15 * 1024
assert 'localStorage.setItem(\'signal:theme\'' in (SITE/'app.js').read_text()
ET.parse(SITE/'feed.xml')
calendar = (SITE/'daily.ics').read_text()
assert calendar.count('BEGIN:VEVENT') == 1 and 'RRULE:FREQ=DAILY;COUNT=7' in calendar and 'END:VCALENDAR' in calendar
assert 'sourceMappingURL' not in (SITE/'app.js').read_text()
print(f'PASS: {len(pages)} pages, {links} internal links/fragments, {len(fixture["DATES"])} complete editions, RSS/calendar, HTML/JS budgets.')
