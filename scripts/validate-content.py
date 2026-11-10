"""Validate the current prototype content contract; optional live URL verification.

Production migration must replace this contract with src/content.config.ts (Zod),
not keep two independently maintained production schemas.
"""
from pathlib import Path
from datetime import datetime, date
from urllib.parse import urlsplit, urlunsplit
import argparse
import hashlib
import json
import re
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def normalized(url):
    p = urlsplit(url)
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip('/'), p.query, ''))

def fingerprint(item):
    return hashlib.sha256('\n'.join(sorted(normalized(s['url']) for s in item['sources'])).encode()).hexdigest()

def required_text(d, keys):
    for k in keys:
        assert isinstance(d.get(k),str) and d[k].strip(), f'missing text: {k}'

def stamp(v):
    value=datetime.fromisoformat(v.replace('Z','+00:00'))
    assert value.tzinfo is not None, f'timestamp needs timezone: {v}'
    return value

def run(check_links=False):
    allow=json.loads((ROOT/'config/sources.json').read_text())['allowedHosts']
    paths=sorted((ROOT/'content/days').glob('*.json'))
    assert paths, 'empty content must never be published'
    seen_ids, seen_fingerprints, urls, history = set(), set(), {}, []
    for path in paths:
        d=json.loads(path.read_text()); dt=path.stem
        assert date.fromisoformat(dt).isoformat()==d['date']
        assert d['schemaVersion']==1 and d['timezone']=='Asia/Shanghai'
        assert d['status'] in ('ready','degraded')
        required_text(d,('headline','short','lede','generatedAt'))
        assert stamp(d['window']['start']) < stamp(d['window']['end']) <= stamp(d['generatedAt'])
        assert d['window']['mode'] in ('scheduled','manual-backfill')
        if d['window']['mode']=='scheduled':
            assert (stamp(d['window']['end'])-stamp(d['window']['start'])).total_seconds()<=86400
        assert len(d['items'])>0
        assert [b['itemId'] for b in d['brief']]==[it['id'] for it in d['items']]
        assert all(isinstance(b['text'],str) and b['text'].strip() for b in d['brief'])
        assert isinstance(d['amendments'],list)
        for a in d['amendments']:
            required_text(a,('itemId','text','createdAt'))
            stamp(a['createdAt'])
            assert a['itemId'] in [it['id'] for it in d['items']]
        # HEAD is the publication baseline once committed. Only append amendments.
        old=subprocess.run(['git','show',f'HEAD:content/days/{dt}.json'],cwd=ROOT,capture_output=True,text=True)
        if old.returncode==0:
            before=json.loads(old.stdout)
            assert {k:v for k,v in d.items() if k!='amendments'}=={k:v for k,v in before.items() if k!='amendments'}, f'{dt}: published body changed'
            assert d['amendments'][:len(before['amendments'])]==before['amendments'], 'amendments must be append-only'
        for it in d['items']:
            required_text(it,('id','cat','title','verdict','why','event','caveat'))
            assert 3<=len(it['facts'])<=4 and all(isinstance(v,str) and v.strip() for v in it['facts'])
            assert 2<=len(it['scenes'])<=4 and all(isinstance(v,str) and v.strip() for v in it['scenes'])
            assert it['sources'], 'each item needs actual source URLs'
            assert it['id'] not in seen_ids, f'duplicate item ID {it["id"]}'
            fp=fingerprint(it)
            assert fp not in seen_fingerprints, f'duplicate source event: {it["title"]}'
            seen_ids.add(it['id']);seen_fingerprints.add(fp)
            for source in it['sources']:
                required_text(source,('url','title','publisher','publishedAt','publishedPrecision','checkedAt','verification'))
                u=urlsplit(source['url'])
                assert u.scheme=='https' and u.hostname in allow and u.path not in ('','/'), f'not an allowed article URL: {source["url"]}'
                assert u.username is None and u.password is None
                checked=stamp(source['checkedAt']);assert checked<=stamp(d['generatedAt'])
                if source['publishedPrecision']=='day':
                    pub=date.fromisoformat(source['publishedAt'])
                    assert stamp(d['window']['start']).date()<=pub<=stamp(d['window']['end']).date()
                else:
                    assert source['publishedPrecision']=='second'
                    assert stamp(d['window']['start'])<=stamp(source['publishedAt'])<=stamp(d['window']['end'])
                urls[source['url']]=source
            history.append(dict(date=dt,itemId=it['id'],fingerprint=fp,urls=sorted(normalized(v['url']) for v in it['sources'])))
        p=json.loads((ROOT/'content/projects'/f'{dt}.json').read_text())
        assert p['date']==dt and p['projects']
        for repo in p['projects']:
            required_text(repo,('name','oneline','problem','notFor','whyToday','whyWeek','license','collectedAt'))
            assert re.fullmatch(r'[\w.-]+/[\w.-]+',repo['name'])
            assert 2<=len(repo['scenes'])<=4
            assert repo['sources'] and all(urlsplit(v['url']).scheme=='https' for v in repo['sources'])
            for period in ('day','week'):
                metric=repo[period]
                assert type(metric['total']) is int and metric['total']>=0
                assert metric['delta'] is None or type(metric['delta']) is int
                if metric['delta'] is not None:
                    assert metric.get('baselineAt') and metric.get('baselineFile'), 'delta requires auditable baseline'
            snap=ROOT/'content/snapshots'/f'{dt}-{repo["name"].replace("/","--")}.json'
            evidence=json.loads(snap.read_text())
            assert evidence['stars']==repo['day']['total']==repo['week']['total']
            assert evidence['collectedAt']==repo['collectedAt']
        old_projects=subprocess.run(['git','show',f'HEAD:content/projects/{dt}.json'],cwd=ROOT,capture_output=True,text=True)
        if old_projects.returncode==0:
            assert json.loads(old_projects.stdout)==p, 'published project snapshot must not be rewritten'
    if check_links:
        for url,s in urls.items():
            # The article can be read by the Agent's web tool when this machine's TLS fails.
            # A failure here remains a failure; never treat a cached search as HTTP 200.
            try:
                with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'SIGNAL-source-check'}),timeout=25) as r:
                    assert r.status==200; r.read(512)
                print('REACHABLE',url)
            except Exception as exc:
                raise RuntimeError(f'Live URL check failed: {url}: {exc}. Verify full text with a browser; record result separately.') from exc
    return history

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check-links',action='store_true');parser.add_argument('--write-history',action='store_true');args=parser.parse_args()
    entries=run(args.check_links)
    target=ROOT/'content/history.json';value=dict(schemaVersion=1,entries=entries)
    if args.write_history:target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    else:assert json.loads(target.read_text())==value, 'history mismatch; review dedup then run --write-history'
    print(f'PASS: {len(entries)} items; required fields, source windows, dedup, immutability, project snapshots.')
