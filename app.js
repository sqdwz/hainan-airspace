const $ = (s) => document.querySelector(s);

let latestData = null;
let activeFilter = null;

function fmtTime(v){
  if(!v) return '未明确';
  const d = new Date(v);
  if(Number.isNaN(d.getTime())) return v;
  return new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(d).replaceAll('/','-');
}

function formatMonthDay(v){
  if(!v) return '今日';
  const parts = String(v).split('-');
  if(parts.length < 3) return v;
  return `${Number(parts[1])}月${Number(parts[2])}日`;
}

function statusLabel(status){
  return ({active:'正在生效',upcoming:'即将生效',ended:'已结束',new:'新发布',unknown:'待核验'})[status] || '待核验';
}

function sourceLabel(n){
  if(n.source_label) return n.source_label;
  return ({official:'官方发布',media_repost:'媒体转载',media_report:'媒体发布'})[n.source_type] || '来源待核验';
}

function sourceTagClass(n){
  return ({official:'source-official',media_repost:'source-repost',media_report:'source-media'})[n.source_type] || 'source-unknown';
}

function isScanNew(n){
  if(typeof n.is_new_scan === 'boolean') return n.is_new_scan;
  return n.is_new_today === true;
}

function esc(s=''){
  return String(s).replace(/[&<>"']/g, c => {
    if(c === '&') return '&amp;';
    if(c === '<') return '&lt;';
    if(c === '>') return '&gt;';
    if(c === '"') return '&quot;';
    return '&#39;';
  });
}

function cleanBrief(s=''){
  return String(s).trim().replace(/[。；;，,\s]+$/g, '');
}

function fallbackBrief(n){
  if(n.status !== 'active') return '';
  const area = n.area || n.publisher || '相关区域';
  const end = n.end_time ? fmtTime(n.end_time) : '';
  if(end && !end.includes('未明确')) return `${area}管制持续至${end}`;
  return `${area}当前仍处于管制有效期内`;
}

function noticeBrief(n){
  return cleanBrief(n.brief || fallbackBrief(n));
}

function buildSummaryHtml(data){
  const s = data.summary || {};
  const newCount = s.new || 0;
  const active = s.active || 0;
  const upcoming = s.upcoming || 0;

  let primary = newCount
    ? `本次巡检发现 <strong>${newCount} 条</strong> 新增管制公告。`
    : '本次巡检未发现新增管制公告。';

  const stateParts = [];
  if(active > 0) stateParts.push(`当前仍有 <strong>${active} 条</strong> 管制生效`);
  if(upcoming > 0) stateParts.push(`另有 <strong>${upcoming} 条</strong> 即将生效`);
  if(stateParts.length) primary += `${stateParts.join('，')}。`;

  const allNotices = [...(data.notices || []), ...(data.ended_recent || [])];
  const todayPublished = allNotices.filter(n => n.publish_date === data.date || n.is_new_today === true);
  const dayLabel = formatMonthDay(data.date);
  const activeNotices = (data.notices || []).filter(n => n.status === 'active');

  let warning = todayPublished.length
    ? `⚠️ 今日（${dayLabel}）发现 <strong>${todayPublished.length} 条</strong> 海南省新发布的禁飞/空域管制公告。`
    : `⚠️ 今日（${dayLabel}）未发现海南省新发布的禁飞/空域管制公告。`;

  const highlights = activeNotices.map(noticeBrief).filter(Boolean);
  if(highlights.length){
    warning += todayPublished.length
      ? ` 当前仍需重点关注：${highlights.join('；')}。`
      : ` 但以下既有管制措施仍在有效期内，需特别留意：${highlights.join('；')}。`;
  }

  return `<div class="summary-primary">${primary}</div><div class="summary-warning">${warning}</div>`;
}

function renderNotice(n){
  const cls = ['notice', n.status || 'unknown'].join(' ');
  const tags = [
    `<span class="tag source-label ${sourceTagClass(n)}">${esc(sourceLabel(n))}</span>`,
    `<span class="tag ${esc(n.status || '')}">${statusLabel(n.status)}</span>`
  ];
  return `<article class="${cls}">
    <div class="notice-top">
      <div class="notice-title">${esc(n.title)}</div>
      <div class="tags">${tags.join('')}</div>
    </div>
    <table>
      <tr><th>发布机构</th><td>${esc(n.publisher || '未识别')}</td></tr>
      <tr><th>发布日期</th><td>${esc(n.publish_date || '未识别')}</td></tr>
      <tr><th>管制区域</th><td>${esc(n.area || '原文未明确提取')}</td></tr>
      <tr><th>管制时段</th><td>${esc(n.time_text || `${fmtTime(n.start_time)} — ${fmtTime(n.end_time)}`)}</td></tr>
      <tr><th>通告链接</th><td>${n.url ? `<a href="${esc(n.url)}" target="_blank" rel="noopener">查看通告</a>` : '暂无'}</td></tr>
      <tr><th>摘要</th><td>${esc(n.summary || '暂无摘要')}</td></tr>
    </table>
  </article>`;
}

