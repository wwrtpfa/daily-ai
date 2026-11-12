"""Rebuild the zero-dependency static prototype from canonical daily content and design tokens."""
from pathlib import Path
from html import escape as esc
import json
import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import date as calendar_date, timedelta
from content_data import load_content

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'prototype'
DATA = load_content()
TOKENS = json.loads((ROOT / 'config/design-tokens.json').read_text())
DATES, ISSUES, PROJECTS = DATA['DATES'], DATA['ISSUES'], DATA['PROJECTS']
SNAPSHOTS, EDITORIAL_NOTE = DATA['SNAPSHOTS'], DATA['EDITORIAL_NOTE']
DECISIONS = DATA['DECISIONS']
TODAY = DATES[-1]
SITE_CONFIG = json.loads((ROOT/'config/site.json').read_text())


def plain(value):
    return re.sub('<[^>]+>', '', value)


def marked(value):
    # Only the fixture's four mark classes are allowed through.
    safe = esc(value)
    for name in ('m1', 'm2', 'm3', 'm4'):
        safe = safe.replace(esc(f'<mark class="{name}">'), f'<mark class="{name}">')
    return safe.replace(esc('</mark>'), '</mark>')


def slug(value):
    return re.sub('[^a-z0-9]+', '-', value.lower()).strip('-')


def token_css():
    names = {'background': 'bg', 'text': 'ink', 'secondary': 'secondary', 'muted': 'muted', 'accent': 'accent', 'highlight': 'hl', 'alternate': 'hl2', 'line': 'line', 'backdrop': 'backdrop', 'surface': 'surface', 'rail': 'rail', 'railText': 'rail-text', 'railMuted': 'rail-muted', 'railActive': 'rail-active'}
    result = []
    for theme, colors in TOKENS['color'].items():
        selector = ':root' if theme == 'light' else '[data-theme=dark]'
        result.append(selector + '{' + ''.join(f'--{names[key]}:{value};' for key, value in colors.items()) + '}')
    for theme, materials in TOKENS['material'].items():
        selector = ':root' if theme == 'light' else '[data-theme=dark]'
        result.append(selector + '{' + ''.join('--' + re.sub(r'([A-Z])', lambda m: '-' + m[1].lower(), key) + ':' + value + ';' for key,value in materials.items()) + '}')
    typo, layout = TOKENS['typography'], TOKENS['layout']
    result.append(':root{' + ''.join(f'--{key}:{typo[key]}px;' for key in ('hero', 'title', 'body', 'meta')) + f'--leading:{typo["lineHeight"]};--reading:{layout["readingWidth"]}px;--shell:{layout["shellWidth"]}px;--section-gap:{layout["sectionGap"]}px;--item-gap:{layout["itemGap"]}px;' + '}')
    result.append(':root{--art-bg:' + TOKENS['art']['background'] + ';}')
    return '\n'.join(result) + '\n'


def link(url, label, cls=''):
    return f'<a class="{cls}" href="{esc(url, quote=True)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'


def period_links(prefix, date=None):
    return '<div class="period-list" aria-label="刊期">' + ''.join(f'<a href="{prefix}d/{dt}.html" {"aria-current=date" if dt == date else ""}>{dt[5:].replace("-", ".")}</a>' for dt in DATES) + '</div>'


def footer(prefix, date):
    return f'''<footer class="foot reading">{period_links(prefix, date)}
    <div class="foot-top"><span>信号 SIGNAL · 每日 AI / 每日 GitHub</span><div class="foot-links"><a href="{prefix}status.html">出刊状态</a><a href="{prefix}feed.xml">RSS</a><button class="js-only inline" data-action="theme" aria-label="切换深浅主题">切换主题</button></div></div>
    <p class="disclaimer">SIGNAL v0.6 · 官方来源编纂，统计为采集时快照。无账号，浏览选择不保存。</p></footer>'''


def dialog():
    return '''<dialog id="share-dialog" aria-labelledby="share-title"><div class="dialog-head"><h2 id="share-title">带走这一期</h2><button data-action="close-share" aria-label="关闭分享预览">关闭</button></div>
    <div class="dialog-body"><p class="dialog-help">选择要带走的内容，生成图片或复制文字。仅本次浏览有效。</p><div class="share-layout"><fieldset class="share-options" id="share-options"><legend>选择内容</legend></fieldset><figure class="share-preview"><canvas id="share-canvas" aria-label="所选内容分享图片"></canvas><figcaption>本期内容 · 本地生成</figcaption></figure></div>
    <p class="dialog-feedback" id="share-feedback" role="status"></p><textarea id="copy-fallback" class="copy-fallback" aria-label="可手动复制的分享文字" hidden readonly></textarea>
    <div class="dialog-actions"><button data-action="download">下载 PNG</button><button data-action="copy">复制文字</button></div></div></dialog><div class="toast" id="toast" role="status" hidden></div>'''


