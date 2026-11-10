/* Prototype enhancement only. Reading, routes and evidence remain static HTML. */
'use strict';
document.documentElement.classList.add('js');
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const data = JSON.parse($('#prototype-data').textContent);
const page = document.body.dataset;
const issue = data.issue;
const selection = new Set();
let toastTimer;
let shareFrom = null;
let drawRevision = 0;
let cardReady = false;
let period = new URLSearchParams(location.search).get('period') === 'week' ? 'week' : 'day';

function plain(value) {
  const node = document.createElement('div');
  node.innerHTML = value; // only locally built fixture marks; never remote model output
  return node.textContent;
}

function toast(message) {
  const node = $('#toast');
  node.textContent = message;
  node.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { node.hidden = true; }, 2600);
}

function theme() {
  return document.documentElement.dataset.theme || 'light';
}

function setTheme(value) {
  document.documentElement.dataset.theme = value;
  $$('[data-action="theme"]').forEach(button => {
    button.textContent = value === 'dark' ? '浅色' : '深色';
    button.setAttribute('aria-label', value === 'dark' ? '切换为浅色主题' : '切换为深色主题');
  });
}

try {
  setTheme(localStorage.getItem('signal:theme') || (matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light'));
} catch { setTheme('light'); }

function syncSelection() {
  $$('[data-action="take"]').forEach(button => {
    const taken = selection.has(Number(button.dataset.index));
    button.setAttribute('aria-pressed', String(taken));
    button.textContent = taken ? '已选 · 取消' : '带走这条';
  });
  $$('[data-selection-count]').forEach(node => { node.textContent = selection.size ? ` · 已选 ${selection.size} 条` : ''; });
}

function shareRows() {
  return issue.items.map((item, index) => ({ item, index })).filter(({ index }) => selection.has(index));
}

function shareText() {
  return [`SIGNAL · ${page.date}`, plain(issue.headline), ...shareRows().map(({item}, index) => `${index + 1}. ${item.title}\n${plain(item.verdict)}`), '来源与边界见本期原文。'].join('\n\n');
}

function lines(ctx, text, width) {
  const result = [];
  let line = '';
  for (const character of [...text]) {
    if (character === '\n') { result.push(line); line = ''; continue; }
    if (line && ctx.measureText(line + character).width > width) { result.push(line); line = character; }
    else line += character;
  }
  if (line) result.push(line);
  return result;
}

async function drawCard() {
  const revision = ++drawRevision;
  cardReady = false;
  const feedback = $('#share-feedback');
  const buttons = $$('[data-action="download"], [data-action="copy"]');
  const rows = shareRows();
  buttons.forEach(button => { button.disabled = !rows.length; });
  if (!rows.length) {
    $('#share-canvas').hidden = true;
    feedback.textContent = '至少选择一条内容。';
    return;
  }
  $('#share-canvas').hidden = false;
  feedback.textContent = `已选 ${rows.length} 条 · 正在生成图片…`;
  try {
    await document.fonts.ready;
    if (revision !== drawRevision) return;
    const canvas = $('#share-canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas unavailable');
    const palette = data.colors[theme()];
    const font = '-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif';
    canvas.width = 1080;
    ctx.font = `700 54px ${font}`;
    const heading = lines(ctx, plain(issue.headline), 920);
    let height = 184 + heading.length * 72 + 44;
    const measured = rows.map(({item,index}) => {
      ctx.font = `650 36px ${font}`;
      const titles = lines(ctx, item.title, 850);
      ctx.font = `30px ${font}`;
      const text = lines(ctx, plain(item.verdict), 850);
      height += titles.length * 53 + text.length * 47 + 88;
      return { titles, text, index };
    });
    canvas.height = height + 60;
    ctx.fillStyle = palette.background;
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle = palette.accent;
    ctx.fillRect(0,0,canvas.width,8);
    ctx.font = `600 28px ${font}`;
    ctx.fillStyle = palette.text;
    ctx.fillText('信号  SIGNAL',80,90);
    ctx.textAlign = 'right';
    ctx.font = `26px ${font}`;
    ctx.fillStyle = palette.muted;
    ctx.fillText(page.date,1000,90);
    ctx.textAlign = 'left';
    let y = 184;
    ctx.font = `700 54px ${font}`;
    ctx.fillStyle = palette.text;
    heading.forEach(line => { ctx.fillText(line,80,y); y += 72; });
    y += 44;
    measured.forEach(({titles,text,index}) => {
      ctx.fillStyle = palette.accent;
      ctx.font = `28px ${font}`;
      ctx.fillText(String(index+1).padStart(2,'0'),80,y);
      ctx.fillStyle = palette.text;
      ctx.font = `650 36px ${font}`;
      titles.forEach(line => { ctx.fillText(line,144,y); y += 53; });
      y += 8;
      ctx.fillStyle = palette.secondary;
      ctx.font = `30px ${font}`;
      text.forEach(line => { ctx.fillText(line,144,y); y += 47; });
      y += 80;
    });
    ctx.font = `26px ${font}`;
    ctx.fillStyle = palette.muted;
    ctx.fillText('SIGNAL · 官方来源编纂',80,canvas.height-82);
    ctx.fillText('本地生成 · 不上传',80,canvas.height-40);
    feedback.textContent = `已选 ${rows.length} 条 · 图片包含完整标题与摘要`;
    cardReady = true;
  } catch {
    feedback.textContent = '图片生成失败，可复制文字，或关闭后重试。';
    $('[data-action="download"]').disabled = true;
  }
}

function openShare(trigger) {
  if (!issue) return;
  shareFrom = trigger;
  // With no chosen item, the default is the entire issue; later checkbox changes are explicit.
  if (!selection.size) issue.items.forEach((_,index) => selection.add(index));
  syncSelection();
  const options = $('#share-options');
  options.replaceChildren();
  const legend = document.createElement('legend'); legend.textContent = '选择内容'; options.append(legend);
  const all = document.createElement('button'); all.type = 'button'; all.dataset.action = 'select-all'; all.className = 'share-all'; all.textContent = '全选 / 清空'; options.append(all);
  issue.items.forEach((item,index) => {
    const label = document.createElement('label');
    const input = document.createElement('input'); input.type='checkbox'; input.checked=selection.has(index); input.dataset.shareIndex=index;
    const text = document.createElement('span'); text.textContent=`${String(index+1).padStart(2,'0')}  ${item.title}`;
    label.append(input,text);options.append(label);
  });
  $('#copy-fallback').hidden = true;
  $('#share-dialog').showModal();
  drawCard();
}

$('#share-dialog').addEventListener('close', () => {
  drawRevision++;
  syncSelection();
  if (shareFrom?.isConnected) shareFrom.focus({preventScroll:true});
});

function updateProjects() {
  const select = $('#project-topic');
  if (!select) return;
  const topic = select.value;
  const list = $('#project-list');
  const projects = $$('[data-project]',list).sort((a,b) => {
    if (a.dataset[period] === '') return b.dataset[period] === '' ? 0 : 1;
    if (b.dataset[period] === '') return -1;
    return Number(b.dataset[period])-Number(a.dataset[period]);
  });
  let count = 0;
  for (const node of projects) {
    node.hidden = topic !== 'all' && !node.dataset.topics.split(' ').includes(topic);
    if (!node.hidden) count++;
    const value = node.dataset[period];
    $('[data-growth]',node).textContent=`${period === 'week'?'本周':'今日'}增量 ${value === '' ? '暂缺（无对照快照）' : Number(value).toLocaleString('en-US',{signDisplay:'always'})}`;
    $('[data-day-reason]',node).hidden=period==='week';
    $('[data-week-reason]',node).hidden=period!=='week';
    list.append(node);
  }
  $$('[data-period]').forEach(button => button.setAttribute('aria-pressed',String(button.dataset.period===period)));
  $('#project-count').textContent=`${count} 个项目 · 缺少增量时按收录顺序`;
  $('#project-empty').hidden=count>0;
}
$('#project-topic')?.addEventListener('change',updateProjects);
updateProjects();

function searchArchive() {
  const input = $('#search');
  if (!input) return;
  const query = input.value.trim().toLocaleLowerCase();
  const terms = query.split(/\s+/).filter(Boolean);
  const matches = text => terms.every(term => text.toLocaleLowerCase().includes(term));
  let issues=0,items=0;
  $$('[data-issue]').forEach(node => {
    const whole = !!query && matches(node.dataset.search);
    let hits=0;
    $$('.archive-hit',node).forEach(hit => {
      const match = matches(hit.dataset.search);
      hit.hidden=!!query&&!match;
      if(query&&match) hits++;
    });
    node.hidden=!!query&&!whole&&!hits;
    if(!node.hidden) issues++;
    items+=hits;
  });
  $('#archive-results').classList.toggle('searching',!!query);
  $('#search-status').textContent=query ? `找到 ${issues} 期 · ${items} 条相关内容` : `共 ${issues} 期`;
  $('#search-empty').hidden=issues>0;
  $('.archive-search [data-action="clear-search"]').hidden=!query;
}
$('#search')?.addEventListener('input',searchArchive);

function revealAnchor() {
  if (!location.hash) return;
  const node=document.getElementById(decodeURIComponent(location.hash.slice(1)));
  if(!node) return;
  const details=$('details',node);
  if(page.view==='projects'&&details) details.open=true;
  node.scrollIntoView({block:'start'});
}
window.addEventListener('hashchange',revealAnchor);
revealAnchor();

document.addEventListener('change',event => {
  if (!event.target.matches('[data-share-index]')) return;
  const index=Number(event.target.dataset.shareIndex);
  if(event.target.checked) selection.add(index); else selection.delete(index);
  syncSelection();drawCard();
});

document.addEventListener('click',async event => {
  const control=event.target.closest('[data-action],[data-period]');
  if(!control) return;
  if(control.dataset.period) { period=control.dataset.period;updateProjects();return; }
  switch(control.dataset.action) {
    case 'theme': {
      const value=theme()==='light'?'dark':'light';setTheme(value);
      try { localStorage.setItem('signal:theme',value); } catch { /* theme remains in memory */ }
      if($('#share-dialog').open) drawCard();
      break;
    }
    case 'take': {
      const index=Number(control.dataset.index);
      if(selection.has(index)) selection.delete(index);else selection.add(index);
      syncSelection();break;
    }
    case 'share':openShare(control);break;
    case 'close-share':$('#share-dialog').close();break;
    case 'select-all':
      if(selection.size===issue.items.length) selection.clear();else issue.items.forEach((_,i)=>selection.add(i));
      $$('[data-share-index]').forEach(input=>{input.checked=selection.has(Number(input.dataset.shareIndex));});syncSelection();drawCard();break;
    case 'download': {
      if(!cardReady) return;
      const anchor=document.createElement('a');anchor.download=`SIGNAL-demo-${page.date}.png`;anchor.href=$('#share-canvas').toDataURL('image/png');anchor.click();
      $('#share-feedback').textContent='PNG 下载已发起';break;
    }
    case 'copy': {
      const text=shareText();
      try { await Promise.race([navigator.clipboard.writeText(text), new Promise((_, reject) => setTimeout(() => reject(new Error('Clipboard timeout')), 1500))]);$('#share-feedback').textContent=`已复制 ${selection.size} 条摘要`; }
      catch { const field=$('#copy-fallback');field.value=text;field.hidden=false;field.focus();field.select();$('#share-feedback').textContent='请从下方文本框手动复制。'; }
      break;
    }
    case 'clear-search':$('#search').value='';searchArchive();$('#search').focus();break;
    case 'reset-projects':$('#project-topic').value='all';updateProjects();$('#project-topic').focus();break;
  }
});

document.addEventListener('keydown',event => {
  if(event.ctrlKey||event.metaKey||event.altKey||event.target.closest('input,textarea,select,[contenteditable="true"]')||$('#share-dialog').open) return;
  if(event.key==='/') {event.preventDefault();if($('#search'))$('#search').focus();else location.href=page.prefix+'archive.html?search=1';}
  if(event.key==='c'&&page.view==='today') {event.preventDefault();openShare(document.activeElement);}
  if((event.key==='j'||event.key==='k')&&page.view==='today') {
    event.preventDefault();const nodes=$$('[data-item]');const focused=nodes.findIndex(node=>node.contains(document.activeElement));
    const index=Math.max(0,Math.min(nodes.length-1,focused+(event.key==='j'?1:-1)));
    $('h2 a',nodes[index])?.focus();
  }
});
if(new URLSearchParams(location.search).has('search')) $('#search')?.focus();