function renderTyphoon(t){
  if(!t || !t.affects_hainan){
    return '<div class="typhoon-card quiet"><div class="typhoon-title">当前未发现影响海南的台风或热带气旋系统</div><p>仅跟踪台风、热带低压等热带气旋信息，不展示普通雷雨或一般天气。</p></div>';
  }
  return `<div class="typhoon-card alert">
    <div class="typhoon-title">${esc(t.headline || t.name || '台风系统影响海南')}</div>
    <div class="typhoon-meta">${esc(t.system_type || '热带气旋')} · ${esc(t.publisher || '气象部门')} · 来源时间 ${esc(t.source_time || '未明确')}</div>
    <p>${esc(t.summary || '')}</p>
    ${t.source_url ? `<a href="${esc(t.source_url)}" target="_blank" rel="noopener">查看气象原文</a>` : ''}
  </div>`;
}

function matchesFilter(n, filter){
  if(!filter) return true;
  if(filter === 'scan-new') return isScanNew(n);
  return n.status === filter;
}

function emptyText(filter){
  return ({
    'scan-new':'本次巡检暂无新增公告。',
    active:'当前暂无正在生效的公告。',
    upcoming:'当前暂无即将生效的公告。',
    ended:'暂无近期结束记录。'
  })[filter] || '暂无符合条件的公告。';
}

function renderNoticeLists(data){
  const current = data.notices || [];
  const ended = data.ended_recent || [];
  const activeSection = $('#activeList')?.closest('.section');
  const endedSection = $('#endedList')?.closest('.section');

  if(!activeFilter){
    if(activeSection) activeSection.style.display = '';
    if(endedSection) endedSection.style.display = '';
    $('#activeList').innerHTML = current.length ? current.map(renderNotice).join('') : '<div class="empty">当前未发现生效中或即将生效的公开管制公告。</div>';
    $('#endedList').innerHTML = ended.length ? ended.map(renderNotice).join('') : '<div class="empty">暂无近期结束记录。</div>';
    return;
  }

  const currentMatches = current.filter(n => matchesFilter(n, activeFilter));
  const endedMatches = ended.filter(n => matchesFilter(n, activeFilter));

  if(currentMatches.length){
    if(activeSection) activeSection.style.display = '';
    $('#activeList').innerHTML = currentMatches.map(renderNotice).join('');
  }else if(activeFilter !== 'ended' && !endedMatches.length){
    if(activeSection) activeSection.style.display = '';
    $('#activeList').innerHTML = `<div class="empty">${emptyText(activeFilter)}</div>`;
  }else if(activeSection){
    activeSection.style.display = 'none';
  }

  if(endedMatches.length){
    if(endedSection) endedSection.style.display = '';
    $('#endedList').innerHTML = endedMatches.map(renderNotice).join('');
  }else if(activeFilter === 'ended'){
    if(endedSection) endedSection.style.display = '';
    $('#endedList').innerHTML = `<div class="empty">${emptyText(activeFilter)}</div>`;
  }else if(endedSection){
    endedSection.style.display = 'none';
  }
}

function renderStats(data){
  const s = data.summary || {};
  const stats = [
    {key:'scan-new',label:'本次巡检新增',value:s.new || 0},
    {key:'active',label:'当前生效',value:s.active || 0},
    {key:'upcoming',label:'即将生效',value:s.upcoming || 0},
    {key:'ended',label:'近期结束',value:s.ended || 0}
  ];
  $('#stats').innerHTML = stats.map(item => `
    <button type="button" class="stat ${activeFilter === item.key ? 'is-selected' : ''}" data-filter="${item.key}" aria-pressed="${activeFilter === item.key}" title="点击筛选，再次点击取消筛选">
      <b>${item.value}</b><span>${item.label}</span>
    </button>`).join('');
}

function render(data){
  latestData = data;
  $('#meta').textContent = `生成时间：${data.generated_at || '未知'} ｜ 数据范围：海南省禁飞、临时空域管制与台风影响公开信息`;
  $('#summary').innerHTML = buildSummaryHtml(data);

  renderStats(data);
  renderNoticeLists(data);
  $('#typhoonBox').innerHTML = renderTyphoon(data.typhoon);

  $('#sourceList').innerHTML = (data.sources || []).map(src => `<div class="source ${src.ok === false ? 'warn':''}"><span>${esc(src.name)}</span><span>${src.ok === false ? '需复核' : '已检索'}</span></div>`).join('');
}

async function load(){
  try{
    const r = await fetch(`./data/latest.json?t=${Date.now()}`, {cache:'no-store'});
    if(!r.ok) throw new Error(`HTTP ${r.status}`);
    render(await r.json());
  }catch(err){
    $('#summary').textContent = `最新数据读取失败：${err.message}`;
    $('#activeList').innerHTML = '<div class="empty">请稍后刷新页面。</div>';
  }
}

$('#stats')?.addEventListener('click', (event) => {
  const card = event.target.closest('.stat[data-filter]');
  if(!card || !latestData) return;
  const selected = card.dataset.filter;
  activeFilter = activeFilter === selected ? null : selected;
  renderStats(latestData);
  renderNoticeLists(latestData);
});

$('#refreshBtn')?.addEventListener('click', load);
load();