def layout(body, view='today', date=TODAY, prefix='', title='今日'):
    version = hashlib.sha256((OUT/'app.js').read_bytes() + (OUT/'style.css').read_bytes() + json.dumps(TOKENS).encode()).hexdigest()[:10]
    nav = [('today', 'index.html', '今日简报', '01'), ('projects', 'projects.html', '开源项目', '02'), ('week', 'week.html', '一周观察', '03'), ('archive', 'archive.html', '往期检索', '04')]
    navigation = ''.join(f'<a href="{prefix}{path}" ' + ('aria-current="page"' if name == view else '') + f'><span class="nav-number">{num}</span>{label}<span class="nav-arrow" aria-hidden="true">↗</span></a>' for name,path,label,num in nav)
    dec = DECISIONS.get(date) if view == 'today' else None
    order = ([i for group in dec['groups'] for i, it in enumerate(ISSUES[date]['items'])
              if dec['items'].get(it['id'], {}).get('group') == group['key']]
             if dec else None)
    payload = json.dumps({'issue': ISSUES[date] if view == 'today' else None, 'dates': DATES,
                          'colors': TOKENS['color'], 'decisionOrder': order},
                         ensure_ascii=False).replace('<', chr(92)+'u003c')
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="description" content="每日 AI 与 GitHub 动态，附官方来源、事实与边界。"><title>{esc(title)} · 信号 SIGNAL</title><link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{prefix}tokens.css?v={version}"><link rel="stylesheet" href="{prefix}style.css?v={version}"><script src="{prefix}app.js?v={version}" defer></script></head>
<body data-view="{view}" data-date="{date}" data-prefix="{prefix}"><a class="skip" href="#main">跳到正文</a><div class="shell"><header class="top"><a class="brand" href="{prefix}index.html"><span class="brand-symbol" aria-hidden="true"><svg viewBox="0 0 32 32" fill="none"><circle class="radar-ring" cx="16" cy="16" r="13" stroke-width="1.3"/><circle class="radar-ring" cx="16" cy="16" r="8.5" stroke-width="1.1"/><circle class="radar-ring" cx="16" cy="16" r="4" stroke-width="1"/><path class="radar-tick" d="M16 1.5v3M16 27.5v3M1.5 16h3M27.5 16h3" stroke-width="1.2" stroke-linecap="round"/><g class="radar-sweep"><path d="M16 16 L16 3 A13 13 0 0 1 27.3 9.5 Z"/><line x1="16" y1="16" x2="16" y2="3"/></g><circle class="radar-blip" cx="21" cy="11" r="1.5"/><circle class="radar-blip" cx="11" cy="20" r="1.2" opacity=".6"/></svg></span><span class="brand-name">信号<small>SIGNAL</small></span></a><p class="brand-note">把变化读明白。</p><nav class="nav" aria-label="主导航">{navigation}</nav><div class="rail-bottom"><span>每日 AI / GitHub</span><a href="{prefix}status.html">出刊状态 <span aria-hidden="true">↗</span></a><p>独立阅读 · 无账号</p><span class="rail-edition">VOL. {ISSUES[date]['no']:03d} / 2026</span></div></header><div class="workspace"><div class="workspace-top"><span>{dict((name,label) for name,_,label,_ in nav).get(view,'出刊状态')}</span><div><span class="demo-label">每日简报</span><a href="{prefix}archive.html?search=1" aria-label="搜索往期">检索 <kbd>/</kbd></a></div></div>
<main id="main" class="reading">{body}</main>{footer(prefix,date)}</div></div>{dialog()}<script type="application/json" id="prototype-data">{payload}</script></body></html>'''

def evidence(it):
    links = ' '.join(link(source['url'], source['publisher']+' · '+source['title']) for source in it['sources'])
    times = '；'.join(source['publisher']+'：'+source['publishedAt'] for source in it['sources'])
    return f'''<details class="evidence"><summary>事实与边界</summary><div class="evidence-body"><h3>事件</h3><p>{esc(it['event'])}</p><h3>关键事实</h3><ul>{''.join('<li>'+esc(v)+'</li>' for v in it['facts'])}</ul><h3>适用场景</h3><ul>{''.join('<li>'+esc(v)+'</li>' for v in it['scenes'])}</ul><h3>边界与存疑</h3><p>{esc(it['caveat'])}</p><h3>来源原文</h3><div class="source-links">{links}</div><p class="fine">原始发布时间：{esc(times)}。仅标日期的来源未补造时刻。</p></div></details>'''


def item(it, idx, date, decision=None):
    """Original index is preserved so archive/permalink anchors never move."""
    kind_ic = 'ic-branch' if 'GITHUB' in it['cat'].upper() else 'ic-sparkles'
    if decision:
        meta = f'''<div class="decision-head"><span class="number">{idx+1:02d}</span><span class="level-tag{' subtle' if decision['group'] != 'do' else ''}">{esc(decision['level'])}</span><span class="item-meta"><i class="ic {kind_ic}" aria-hidden="true"></i>{esc(it['cat'])}</span></div>
    <p class="action">{esc(decision['action'])}</p><p class="rel"><span class="k">与你有关，如果</span>{esc(decision['relevantIf'])}</p><p class="skip-line"><span class="k">否则</span>{esc(decision['skipIf'])}</p>'''
        cls = 'item decision-item'
    else:
        meta = f'<p class="item-meta"><span class="number">{idx+1:02d}</span><i class="ic {kind_ic}" aria-hidden="true"></i><span>{esc(it["cat"])}</span></p>'
        cls = 'item'
    return f'''<article class="{cls}" id="item-{idx}" data-item="{idx}" data-kind="{'github' if 'GITHUB' in it['cat'].upper() else 'ai'}">{meta}<h2><a href="#item-{idx}">{esc(it['title'])}</a></h2><p class="verdict">{marked(it['verdict'])}</p><p class="why">{esc(it['why'])}</p>{evidence(it)}<div class="item-actions"><button class="take js-only inline" data-action="take" data-index="{idx}" aria-pressed="false">带走这条</button><a href="#item-{idx}" aria-label="第 {idx+1} 条固定位置">定位此条</a></div></article>'''


def teaser(p, prefix):
    return f'''<article class="project teaser"><h3><a href="{prefix}projects.html#{slug(p['name'])}">{esc(p['name'])}</a></h3><p>{esc(p['oneline'])}</p><a class="project-ref" href="{prefix}projects.html#{slug(p['name'])}">适用场景与项目介绍</a></article>'''


def decision_hero(d, dec, date):
    headline = esc(dec['headline']).replace(esc(dec['accent']), '<mark>' + esc(dec['accent']) + '</mark>', 1)
    lens = ''.join(f'<a href="{esc(v["target"], quote=True)}">{esc(v["label"])}</a>' for v in dec['lens'])
    return f'''<section class="hero decision-band glass" aria-labelledby="decision-headline">
    <p class="eyebrow">{date.replace('-', '.')} · 第 {d['no']:03d} 期 · 共 {len(d['items'])} 条 · 只读官方来源</p>
    <h1 id="decision-headline">{headline}</h1><p class="intro">{esc(dec['summary'])}</p>
    <div class="lens"><span>你现在在做什么</span>{lens}</div>
    <details class="band-notes"><summary>本期主线与口径</summary><div><p>本期主线：{esc(plain(d['headline']))} · {esc(d['lede'])}</p><p>{esc(dec['editorialNote'])}</p></div></details></section>'''


def grouped_items(d, dec, date):
    blocks = []
    for group in dec['groups']:
        members = [(i, it) for i, it in enumerate(d['items'])
                   if dec['items'].get(it['id'], {}).get('group') == group['key']]
        if not members:
            continue
        key = esc(group['key'], quote=True)
        cards = ''.join(item(it, i, date, dec['items'][it['id']]) for i, it in members)
        blocks.append(f'<section class="decision-group" id="group-{key}" aria-labelledby="gh-{key}"><div class="group-head"><h2 id="gh-{key}">{esc(group["label"])}</h2><span>{esc(group["note"])}</span></div>{cards}</section>')
    return ''.join(blocks)


def today(date, prefix):
    d = ISSUES[date]
    dec = DECISIONS.get(date)
    idx = DATES.index(date)
    prev = f'<a href="{prefix}d/{DATES[idx-1]}.html">上一期 · {esc(ISSUES[DATES[idx-1]]["short"])}</a>' if idx else '<span>最早一期</span>'
    nxt = f'<a href="{prefix}d/{DATES[idx+1]}.html">下一期</a>' if idx < len(DATES)-1 else '<span>已是最新一期</span>'
    amendments = ''.join('<section class="section"><h2>勘误与补充</h2><p>'+esc(a['createdAt'])+' · '+esc(a['text'])+'</p></section>' for a in d['amendments'])
    if dec:
        # Contents follows the decision reading order; anchors keep their original
        # indices so archive/permalink links never move.
        toc_order = [(i, it) for group in dec['groups'] for i, it in enumerate(d['items'])
                     if dec['items'].get(it['id'], {}).get('group') == group['key']]
        hero = decision_hero(d, dec, date)
        items_html = grouped_items(d, dec, date)
    else:
        toc_order = list(enumerate(d['items']))
        hero = f'''<section class="hero feature"><div class="feature-copy"><span class="feature-label">本期主线</span><h1>{marked(d['headline'])}</h1><p class="intro">{esc(d['lede'])}</p><div class="hero-meta"><a class="primary-link" href="#daily-content">阅读本期 <span aria-hidden="true">↓</span></a><span>{len(d['items'])} 条动态 · 约 5 分钟</span></div></div><figure class="feature-art"><picture><source media="(max-width:640px)" srcset="{prefix}assets/delivery-mobile.svg?v=6"><img src="{prefix}assets/delivery.svg?v=6" alt="任务交付流程示意：问题经拆解、执行、验收后形成交付物，不代表性能统计。" width="420" height="330"></picture><figcaption>从回答问题，到交付结果。</figcaption></figure></section>'''
        items_html = ''.join(item(it, i, date) for i, it in enumerate(d['items']))
    toc = ''.join(f'<a href="#item-{i}"><span>{i+1:02d}</span><strong>{esc(it["title"])}</strong></a>' for i, it in toc_order)
    return f'''<div class="edition"><time datetime="{date}">{date.replace('-', '.')} <span> / {DATA['WD'][date]}</span></time><span>第 {d['no']:03d} 期 · 官方来源</span></div>
    {hero}
    <div class="daily-grid"><section class="daily-reading" id="daily-content"><div class="toolbar"><h2 class="label">今日动态 <span>{len(d['items']):02d}</span></h2><div class="tools js-only"><button data-action="share">生成分享图<span data-selection-count></span></button></div></div><div class="items">{items_html}</div></section>
    <aside class="issue-aside"><section class="toc"><div class="aside-heading"><h2>本期目录</h2><span>CONTENTS</span></div>{toc}</section><section class="aside-projects"><div class="aside-heading"><h2>项目速递</h2><a href="{prefix}projects.html">全部</a></div>{''.join(teaser(p,prefix) for p in PROJECTS[:2])}</section><a class="previous-edition" href="{prefix}archive.html"><span>错过了哪一期？</span><strong>去往期接着读</strong></a></aside></div>
    {amendments}<section class="closing"><div><h2>值得带走的，不止一个标题。</h2><p>选好想继续了解的内容，留一份给自己。</p></div><div class="links"><button class="js-only inline" data-action="share">生成分享图</button><a href="{prefix}downloads/{date}.md" download>下载文字版</a><a href="{prefix}feed.xml">RSS</a><a href="{prefix}daily.ics" download>阅读提醒</a></div><p class="fine">日历提醒需导入后生效；新闻边界与原始来源见条目展开。</p></section><div class="pager">{prev}{nxt}</div>'''


def growth(value):
    return '暂缺（无对照快照）' if value is None else f'{value:+,}'


def stars_chart():
    """Same-instant cumulative stars as CSS bars, not an SVG trend line.

    CSS bars keep label text at real pixel sizes on narrow viewports, inherit
    theme colours from tokens.css and need no script to render.
    """
    rows = sorted(((p['name'], SNAPSHOTS[p['name']]['stars']) for p in PROJECTS), key=lambda r: -r[1])
    peak = max(v for _, v in rows)
    collected = SNAPSHOTS[rows[0][0]]['collectedAt']
    bars = []
    for name, value in rows:
        pct = f'{value / peak * 100:.1f}'
        bars.append(f'<li class="bar-row"><span class="bar-name">{esc(name)}</span>'
                    f'<span class="bar-track" aria-hidden="true"><span class="bar-fill" style="width:{pct}%"></span></span>'
                    f'<span class="bar-value">{value:,}</span></li>')
    return (f'<ol class="bar-list" aria-label="本期 {len(rows)} 个项目的累计星标对比">'
            + ''.join(bars) + '</ol>'
            + f'<p class="chart-foot">累计星标 · GitHub API 单次快照 · 采集于 {esc(collected)} · 无历史基线，不计算增量或趋势</p>')


def snapshot_table():
    head = '<thead><tr><th scope="col">项目</th><th scope="col">累计星标</th><th scope="col">主语言</th><th scope="col">许可</th><th scope="col">最近推送（UTC）</th><th scope="col">已归档</th></tr></thead>'
    body = []
    for p in PROJECTS:
        s = SNAPSHOTS[p['name']]
        body.append('<tr><th scope="row">' + esc(p['name']) + '</th><td>' + f"{s['stars']:,}" + '</td><td>' + esc(s['language'] or '未标注') + '</td><td>' + esc(p['license']) + '</td><td>' + esc(s['pushedAt'].replace('T', ' ').replace('Z', '')) + '</td><td>' + ('是' if s['archived'] else '否') + '</td></tr>')
    return '<div class="table-scroll"><table class="data-table"><caption>快照明细 · 图表的纯文字等价版本</caption>' + head + '<tbody>' + ''.join(body) + '</tbody></table></div>'


def backend_table(p):
    rows = p.get('backends') or []
    if not rows:
        return ''
    body = ''.join('<tr><th scope="row">' + esc(b['name']) + '</th><td>' + esc(b['target']) + '</td></tr>' for b in rows)
    return f'''<h3>硬件后端 · README 列出 {len(rows)} 项</h3><div class="table-scroll"><table class="data-table compact"><caption>后端与目标设备，逐条取自官方 README</caption><thead><tr><th scope="col">后端</th><th scope="col">目标设备</th></tr></thead><tbody>{body}</tbody></table></div><p class="fine">中文设备名按 README 的 Target devices 归纳；含进行中项目，不代表本站实测可用。</p>'''


def how_to(p):
    h = p.get('howTo')
    if not h:
        return ''
    steps = ''.join(f'<div class="cmd-row"><span class="cmd-label">{esc(s["label"])}</span><pre><code>{esc(s["cmd"])}</code></pre></div>' for s in h['steps'])
    return f'''<section class="pf-block pf-how"><h3>怎么开始</h3><p>{esc(h["intro"])}</p><div class="cmd-list">{steps}</div><p class="fine">{esc(h["note"])}</p></section>'''


def profile(p, today_ids):
    name, snap = p['name'], SNAPSHOTS[p['name']]
    owner, repo = name.split('/')
    anchor = slug(name)
    item = p.get('todayItem')
    has_release = item is not None and item in today_ids
    tag = '今日有发布' if has_release else '补录 · 今日无发布'
    day_delta = p['day']['delta'] if p['day']['delta'] is not None else ''
    week_delta = p['week']['delta'] if p['week']['delta'] is not None else ''
    who = ''.join('<li>' + esc(v) + '</li>' for v in p.get('whoFor', []))
    scenes = ''.join('<li>' + esc(v) + '</li>' for v in p['scenes'])
    sources = ''.join(link(v['url'], v['title']) for v in p['sources'])
    pushed = snap['pushedAt'][5:16].replace('T', ' ')
    return f'''<article class="project profile" id="{anchor}" data-project data-topics="{esc(' '.join(p['topics']))}" data-day="{day_delta}" data-week="{week_delta}">
    <header class="pf-head"><div class="project-identity"><span class="repo-monogram" aria-hidden="true">{esc(owner[:2].upper())}</span><div><span class="repo-owner">{esc(owner)}</span><h2><a href="#{anchor}">{esc(repo)}</a></h2></div></div><div class="pf-head-side"><span class="release-tag{' yes' if has_release else ''}">{tag}</span>{link('https://github.com/'+name,'打开仓库')}</div></header>
    <p class="oneline">{esc(p['oneline'])}</p>
    <section class="pf-block"><h3>解决什么</h3><p>{esc(p['problem'])}</p></section>
    <div class="pf-cols"><section class="pf-block"><h3>谁在用</h3><ul>{who}</ul></section><section class="pf-block"><h3>什么时候别用 / 边界</h3><p>{esc(p['not'])}</p><p class="caveat">{esc(p.get('caveat', ''))}</p></section></div>
    {how_to(p)}
    <div class="pf-data"><div><span>累计星标</span><strong>{snap['stars']:,}</strong></div><div><span>主语言</span><strong>{esc(snap['language'] or '未标注')}</strong></div><div><span>许可</span><strong>{esc(p['license'])}</strong></div><div><span>最近推送</span><strong>{esc(pushed)} UTC</strong></div></div>
    <p class="fine pf-growth"><i class="ic ic-activity" aria-hidden="true"></i><span data-growth>今日增量 {growth(p['day']['delta'])}</span></p>
    <details class="evidence"><summary>完整事实 · 后端清单 · 来源与口径</summary><div class="evidence-body"><h3>适用场景</h3><ul>{scenes}</ul><h3>为什么现在关注</h3><p data-day-reason>{esc(p['why'])}</p><p data-week-reason hidden>{esc(p['whyWeek'])}</p><h3>同类可选</h3><p>{esc(p['alt'])}</p>{backend_table(p)}<h3>采集快照</h3><p>累计星标 {p['day']['total']:,} · 今日增量 {growth(p['day']['delta'])} · 本周增量 {growth(p['week']['delta'])}</p><p class="fine">采集于 {esc(snap['collectedAt'])}；仓库归档状态：{'是' if snap['archived'] else '否'}。增量需相同时间基准的历史快照。</p><h3>来源</h3><div class="source-links">{sources}</div></div></details></article>'''


def projects():
    today_ids = {it['id'] for it in ISSUES[TODAY]['items']}
    released = [p for p in PROJECTS if p.get('todayItem') and p['todayItem'] in today_ids]
    ordered = released + [p for p in PROJECTS if p not in released]
    lens = ''.join(f'<a href="#{slug(p["name"])}">{esc(p.get("lens", p["name"].split("/")[-1]))}</a>' for p in ordered)
    collected = SNAPSHOTS[ordered[0]['name']]['collectedAt']
    return f'''<div class="edition"><span>GITHUB</span><span>{TODAY} · 已采集</span></div>
    <div class="overview"><section class="hero result"><h1>今天 <mark>{len(released)} 个</mark>项目有发布。</h1><p class="intro">共 {len(PROJECTS)} 份档案 · 命令来自官方 README · 数字来自 GitHub API 快照。</p><div class="lens"><span>你现在要做什么</span>{lens}</div><p class="editorial-note">{esc(EDITORIAL_NOTE)}</p></section>
    <div class="overview-data"><figure class="chart glass">{stars_chart()}<figcaption>三个项目同一时点的累计星标对比。这是单次快照，不是趋势线；缺少历史基线时不计算增量。</figcaption></figure>
    <details class="data-detail"><summary>快照明细 · 图表的纯文字等价版本</summary>{snapshot_table()}</details></div></div>
    <div class="project-filters js-only"><div class="filters" aria-label="统计周期"><button data-period="day" aria-pressed="true">今日</button><button data-period="week" aria-pressed="false">本周</button><span class="fine" id="project-count">{len(PROJECTS)} 个项目</span></div><label class="select-wrap">主题<select id="project-topic"><option value="all">全部主题</option><option value="agent">智能体</option><option value="inference">推理服务</option><option value="local-llm">本地模型</option><option value="developer-tools">开发工具</option></select></label></div>
    <div id="project-list">{''.join(profile(p, today_ids) for p in ordered)}</div>
    <div id="project-empty" class="empty" hidden><h2>这个主题暂时没有项目</h2><p>换个主题继续看看。</p><button data-action="reset-projects">查看全部项目</button></div>
    <section class="closing"><a class="text-link" href="index.html">返回今日动态</a><p class="fine">采集于 {esc(collected)}；介绍层据官方 README 归纳，已发布快照不可改写。</p></section>'''


def archive():
    entries = []
    for date in reversed(DATES):
        d = ISSUES[date]
        hits = []
        for i,it in enumerate(d['items']):
            haystack = plain(' '.join([it['title'],it['verdict'],it['why'],it['event'],*it['facts'],*it['scenes'],it['caveat'],json.dumps(it['sources'],ensure_ascii=False)]))
            hits.append(f'<div class="archive-hit" data-search="{esc(haystack,quote=True)}"><a href="d/{date}.html#item-{i}">{esc(it["title"])}</a><p data-snippet>{esc(plain(it["verdict"]))}</p></div>')
        entries.append(f'<section class="archive-issue" data-issue data-search="{esc(date+" "+plain(d["headline"])+" "+d["lede"],quote=True)}"><p class="issue-date">{date} · {len(d["items"])} 条</p><h2><a href="d/{date}.html">{esc(plain(d["headline"]))}</a></h2><p class="issue-summary">{esc(d["lede"])}</p>{"".join(hits)}</section>')
    return f'''<div class="edition"><span>ARCHIVE</span><span>{len(DATES)} 期 · 已采集</span></div><section class="hero"><h1>每一天，都有<mark>迹可循</mark>。</h1><p class="intro">按日期翻阅，或搜索标题、正文和项目场景。</p></section><div class="archive-search js-only"><label for="search" hidden>搜索往期全文</label><input id="search" type="search" placeholder="搜索日期、主题或正文" aria-label="搜索往期全文" autocomplete="off"><button data-action="clear-search" hidden>清空</button></div><p class="fine" id="search-status" role="status">共 {len(DATES)} 期</p><div class="archive-results" id="archive-results">{''.join(entries)}</div><div class="empty" id="search-empty" hidden><h2>没有找到相关内容</h2><p>试试“Agent”“推理”，或直接输入日期。</p><button data-action="clear-search">清空搜索，查看全部刊期</button></div>'''


def week():
    start = (calendar_date.fromisoformat(TODAY)-timedelta(days=6)).isoformat()
    covered = [dt for dt in DATES if start <= dt <= TODAY]
    sections = ''.join(f'<section class="week-theme"><h2>{dt}</h2><ul>'+''.join(f'<li><a href="d/{dt}.html#item-{i}">{esc(it["title"])}</a></li>' for i,it in enumerate(ISSUES[dt]['items']))+'</ul></section>' for dt in reversed(covered))
    note = f'近七天已有 {len(covered)} 期真实记录。' + ('历史不足七天，暂不推断趋势或项目周增量。' if len(covered)<7 else '沿具体条目回看变化，不将报道次数等同于热度。')
    return f'''<div class="edition"><span>近七天</span><span>{start} — {TODAY}</span></div><section class="hero"><h1>一周的进展，<mark>连起来看</mark>。</h1><p class="intro">{note}</p></section><div class="week-grid">{sections}</div><section class="section"><div class="section-head"><h2>项目观察</h2><a href="projects.html?period=week">查看项目</a></div>{''.join(teaser(p,'') for p in PROJECTS[:3])}</section>'''


def status():
    d=ISSUES[TODAY]
    return f'''<div class="edition"><span>STATUS</span><span>内容已接入</span></div><section class="hero"><h1>每一次出刊，<mark>有据可查</mark>。</h1><p class="intro">本期为人工补刊，由官方原文与 GitHub API 编纂；自动出刊和生产部署尚未接入。</p></section><dl class="status-grid"><div><dt>当前刊期</dt><dd>{TODAY} · {len(d['items'])} 条</dd></div><div><dt>本期采集截止</dt><dd>{esc(d['generatedAt'])}</dd></div><div><dt>自动出刊</dt><dd>未接入</dd></div><div><dt>项目档案</dt><dd>{len(PROJECTS)} 个真实快照</dd></div></dl><section class="section"><h2>采集范围</h2><p>{esc(d['window']['note'])}</p><p>开始：{esc(d['window']['start'])}<br>截止：{esc(d['window']['end'])}</p><p>来源可达性、原始发布时间和未复跑的边界均在各条目中保留。缺少历史对照时，日增量与周增量为暂缺。</p></section>'''


def make_art():
    a = TOKENS['art']
    (OUT/'assets').mkdir(parents=True, exist_ok=True)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="330" viewBox="0 0 480 330"><defs>
<linearGradient id="glass" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{a['node']}"/><stop offset="1" stop-color="{a['panel']}"/></linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{a['line']}"/><stop offset=".5" stop-color="{a['tint']}" stop-opacity=".25"/><stop offset="1" stop-color="{a['line']}"/></linearGradient>
<radialGradient id="glow"><stop stop-color="{a['glow']}" stop-opacity=".7"/><stop offset="1" stop-color="{a['glow']}" stop-opacity="0"/></radialGradient>
<filter id="shadow" x="-50%" y="-60%" width="220%" height="240%"><feDropShadow dx="0" dy="14" stdDeviation="12" flood-color="{a['shadow']}" flood-opacity=".14"/></filter></defs>
<ellipse cx="255" cy="188" rx="210" ry="140" fill="url(#glow)"/>
<g transform="translate(94 57) rotate(-13 126 100)" filter="url(#shadow)"><rect width="234" height="146" rx="18" fill="url(#glass)" stroke="url(#edge)" stroke-width="1.3"/><path d="M25 35h42m-42 14h85" stroke="{a['tint']}" stroke-width="3" stroke-linecap="round"/><text x="25" y="120" font-family="sans-serif" font-size="15" fill="{a['secondary']}">理解问题</text><text x="200" y="120" font-family="Arial,sans-serif" font-size="11" fill="{a['secondary']}">01</text></g>
<g transform="translate(130 92) rotate(1 117 73)" filter="url(#shadow)"><rect width="234" height="146" rx="18" fill="url(#glass)" stroke="url(#edge)" stroke-width="1.3"/><path d="M25 35h42m-42 14h85" stroke="{a['tint']}" stroke-width="3" stroke-linecap="round"/><text x="25" y="120" font-family="sans-serif" font-size="15" fill="{a['secondary']}">拆解与执行</text><text x="200" y="120" font-family="Arial,sans-serif" font-size="11" fill="{a['secondary']}">02</text></g>
<g transform="translate(160 133) rotate(13 117 73)" filter="url(#shadow)"><rect width="234" height="146" rx="18" fill="url(#glass)" stroke="url(#edge)" stroke-width="1.3"/><path d="M25 35h42m-42 14h85" stroke="{a['tint']}" stroke-width="3" stroke-linecap="round"/><text x="25" y="120" font-family="sans-serif" font-size="19" font-weight="500" fill="{a['ink']}">完整交付</text><path d="m192 108 6 6 12-13" stroke="{a['ink']}" stroke-width="1.8" fill="none" stroke-linecap="round"/></g></svg>'''
    (OUT/'assets'/'delivery.svg').write_text(svg)
    mobile = f'''<svg xmlns="http://www.w3.org/2000/svg" width="420" height="115" viewBox="0 0 420 115"><defs><linearGradient id="g"><stop stop-color="{a['node']}"/><stop offset="1" stop-color="{a['panel']}"/></linearGradient></defs><g font-family="sans-serif" font-size="13" fill="{a['ink']}"><rect x="16" y="20" width="126" height="70" rx="12" fill="url(#g)" stroke="{a['line']}"/><rect x="147" y="14" width="126" height="70" rx="12" fill="url(#g)" stroke="{a['line']}"/><rect x="278" y="20" width="126" height="70" rx="12" fill="url(#g)" stroke="{a['line']}"/><text x="34" y="46" font-size="9" fill="{a['secondary']}">01 / UNDERSTAND</text><text x="34" y="70">理解问题</text><text x="165" y="40" font-size="9" fill="{a['secondary']}">02 / BUILD</text><text x="165" y="64">拆解与执行</text><text x="296" y="46" font-size="9" fill="{a['secondary']}">03 / DELIVER</text><text x="296" y="70">完整交付 ↗</text></g></svg>'''
    (OUT/'assets'/'delivery-mobile.svg').write_text(mobile)
    (OUT/'assets'/'favicon.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="{a["background"]}"/><g fill="none" stroke="{a["ink"]}"><circle cx="16" cy="16" r="11" stroke-width="1.4" opacity=".4"/><circle cx="16" cy="16" r="6.5" stroke-width="1.2" opacity=".55"/></g><path d="M16 16 L16 5 A11 11 0 0 1 25.5 10.5 Z" fill="{a["ink"]}" opacity=".22"/><path d="M16 16V5" stroke="{a["ink"]}" stroke-width="1.8" stroke-linecap="round"/><circle cx="20.5" cy="11.5" r="1.8" fill="{a["ink"]}"/></svg>')


