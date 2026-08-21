const $ = (s) => document.querySelector(s);

function fmtTime(v){
  if(!v) return '未明确';
  const d = new Date(v);
  if(Number.isNaN(d.getTime())) return v;
  return new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(d).replaceAll('/','-');
}

function statusLabel(status){
  return ({active:'正在生效',upcoming:'即将生效',ended:'已结束',new:'新发布',unknown:'待核验'})[status] || '待核验';
}

function esc(s=''){
  return String(s).replace(/[&<>'\"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','\"':'&quot;'}[c]));
}

function renderNotice(n){
  const cls = ['notice', n.status || 'unknown'].join(' ');
  const tags = [];
  if(n.is_new_today) tags.push('<span class="tag">今日新发布</span>');
  tags.push(`<span class="tag ${esc(n.status || '')}">${statusLabel(n.status)}</span>`);
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
      <tr><th>原文链接</th><td>${n.url ? `<a href="${esc(n.url)}" target="_blank" rel="noopener">打开原文</a>` : '暂无'}</td></tr>
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

function render(data){
  $('#meta').textContent = `生成时间：${data.generated_at || '未知'} ｜ 数据范围：海南省禁飞、临时空域管制与台风影响公开信息`;
  const s = data.summary || {};
  const newCount = s.new || 0;
  const active = s.active || 0;
  const upcoming = s.upcoming || 0;
  $('#summary').innerHTML = newCount
    ? `今日发现 <strong>${newCount} 条</strong> 新发布的管制公告。当前仍有 <strong>${active} 条</strong> 管制生效，另有 <strong>${upcoming} 条</strong> 即将生效。`
    : `今日未发现海南省新的禁飞/空域管制公告。当前仍有 <strong>${active} 条</strong> 管制生效，另有 <strong>${upcoming} 条</strong> 即将生效。`;

  const stats = [
    ['今日新增', newCount],['当前生效', active],['即将生效', upcoming],['近期结束', s.ended || 0]
  ];
  $('#stats').innerHTML = stats.map(([k,v]) => `<div class="stat"><b>${v}</b><span>${k}</span></div>`).join('');

  const notices = data.notices || [];
  $('#activeList').innerHTML = notices.length ? notices.map(renderNotice).join('') : '<div class="empty">当前未发现生效中或即将生效的公开管制公告。</div>';

  const ended = data.ended_recent || [];
  $('#endedList').innerHTML = ended.length ? ended.map(renderNotice).join('') : '<div class="empty">暂无近期结束记录。</div>';

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

$('#refreshBtn')?.addEventListener('click', load);
load();