def resources():
    feed = ET.Element('rss', version='2.0')
    channel = ET.SubElement(feed,'channel')
    for name,text in [('title','SIGNAL · 每日 AI / GitHub'),('link',SITE_CONFIG['publicBaseUrl'] or SITE_CONFIG['repositoryUrl']),('description','官方来源编纂的每日简报；尚未配置站点域名时，订阅条目指向仓库 Markdown。')]: ET.SubElement(channel,name).text=text
    for date in reversed(DATES):
        d=ISSUES[date];entry=ET.SubElement(channel,'item')
        for name,text in [('title',plain(d['headline'])),('link',(SITE_CONFIG['publicBaseUrl'].rstrip('/')+f'/d/{date}.html') if SITE_CONFIG['publicBaseUrl'] else SITE_CONFIG['repositoryUrl']+f'/blob/main/content/days/{date}.md'),('description',d['lede'])]: ET.SubElement(entry,name).text=text
        ET.SubElement(entry,'guid',isPermaLink='false').text='signal-'+date
    ET.ElementTree(feed).write(OUT/'feed.xml',encoding='utf-8',xml_declaration=True)
    (OUT/'daily.ics').write_bytes(('BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//SIGNAL//Prototype//ZH\r\nCALSCALE:GREGORIAN\r\nBEGIN:VEVENT\r\nUID:signal-reading-20261110\r\nDTSTAMP:20261110T000000Z\r\nDTSTART:20261110T230000Z\r\nDURATION:PT5M\r\nRRULE:FREQ=DAILY;COUNT=7\r\nSUMMARY:阅读 SIGNAL\r\nDESCRIPTION:每天北京时间 07:00 留五分钟阅读。不会自动打开网页或订阅邮件。\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n').replace('20261110', TODAY.replace('-', '')).encode())
    for date,d in ISSUES.items():
        parts=[f'# SIGNAL · {date}', '> 官方来源编纂；厂商声明与实测边界见各条目。',plain(d['headline']),d['lede']]
        for i,it in enumerate(d['items']):
            parts.extend([f'## {i+1}. {it["title"]}',plain(it['verdict']),it['why'],it['event'],'关键事实：'+'；'.join(it['facts']),'场景：'+'；'.join(it['scenes']),it['caveat'],'来源：'+'；'.join(v['title']+' '+v['url'] for v in it['sources'])])
        for a in d['amendments']:
            parts.extend(['## 勘误与补充', a['createdAt']+' · '+a['itemId']+' · '+a['text']])
        text='\n\n'.join(parts)+'\n'
        (OUT/'downloads'/f'{date}.md').write_text(text)
        (ROOT/'content/days'/f'{date}.md').write_text(text)


for directory, suffix in [('d','.html'), ('downloads','.md')]:
    for stale in (OUT/directory).glob('*'+suffix):
        if stale.stem not in DATES:
            stale.unlink()
(OUT/'d').mkdir(parents=True, exist_ok=True)
(OUT/'downloads').mkdir(parents=True, exist_ok=True)
(OUT/'tokens.css').write_text(token_css())
make_art()
(OUT/'index.html').write_text(layout(today(TODAY,''),title='今日'))
for date in DATES:
    (OUT/'d'/f'{date}.html').write_text(layout(today(date,'../'),date=date,prefix='../',title=date))
for name,fn,title in [('projects',projects,'项目'),('archive',archive,'往期'),('week',week,'本周'),('status',status,'状态')]:
    (OUT/f'{name}.html').write_text(layout(fn(),view=name,title=title))
resources()
print(f'Built {len(DATES)+5} static pages, {len(DATES)} text editions, RSS, calendar and token CSS.')
