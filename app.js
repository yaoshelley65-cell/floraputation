// ============================================================
// FLORAPUTATION 1.3 — Main Application Logic
// Target: European Floral Breeding Companies (B2B SaaS)
// Language: English only
// ============================================================

// ===== UTILITIES =====
function fmt(n) {
  if (n >= 1000000) return (n/1000000).toFixed(1)+'M';
  if (n >= 1000) return (n/1000).toFixed(1)+'K';
  return n.toString();
}
function scoreColor(s) {
  if (s >= 85) return '#16A34A';
  if (s >= 75) return '#D97706';
  return '#DC2626';
}
function trendHtml(t) {
  if (t > 0) return `<span class="vc-trend up">▲ +${t.toFixed(1)}</span>`;
  return `<span class="vc-trend down">▼ ${t.toFixed(1)}</span>`;
}
function signalHtml(sig) {
  const map = {
    hot: ['sig-hot','🔥 Hot'],
    low: ['sig-low','📊 Low'],
    risk: ['sig-risk','⚠️ Risk'],
    stable: ['sig-stable','— Stable']
  };
  const [cls, label] = map[sig] || map[(sig||'').toLowerCase()] || ['sig-stable','—'];
  return `<span class="rt-signal ${cls}">${label}</span>`;
}
function oppHtml(opp, size='small') {
  const o = OPPORTUNITY_LABELS[opp];
  if (!o) return '';
  if (size === 'large') return `<div class="opportunity-badge-large ${o.color}"><span class="opp-icon">${o.icon}</span><div><div class="opp-label">${o.label}</div><div class="opp-desc">${getOppDesc(opp)}</div></div></div>`;
  return `<span class="vc-opp-badge ${o.color}">${o.icon} ${o.label}</span>`;
}
function getOppDesc(opp) {
  const map = {
    growth: 'High scores from both consumers and growers — ready for scale',
    premium: 'Consumers love it, but growers find it challenging — strong premium pricing signal',
    risk: 'Negative sentiment rising — requires immediate attention',
    regional: 'Strong in select regions — focus resources on proven markets',
    declining: 'Overall momentum declining — reassess investment level'
  };
  return map[opp] || '';
}
function decisionLabel(d) {
  const map = {
    push: { icon: '🚀', label: 'Push', color: 'dec-push' },
    stop: { icon: '🛑', label: 'Phase Out', color: 'dec-stop' },
    price: { icon: '💰', label: 'Raise Price', color: 'dec-price' },
    elite: { icon: '🌿', label: 'Elite Growers Only', color: 'dec-elite' },
    monitor: { icon: '👁', label: 'Monitor', color: 'dec-monitor' }
  };
  return map[d] || { icon: '—', label: 'Unclassified', color: '' };
}
function dimLabel(k) {
  const map = {
    color: 'Colour Appeal', longevity: 'Longevity / Vase Life', visualAppeal: 'Visual Appeal',
    fragrance: 'Fragrance', uniqueness: 'Uniqueness', diseaseResistance: 'Disease Resistance',
    yieldConsistency: 'Yield Consistency', growthStability: 'Growth Stability',
    cultivationDifficulty: 'Cultivation Difficulty', profitability: 'Profitability'
  };
  return map[k] || k;
}

// ===== GENERATE MONTHLY DATA =====
function genMonthlyData(variety, months, field) {
  const base = field === 'consumer' ? variety.consumer
    : field === 'grower' ? variety.grower
    : field === 'distributor' ? variety.retailer
    : variety.score;
  const trend = variety.trend;
  const seed = variety.id * 17 + (field === 'consumer' ? 3 : field === 'grower' ? 7 : 11);
  const data = [];
  for (let i = months - 1; i >= 0; i--) {
    const noise = ((seed * (i + 1) * 2654435761) % 100) / 100 * 8 - 4;
    const t = base - (trend * i / 12) + noise;
    data.push(Math.max(40, Math.min(100, Math.round(t))));
  }
  return data;
}
function genMentionsData(variety, months) {
  const base = (variety.mentionsRaw || 10000) / 12;
  const trend = variety.trend;
  const seed = variety.id * 31;
  const data = [];
  for (let i = months - 1; i >= 0; i--) {
    const noise = ((seed * (i + 1) * 1234567) % 100) / 100 * 0.4 - 0.2;
    const t = base * (1 - trend * i / 1200) * (1 + noise);
    data.push(Math.max(0, Math.round(t)));
  }
  return data;
}
function getMonthLabels(months) {
  const labels = [];
  const now = new Date();
  for (let i = months - 1; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    labels.push(d.toLocaleDateString('en-US', { month: 'short', year: months > 12 ? '2-digit' : undefined }));
  }
  return labels;
}

// ===== STATE =====
let currentPage = 0;
const PAGE_SIZE = 24;
let currentResults = [];
let currentModalId = null;
let currentPeriod = '1y';
let currentRegionView = 'overall';
let portfolioIds = [];
let compareSlots = [null, null, null];
let activeCharts = {};

function destroyChart(id) {
  if (activeCharts[id]) { activeCharts[id].destroy(); delete activeCharts[id]; }
}

// ===== SEARCH ENGINE =====
function searchVarieties(query, category, opp, decision, sort) {
  let results = [...VARIETIES];
  if (query && query.trim()) {
    const q = query.toLowerCase().trim();
    results = results.filter(v =>
      v.variety.toLowerCase().includes(q) ||
      (v.aliases && v.aliases.some(a => a.toLowerCase().includes(q))) ||
      v.crop.toLowerCase().includes(q) ||
      (v.subcategory && v.subcategory.toLowerCase().includes(q)) ||
      (v.series && v.series.toLowerCase().includes(q)) ||
      (v.tags && v.tags.some(t => t.toLowerCase().includes(q)))
    );
  }
  if (category && category !== '') results = results.filter(v => v.crop === category);
  if (opp && opp !== '') results = results.filter(v => v.opportunity === opp);
  if (decision && decision !== '') results = results.filter(v => v.decision === decision);
  // Sort
  if (sort === 'score_desc' || !sort) results.sort((a,b) => b.score - a.score);
  else if (sort === 'score_asc') results.sort((a,b) => a.score - b.score);
  else if (sort === 'trend_desc') results.sort((a,b) => b.trend - a.trend);
  else if (sort === 'mentions_desc') results.sort((a,b) => b.mentions - a.mentions);
  else if (sort === 'consumer_desc') results.sort((a,b) => b.consumer - a.consumer);
  else if (sort === 'grower_desc') results.sort((a,b) => b.grower - a.grower);
  return results;
}

// ===== PERFORM SEARCH =====
function performSearch() {
  const query = (document.getElementById('main-search') || {}).value || '';
  const category = (document.getElementById('filter-crop') || {}).value || '';
  const opp = (document.getElementById('filter-opp') || {}).value || '';
  const decision = (document.getElementById('filter-decision') || {}).value || '';
  const sort = (document.getElementById('filter-sort') || {}).value || '';
  currentResults = searchVarieties(query, category, opp, decision, sort);
  currentPage = 0;
  renderSearchResults(currentResults, true);
  // Scroll to results
  const sec = document.getElementById('search-section');
  if (sec) sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
  // Hide autocomplete
  const ac = document.getElementById('autocomplete-list');
  if (ac) ac.style.display = 'none';
}

// ===== HANDLE SEARCH INPUT (AUTOCOMPLETE) =====
function handleSearchInput(val) {
  const ac = document.getElementById('autocomplete-list');
  if (!ac) return;
  if (!val || val.length < 2) { ac.style.display = 'none'; return; }
  const q = val.toLowerCase();
  const matches = VARIETIES.filter(v =>
    v.variety.toLowerCase().includes(q) ||
    (v.aliases && v.aliases.some(a => a.toLowerCase().includes(q)))
  ).slice(0, 8);
  if (matches.length === 0) { ac.style.display = 'none'; return; }
  ac.innerHTML = matches.map(v =>
    `<div class="ac-item" onclick="selectAutocomplete('${v.variety.replace(/'/g,"\\'")}')">
      <span class="ac-name">${v.variety}</span>
      <span class="ac-cat">${v.crop}</span>
    </div>`
  ).join('');
  ac.style.display = 'block';
}

function selectAutocomplete(name) {
  const inp = document.getElementById('main-search');
  if (inp) inp.value = name;
  const ac = document.getElementById('autocomplete-list');
  if (ac) ac.style.display = 'none';
  performSearch();
}

// ===== QUICK FILTER TAGS =====
function quickFilter(el, decision) {
  document.querySelectorAll('.qt-tag').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  const decSel = document.getElementById('filter-decision');
  if (decSel) decSel.value = decision;
  performSearch();
}

// ===== LOAD MORE =====
function loadMore() {
  currentPage++;
  renderSearchResults(currentResults, false);
}

// ===== RENDER SEARCH RESULTS =====
function renderSearchResults(varieties, reset) {
  const container = document.getElementById('search-results-container');
  const countEl = document.getElementById('results-count');
  const loadMoreBtn = document.querySelector('.load-more-wrap');
  if (!container) return;

  if (countEl) countEl.textContent = `${varieties.length} variet${varieties.length === 1 ? 'y' : 'ies'} found`;

  const start = reset ? 0 : currentPage * PAGE_SIZE;
  const slice = varieties.slice(0, (currentPage + 1) * PAGE_SIZE);

  if (varieties.length === 0) {
    container.innerHTML = `<div class="no-results">
      <div class="no-results-icon">🔍</div>
      <h3>No varieties found</h3>
      <p>Try searching by variety name, category, breeder, or characteristic tags.</p>
    </div>`;
    if (loadMoreBtn) loadMoreBtn.style.display = 'none';
    return;
  }

  container.innerHTML = slice.map(v => {
    const opp = OPPORTUNITY_LABELS[v.opportunity] || {};
    const dec = decisionLabel(v.decision);
    const cvgGap = v.consumer - v.grower;
    const cvgNote = cvgGap >= 12 ? `<div class="low-confidence">⚠️ Consumer–Grower gap: +${cvgGap} pts — premium signal</div>` : '';
    const lowConf = v.confidence < 80 ? `<div class="low-confidence">⚠️ Low confidence (${v.confidence}%)</div>` : '';
    return `<div class="variety-card" onclick="openVarietyModal(${v.id})">
      <div class="vc-top-row">
        <span class="vc-category">${v.crop}</span>
        <span class="vc-decision-badge ${dec.color}">${dec.icon} ${dec.label}</span>
      </div>
      <div class="vc-name">${v.variety}</div>
      <div class="vc-alias">${v.aliases && v.aliases[0] ? v.aliases[0] : ''}</div>
      <div class="vc-score-row">
        <span class="vc-score" style="color:${scoreColor(v.score)}">${v.score}</span>
        <span class="vc-score-max">/100</span>
        ${trendHtml(v.trend)}
      </div>
      <div class="vc-bar-wrap"><div class="vc-bar" style="width:${v.score}%;background:${scoreColor(v.score)}"></div></div>
      <div class="vc-three-scores">
        <div class="vc-mini-score"><div class="vc-mini-label">Consumer</div><div class="vc-mini-val" style="color:${scoreColor(v.consumer)}">${v.consumer}</div></div>
        <div class="vc-mini-score"><div class="vc-mini-label">Distributor</div><div class="vc-mini-val" style="color:${scoreColor(v.retailer)}">${v.retailer}</div></div>
        <div class="vc-mini-score"><div class="vc-mini-label">Grower</div><div class="vc-mini-val" style="color:${scoreColor(v.grower)}">${v.grower}</div></div>
      </div>
      <div class="vc-meta-row">
        <span class="vc-mentions">📊 ${fmt(v.mentions)} mentions</span>
        <span class="vc-opp-badge ${opp.color || ''}">${opp.icon || ''} ${opp.label || ''}</span>
      </div>
      ${cvgNote}${lowConf}
    </div>`;
  }).join('');

  if (loadMoreBtn) loadMoreBtn.style.display = slice.length < varieties.length ? 'flex' : 'none';
}

// ===== OPEN VARIETY MODAL =====
function openVarietyModal(id) {
  const v = VARIETIES.find(x => x.id == id);
  if (!v) return;
  currentModalId = id;
  const modal = document.getElementById('variety-modal');
  if (!modal) return;
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';

  // Header
  document.getElementById('modal-name').textContent = v.variety;
  const aliasEl = document.getElementById('modal-alias'); if (aliasEl) aliasEl.textContent = v.aliases ? v.aliases.join(' / ') : '';
  const cropEl = document.getElementById('modal-crop'); if (cropEl) cropEl.textContent = v.crop;
  const seriesEl = document.getElementById('modal-series'); if (seriesEl) seriesEl.textContent = v.series || '';
  const metaEl = document.getElementById('modal-meta-row'); if (metaEl) metaEl.innerHTML = `<span class="meta-tag">${v.crop}</span>${v.series ? `<span class="meta-tag">${v.series}</span>` : ''}<span class="meta-tag">${v.mentions} mentions</span>`;

  // Decision badge
  const dec = decisionLabel(v.decision);
  const decEl = document.getElementById('modal-decision-badges');
  if (decEl) decEl.innerHTML = `<span class="decision-badge-large ${dec.color}">${dec.icon} ${dec.label}</span>`;

  // Opportunity badge
  const oppEl = document.getElementById('modal-opp-badge');
  if (oppEl) oppEl.innerHTML = oppHtml(v.opportunity, 'large');

  // Score ring
  drawScoreRing('modal-ring-canvas', v.score);
  const sn = document.getElementById('modal-score-num');
  if (sn) sn.textContent = v.score;
  const sv = document.getElementById('modal-verdict');
  if (sv) sv.textContent = v.score >= 90 ? 'Excellent' : v.score >= 80 ? 'Good' : v.score >= 70 ? 'Fair' : 'Weak';
  const tv = document.getElementById('modal-trend-val');
  if (tv) tv.innerHTML = trendHtml(v.trend);
  const mv = document.getElementById('modal-mentions-num');
  if (mv) mv.textContent = fmt(v.mentionsRaw || v.mentions);
  const mt = document.getElementById('modal-mentions-text');
  if (mt) mt.textContent = `${v.mentions} total mentions | Confidence: ${v.confidence}%`;

  // Sentiment bars
  setSentBar('sbar-pos', 'spct-pos', v.positive);
  setSentBar('sbar-neu', 'spct-neu', v.neutral);
  setSentBar('sbar-neg', 'spct-neg', v.negative);
  // Confidence
  const confBar = document.getElementById('conf-bar');
  if (confBar) confBar.style.width = v.confidence + '%';
  const confPct = document.getElementById('conf-pct');
  if (confPct) confPct.textContent = v.confidence + '%';

  // Three-way scores
  setEl('seg-consumer', v.consumer);
  setEl('seg-retailer', v.retailer);
  setEl('seg-grower', v.grower);

  // C-G gap insight
  const gap = v.consumer - v.grower;
  const gapEl = document.getElementById('cg-gap-note');
  if (gapEl) {
    if (gap >= 12) {
      gapEl.textContent = `Consumer score exceeds grower score by ${gap} pts — strong premium pricing signal. Consider exclusive partnerships with specialist growers.`;
      gapEl.style.display = 'block';
      gapEl.className = 'cvg-gap-note gap-premium';
    } else if (gap <= -5) {
      gapEl.textContent = `Grower score exceeds consumer score by ${Math.abs(gap)} pts — supply-side strength, but consumer awareness may need investment.`;
      gapEl.style.display = 'block';
      gapEl.className = 'cvg-gap-note gap-edu';
    } else {
      gapEl.style.display = 'none';
    }
  }

  // Consumer top tags
  const ctags = v.tags ? v.tags.slice(0,3).map(t=>`<span class="cvg-tag">${t}</span>`).join('') : '';
  setElHTML('modal-consumer-tags', ctags);

  // Grower weak tags
  const gtags = v.cgGap >= 15 ? `<span class="cvg-tag cvg-tag-warn">Grower Challenge</span><span class="cvg-tag cvg-tag-warn">Requires Expert Care</span>` : `<span class="cvg-tag">Grower Friendly</span>`;
  setElHTML('modal-grower-tags', gtags);

  // Confidence
  const cb = document.getElementById('modal-confidence-bar');
  if (cb) cb.style.width = v.confidence + '%';
  setEl('modal-confidence-pct', v.confidence + '%');

  // Tags
  const tagsEl = document.getElementById('modal-tags');
  if (tagsEl && v.tags) tagsEl.innerHTML = v.tags.map(t=>`<span class="variety-tag">${t}</span>`).join('');

  // Charts
  currentPeriod = '1y';
  renderModalCharts(v, 12);

  // Region table
  renderRegionTable(v, 'overall');

  // Heatmap row
  renderModalHeatmapRow(v);

  // CVG Deep Dive
  renderCVGDeep(v);

  // AI Insights
  renderAIInsights(v);

  // Strategic Recommendations
  renderStrategicRecs(v);

  // Competitive Benchmark
  renderCompetitiveBenchmark(v);
}

function setEl(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}
function setElHTML(id, html) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = html;
}
function setSentBar(barId, pctId, pct) {
  const bar = document.getElementById(barId);
  const label = document.getElementById(pctId);
  if (bar) bar.style.width = pct + '%';
  if (label) label.textContent = pct + '%';
}

// ===== CLOSE MODAL =====
function closeModal() {
  const modal = document.getElementById('variety-modal');
  if (modal) modal.style.display = 'none';
  document.body.style.overflow = '';
  currentModalId = null;
  // Destroy charts
  ['chart-segments','chart-mentions','chart-benchmark'].forEach(id => destroyChart(id));
}
function handleModalOverlayClick(e) {
  if (e.target.id === 'variety-modal') closeModal();
}

// ===== DRAW SCORE RING =====
function drawScoreRing(canvasId, score) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const cx = canvas.width / 2, cy = canvas.height / 2, r = cx - 10;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  // Background ring
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.strokeStyle = '#E5E7EB';
  ctx.lineWidth = 10;
  ctx.stroke();
  // Score arc
  const angle = (score / 100) * Math.PI * 2 - Math.PI / 2;
  ctx.beginPath();
  ctx.arc(cx, cy, r, -Math.PI / 2, angle);
  ctx.strokeStyle = scoreColor(score);
  ctx.lineWidth = 10;
  ctx.lineCap = 'round';
  ctx.stroke();
}

// ===== SWITCH PERIOD (3M/6M/1Y/3Y) =====
function switchPeriod(btn, period) {
  document.querySelectorAll('.time-btn').forEach(b => {
    if (['3m','6m','1y','3y'].some(p => b.getAttribute('onclick') && b.getAttribute('onclick').includes(`'${p}'`) && b.closest('#variety-modal'))) {
      b.classList.remove('active');
    }
  });
  btn.classList.add('active');
  currentPeriod = period;
  if (!currentModalId) return;
  const v = VARIETIES.find(x => x.id == currentModalId);
  if (!v) return;
  const months = period === '3m' ? 3 : period === '6m' ? 6 : period === '3y' ? 36 : 12;
  renderModalCharts(v, months);
}

// ===== SWITCH REGION VIEW =====
function switchRegionView(btn, view) {
  document.querySelectorAll('#modal-region-view-btns .time-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentRegionView = view;
  if (!currentModalId) return;
  const v = VARIETIES.find(x => x.id == currentModalId);
  if (v) renderRegionTable(v, view);
}

// ===== RENDER MODAL CHARTS =====
function renderModalCharts(v, months) {
  const labels = getMonthLabels(months);

  // Trend chart
  destroyChart('chart-segments');
  const tc = document.getElementById('chart-segments');
  if (tc) {
    activeCharts['chart-segments'] = new Chart(tc, {
      type: 'line',
      data: {
        labels,
        datasets: [
          { label: 'Overall', data: genMonthlyData(v, months, 'overall'), borderColor: '#16A34A', backgroundColor: 'rgba(22,163,74,0.1)', tension: 0.4, fill: true, pointRadius: 3 },
          { label: 'Consumer', data: genMonthlyData(v, months, 'consumer'), borderColor: '#2563EB', backgroundColor: 'transparent', tension: 0.4, borderDash: [4,2], pointRadius: 2 },
          { label: 'Distributor', data: genMonthlyData(v, months, 'distributor'), borderColor: '#7C3AED', backgroundColor: 'transparent', tension: 0.4, borderDash: [4,2], pointRadius: 2 },
          { label: 'Grower', data: genMonthlyData(v, months, 'grower'), borderColor: '#D97706', backgroundColor: 'transparent', tension: 0.4, borderDash: [4,2], pointRadius: 2 }
        ]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } } }, scales: { y: { min: 40, max: 100, grid: { color: '#F3F4F6' } }, x: { grid: { display: false } } } }
    });
  }

  // Mentions chart
  destroyChart('chart-mentions');
  const mc = document.getElementById('chart-mentions');
  if (mc) {
    activeCharts['chart-mentions'] = new Chart(mc, {
      type: 'bar',
      data: {
        labels,
        datasets: [{ label: 'Mentions', data: genMentionsData(v, months), backgroundColor: 'rgba(22,163,74,0.7)', borderRadius: 4 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { grid: { color: '#F3F4F6' } }, x: { grid: { display: false } } } }
    });
  }

  // CVG comparison chart
  // CVG chart - reuse chart-segments canvas (skip if already rendered)
  const cc = null; // document.getElementById('modal-cvg-chart');
  if (cc) {
    activeCharts['modal-cvg-chart'] = new Chart(cc, {
      type: 'line',
      data: {
        labels,
        datasets: [
          { label: 'Consumer', data: genMonthlyData(v, months, 'consumer'), borderColor: '#2563EB', backgroundColor: 'rgba(37,99,235,0.1)', tension: 0.4, fill: false, pointRadius: 3 },
          { label: 'Distributor', data: genMonthlyData(v, months, 'distributor'), borderColor: '#7C3AED', backgroundColor: 'transparent', tension: 0.4, fill: false, pointRadius: 3 },
          { label: 'Grower', data: genMonthlyData(v, months, 'grower'), borderColor: '#D97706', backgroundColor: 'rgba(217,119,6,0.1)', tension: 0.4, fill: false, pointRadius: 3 }
        ]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } } }, scales: { y: { min: 40, max: 100, grid: { color: '#F3F4F6' } }, x: { grid: { display: false } } } }
    });
  }

  // Radar chart
  // Radar chart - skip (no canvas in HTML)
  const rc = null; // document.getElementById('modal-radar-chart');
  if (rc) {
    const dims = ['color','longevity','visualAppeal','diseaseResistance','yieldConsistency','profitability'];
    const labels2 = dims.map(dimLabel);
    const consumerVals = dims.map(d => v.consumer);
    const growerVals = dims.map(d => v.grower);
    activeCharts['modal-radar-chart'] = new Chart(rc, {
      type: 'radar',
      data: {
        labels: labels2,
        datasets: [
          { label: 'Consumer', data: consumerVals, borderColor: '#2563EB', backgroundColor: 'rgba(37,99,235,0.15)', pointRadius: 4 },
          { label: 'Grower', data: growerVals, borderColor: '#D97706', backgroundColor: 'rgba(217,119,6,0.15)', pointRadius: 4 }
        ]
      },
      options: { responsive: true, maintainAspectRatio: false, scales: { r: { min: 40, max: 100, ticks: { display: false }, grid: { color: '#E5E7EB' }, pointLabels: { font: { size: 10 } } } }, plugins: { legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } } } }
    });
  }
}

// ===== RENDER REGION TABLE =====
function renderRegionTable(v, view) {
  const tbody = document.getElementById('region-tbody');
  if (!tbody) return;
  view = view || currentRegionView || 'overall';
  tbody.innerHTML = v.regional.map(r => {
    const score = view === 'consumer' ? r.consumer
      : view === 'grower' ? r.grower
      : view === 'retailer' ? r.retailer
      : r.score;
    const bar = `<div class="mini-bar-wrap"><div class="mini-bar" style="width:${score}%;background:${scoreColor(score)}"></div></div>`;
    return `<tr>
      <td><strong>${r.region}</strong></td>
      <td>${bar}</td>
      <td><span style="color:${scoreColor(r.consumer)};font-weight:600">${r.consumer}</span></td>
      <td><span style="color:${scoreColor(r.grower)};font-weight:600">${r.grower}</span></td>
      <td><span style="color:${scoreColor(r.retailer)};font-weight:600">${r.retailer}</span></td>
      <td>${fmt(r.mentions)}</td>
      <td>${trendHtml(r.trend)}</td>
      <td>${signalHtml(r.signal)}</td>
    </tr>`;
  }).join('');
}

// ===== RENDER MODAL HEATMAP ROW =====
function renderModalHeatmapRow(v) {
  // modal-heatmap-row not in HTML - skip
  const el = null; // document.getElementById('modal-heatmap-row');
  if (!el) return;
  const regions = v.regional;
  const maxScore = Math.max(...regions.map(r => r.score));
  el.innerHTML = regions.map(r => {
    const intensity = r.score / 100;
    const bg = `rgba(22,163,74,${intensity.toFixed(2)})`;
    return `<div class="heatmap-cell" style="background:${bg};color:${intensity > 0.6 ? '#fff' : '#1F2937'}">
      <div class="hm-region">${r.region}</div>
      <div class="hm-score">${r.score}</div>
      <div class="hm-trend">${r.trend > 0 ? '▲' : '▼'} ${Math.abs(r.trend).toFixed(1)}</div>
    </div>`;
  }).join('');
}

// ===== RENDER CVG DEEP DIVE =====
function renderCVGDeep(v) {
  const consumerEl = document.getElementById('consumer-dims');
  const growerEl = document.getElementById('grower-dims');
  const gap = v.consumer - v.grower;
  if (consumerEl) {
    const consumerStrengths = v.tags ? v.tags.filter(t => !t.toLowerCase().includes('challenge')).slice(0,4) : ['Colour Appeal','Visual Impact','Market Demand'];
    consumerEl.innerHTML = `
      <div class="cvg-score-large" style="color:#2563EB">${v.consumer}<span style="font-size:14px;color:#6B7280">/100</span></div>
      <div class="cvg-gap-info" style="margin:8px 0;font-size:13px;color:#374151">Consumer score: <strong style="color:#2563EB">${v.consumer}</strong></div>
      ${consumerStrengths.map(s => `<div class="cvg-tag" style="margin:3px 0;display:inline-block">${s}</div>`).join('')}
      ${gap >= 12 ? `<div class="cvg-gap-note gap-premium" style="margin-top:8px">+${gap} pts above grower — premium pricing signal</div>` : ''}
    `;
  }
  if (growerEl) {
    const growerChallenges = v.cgGap >= 15 ? ['Cultivation Complexity','Requires Expert Care','Higher Input Cost'] : ['Stable Growth','Consistent Yield','Manageable Care'];
    growerEl.innerHTML = `
      <div class="cvg-score-large" style="color:#D97706">${v.grower}<span style="font-size:14px;color:#6B7280">/100</span></div>
      <div class="cvg-gap-info" style="margin:8px 0;font-size:13px;color:#374151">Grower score: <strong style="color:#D97706">${v.grower}</strong></div>
      ${growerChallenges.map(s => `<div class="cvg-tag ${v.cgGap >= 15 ? 'cvg-tag-warn' : ''}" style="margin:3px 0;display:inline-block">${s}</div>`).join('')}
      ${v.cgGap >= 15 ? `<div class="cvg-gap-note gap-edu" style="margin-top:8px">Recommend specialist grower partnerships</div>` : ''}
    `;
  }
}

// ===== RENDER AI INSIGHTS =====
function renderAIInsights(v) {
  const el = document.getElementById('ai-insights-grid');
  if (!el) return;
  const insights = generateAIInsights(v);
  el.innerHTML = insights.map(ins =>
    `<div class="ai-card ai-${ins.type}">
      <div class="ai-icon">${ins.icon}</div>
      <div class="ai-body">
        <div class="ai-title">${ins.title}</div>
        <div class="ai-text">${ins.text}</div>
      </div>
    </div>`
  ).join('');
}

function generateAIInsights(v) {
  const insights = [];
  const gap = v.consumer - v.grower;
  const topRegion = v.regional.sort((a,b) => b.score - a.score)[0];
  const weakRegion = v.regional.sort((a,b) => a.score - b.score)[0];

  // Regional insight
  insights.push({
    type: 'region', icon: '🌍',
    title: 'Regional Performance',
    text: `Strongest market: <strong>${topRegion.region}</strong> (${topRegion.score}/100, ${fmt(topRegion.mentions)} mentions). Lowest engagement: <strong>${weakRegion.region}</strong> (${weakRegion.score}/100). ${topRegion.trend > 0 ? `Momentum in ${topRegion.region} is accelerating (+${topRegion.trend.toFixed(1)}).` : `Momentum in ${topRegion.region} is softening (${topRegion.trend.toFixed(1)}).`}`
  });

  // Consumer vs Grower
  if (gap >= 12) {
    insights.push({
      type: 'premium', icon: '💎',
      title: 'Premium Pricing Signal',
      text: `Consumer enthusiasm significantly outpaces grower satisfaction by <strong>${gap} points</strong>. This variety commands premium retail positioning. Recommend restricting supply to a curated network of specialist growers who can consistently deliver quality.`
    });
  } else if (gap <= -8) {
    insights.push({
      type: 'edu', icon: '📣',
      title: 'Consumer Awareness Gap',
      text: `Growers rate this variety highly (+${Math.abs(gap)} pts above consumers), suggesting strong cultivation performance but limited end-market visibility. Invest in consumer-facing marketing and retail education to unlock demand.`
    });
  } else {
    insights.push({
      type: 'balanced', icon: '⚖️',
      title: 'Balanced Stakeholder Sentiment',
      text: `Consumer and grower scores are well-aligned (gap: ${gap > 0 ? '+' : ''}${gap} pts), indicating a stable, scalable variety. Suitable for broad commercial rollout with standard support.`
    });
  }

  // Trend
  if (v.trend >= 3) {
    insights.push({
      type: 'growth', icon: '📈',
      title: 'Strong Growth Momentum',
      text: `Mention volume is growing at +${v.trend.toFixed(1)}% per month. This variety is gaining organic traction — consider increasing production allocation and proactive trade show presence.`
    });
  } else if (v.trend <= -2) {
    insights.push({
      type: 'risk', icon: '⚠️',
      title: 'Declining Momentum',
      text: `Mention volume has declined ${v.trend.toFixed(1)}% per month over the tracked period. Review negative feedback themes and assess whether product improvement, repositioning, or phase-out is warranted.`
    });
  }

  // Sentiment
  if (v.negative >= 25) {
    insights.push({
      type: 'risk', icon: '🔴',
      title: 'Elevated Negative Sentiment',
      text: `${v.negative}% of tracked mentions carry negative sentiment. Grower score (${v.grower}) is significantly below consumer score (${v.consumer}). Proactive engagement with grower communities is recommended.`
    });
  }

  // Decision-specific
  if (v.decision === 'push') {
    insights.push({ type: 'growth', icon: '🚀', title: 'Recommended Action: Push', text: 'This variety meets the criteria for active commercial promotion. Prioritise in catalogue features, trade presentations, and grower incentive programmes.' });
  } else if (v.decision === 'stop') {
    insights.push({ type: 'risk', icon: '🛑', title: 'Recommended Action: Phase Out', text: 'Declining scores and low market traction suggest diminishing returns. Consider a structured wind-down: reduce production targets, redirect resources to higher-performing varieties.' });
  } else if (v.decision === 'price') {
    insights.push({ type: 'premium', icon: '💰', title: 'Recommended Action: Raise Price', text: 'Strong consumer demand with constrained supply-side capacity supports a price increase. A 10–20% price uplift is likely sustainable without significant volume loss.' });
  } else if (v.decision === 'elite') {
    insights.push({ type: 'premium', icon: '🌿', title: 'Recommended Action: Elite Growers Only', text: 'Cultivation complexity limits broad distribution. Restrict to a vetted network of high-capability growers. This protects brand reputation and enables premium positioning.' });
  }

  return insights;
}

// ===== RENDER STRATEGIC RECOMMENDATIONS =====
function renderStrategicRecs(v) {
  const el = document.getElementById('ai-insights-grid');
  if (!el) return;
  const recs = generateStrategicRecs(v);
  // Append strategic recs after AI insights
  el.innerHTML += recs.map(r =>
    `<div class="strat-card">
      <div class="strat-priority priority-${r.priority}">${r.priority.toUpperCase()}</div>
      <div class="strat-icon">${r.icon}</div>
      <div class="strat-title">${r.title}</div>
      <div class="strat-text">${r.text}</div>
      <div class="strat-action">${r.action}</div>
    </div>`
  ).join('');
}

function generateStrategicRecs(v) {
  const recs = [];
  const gap = v.consumer - v.grower;
  const topRegion = [...v.regional].sort((a,b) => b.score - a.score)[0];
  const weakRegion = [...v.regional].sort((a,b) => a.score - b.score)[0];

  if (v.decision === 'push' || v.score >= 82) {
    recs.push({ priority: 'high', icon: '🚀', title: 'Scale Commercial Distribution', text: `With an overall score of ${v.score}/100 and positive momentum (+${v.trend.toFixed(1)}%/mo), this variety is ready for broad market rollout.`, action: 'Action: Feature in Q2 catalogue, increase production allocation by 20–30%.' });
  }
  if (gap >= 12) {
    recs.push({ priority: 'high', icon: '💎', title: 'Implement Premium Pricing Tier', text: `Consumer demand (${v.consumer}) significantly exceeds grower supply capability (${v.grower}). This supply-demand imbalance supports a price premium.`, action: `Action: Introduce a premium SKU at 15–25% above standard list price. Partner with ${topRegion.region} specialist growers.` });
  }
  if (topRegion.score >= 85 && weakRegion.score <= 70) {
    recs.push({ priority: 'medium', icon: '🌍', title: 'Concentrate Resources on Proven Markets', text: `${topRegion.region} shows strong performance (${topRegion.score}/100). ${weakRegion.region} remains underdeveloped (${weakRegion.score}/100).`, action: `Action: Redirect 60% of marketing spend to ${topRegion.region}. Pilot a targeted trade programme in ${weakRegion.region} before committing.` });
  }
  if (v.negative >= 20) {
    recs.push({ priority: 'medium', icon: '🔧', title: 'Address Negative Feedback Loop', text: `${v.negative}% negative sentiment is above the 15% threshold. Unresolved issues risk accelerating decline.`, action: 'Action: Conduct grower focus groups within 60 days. Identify top 2 complaint themes and issue technical guidance notes.' });
  }
  if (v.trend >= 4) {
    recs.push({ priority: 'medium', icon: '📣', title: 'Capitalise on Organic Momentum', text: `Mention growth of +${v.trend.toFixed(1)}%/mo indicates rising organic interest. This is the optimal window for amplification.`, action: 'Action: Engage top 5 social media advocates. Submit for industry awards. Prepare press release for trade media.' });
  }
  if (v.decision === 'stop') {
    recs.push({ priority: 'high', icon: '📉', title: 'Initiate Structured Phase-Out', text: 'Declining scores and weak market traction indicate this variety has passed its commercial peak.', action: 'Action: Reduce production by 50% in next season. Notify key accounts 6 months in advance. Redirect resources to pipeline varieties.' });
  }
  if (recs.length === 0) {
    recs.push({ priority: 'low', icon: '👁', title: 'Continue Monitoring', text: 'This variety shows stable but unremarkable performance. No immediate action required.', action: 'Action: Review at next quarterly planning cycle. Set alert for score change >5 pts.' });
  }
  return recs;
}

// ===== RENDER COMPETITIVE BENCHMARK =====
function renderCompetitiveBenchmark(v) {
  const titleEl = document.getElementById('benchmark-title');
  const descEl = document.getElementById('benchmark-desc');
  const canvas = document.getElementById('chart-benchmark');
  if (!canvas) return;
  const peers = VARIETIES.filter(x => x.crop === v.crop && x.id !== v.id)
    .sort((a,b) => b.score - a.score).slice(0, 4);
  const allInCat = VARIETIES.filter(x => x.crop === v.crop);
  const catAvg = Math.round(allInCat.reduce((s,x)=>s+x.score,0)/allInCat.length);
  const rank = [...allInCat].sort((a,b)=>b.score-a.score).findIndex(x=>x.id===v.id)+1;
  if (titleEl) titleEl.textContent = `Competitive Benchmark — ${v.crop} (Rank #${rank} of ${allInCat.length})`;
  if (descEl) descEl.textContent = `Category average: ${catAvg}/100. ${v.variety} scores ${v.score >= catAvg ? '+' : ''}${v.score - catAvg} vs. category average.`;
  destroyChart('chart-benchmark');
  const chartVarieties = [v, ...peers];
  activeCharts['chart-benchmark'] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: chartVarieties.map(x => x.variety.length > 18 ? x.variety.slice(0,18)+'…' : x.variety),
      datasets: [
        { label: 'Overall', data: chartVarieties.map(x => x.score), backgroundColor: chartVarieties.map(x => x.id === v.id ? '#16A34A' : '#BBF7D0'), borderRadius: 4 },
        { label: 'Consumer', data: chartVarieties.map(x => x.consumer), backgroundColor: chartVarieties.map(x => x.id === v.id ? '#2563EB' : '#BFDBFE'), borderRadius: 4 },
        { label: 'Grower', data: chartVarieties.map(x => x.grower), backgroundColor: chartVarieties.map(x => x.id === v.id ? '#D97706' : '#FDE68A'), borderRadius: 4 }
      ]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } } }, scales: { y: { min: 40, max: 100, grid: { color: '#F3F4F6' } }, x: { grid: { display: false }, ticks: { font: { size: 10 } } } } }
  });
}

// ===== SWITCH DECISION TAB =====
function switchDecision(type) {
  document.querySelectorAll('.opp-tab').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.opp-tab').forEach(b => {
    if (b.getAttribute('onclick') && b.getAttribute('onclick').includes(`'${type}'`)) b.classList.add('active');
  });
  renderDecisionGrid(type);
}

function renderDecisionGrid(type) {
  const el = document.getElementById('decision-grid');
  if (!el) return;
  const varieties = VARIETIES.filter(v => v.decision === type).sort((a,b) => b.score - a.score);
  if (varieties.length === 0) {
    el.innerHTML = '<p class="text-muted" style="padding:24px">No varieties classified in this category.</p>';
    return;
  }
  el.innerHTML = varieties.map(v => {
    const opp = OPPORTUNITY_LABELS[v.opportunity] || {};
    return `<div class="decision-variety-row" onclick="openVarietyModal(${v.id})">
      <div class="dvr-name">${v.variety}</div>
      <div class="dvr-cat">${v.crop}</div>
      <div class="dvr-score" style="color:${scoreColor(v.score)}">${v.score}</div>
      <div class="dvr-trend">${trendHtml(v.trend)}</div>
      <div class="dvr-opp"><span class="vc-opp-badge ${opp.color||''}">${opp.icon||''} ${opp.label||''}</span></div>
    </div>`;
  }).join('');
}

// ===== GLOBAL HEATMAP =====
function renderHeatmap() {
  const el = document.getElementById('heatmap-container');
  if (!el) return;
  const crop = (document.getElementById('heatmap-crop') || {}).value || '';
  const metric = (document.getElementById('heatmap-metric') || {}).value || 'score';
  const limit = parseInt((document.getElementById('heatmap-limit') || {}).value || '20');
  let varieties = VARIETIES;
  if (crop) varieties = varieties.filter(v => v.crop === crop);
  varieties = varieties.sort((a,b) => b.score - a.score).slice(0, limit);
  const regions = ['Netherlands', 'Germany', 'France', 'UK', 'USA', 'Japan', 'China', 'Australia'];

  // Header row
  let html = `<div class="hm-grid" style="grid-template-columns: 200px repeat(${regions.length}, 1fr)">`;
  html += `<div class="hm-header-cell">Variety</div>`;
  regions.forEach(r => html += `<div class="hm-header-cell">${r}</div>`);

  varieties.forEach(v => {
    html += `<div class="hm-variety-cell" onclick="openVarietyModal(${v.id})">${v.variety}<br><small>${v.crop}</small></div>`;
    regions.forEach(r => {
      const rd = v.regional.find(x => x.region === r);
      const score = rd ? (metric === 'consumer' ? rd.consumer : metric === 'grower' ? rd.grower : metric === 'distributor' ? rd.retailer : metric === 'mentions' ? Math.round(rd.mentions/100) : rd.score) : 0;
      const displayScore = rd ? (metric === 'mentions' ? fmt(rd.mentions) : score) : '—';
      const intensity = rd ? score / 100 : 0;
      const bg = rd ? `rgba(22,163,74,${Math.max(0.05, intensity).toFixed(2)})` : '#F9FAFB';
      const color = intensity > 0.65 ? '#fff' : '#1F2937';
      html += `<div class="hm-data-cell" style="background:${bg};color:${color}">${displayScore}</div>`;
    });
  });
  html += '</div>';
  el.innerHTML = html;
}

// ===== PORTFOLIO =====
function addToPortfolio(id) {
  if (!portfolioIds.includes(id)) {
    portfolioIds.push(id);
    updatePortfolioCount();
    showToast('Added to Portfolio');
  }
}
function clearPortfolio() {
  portfolioIds = [];
  updatePortfolioCount();
  const el = document.getElementById('portfolio-list');
  if (el) el.innerHTML = '<p class="text-muted">No varieties added yet.</p>';
  const res = document.getElementById('portfolio-results');
  if (res) res.style.display = 'none';
}
function updatePortfolioCount() {
  const el = document.getElementById('portfolio-count');
  if (el) el.textContent = portfolioIds.length;
}
function handlePortfolioInput(val) {
  const ac = document.getElementById('portfolio-autocomplete');
  if (!ac) return;
  if (!val || val.length < 2) { ac.style.display = 'none'; return; }
  const q = val.toLowerCase();
  const matches = VARIETIES.filter(v => v.variety.toLowerCase().includes(q)).slice(0, 6);
  if (matches.length === 0) { ac.style.display = 'none'; return; }
  ac.innerHTML = matches.map(v =>
    `<div class="ac-item" onclick="addPortfolioVariety(${v.id},'${v.variety.replace(/'/g,"\\'")}')">
      <span class="ac-name">${v.variety}</span><span class="ac-cat">${v.crop}</span>
    </div>`
  ).join('');
  ac.style.display = 'block';
}
function addPortfolioVariety(id, name) {
  addToPortfolio(id);
  const inp = document.getElementById('portfolio-input');
  if (inp) inp.value = '';
  const ac = document.getElementById('portfolio-autocomplete');
  if (ac) ac.style.display = 'none';
  renderPortfolioList();
}
function renderPortfolioList() {
  const el = document.getElementById('portfolio-list');
  if (!el) return;
  if (portfolioIds.length === 0) {
    el.innerHTML = '<p class="text-muted">No varieties added yet.</p>';
    return;
  }
  el.innerHTML = portfolioIds.map(id => {
    const v = VARIETIES.find(x => x.id == id);
    if (!v) return '';
    const dec = decisionLabel(v.decision);
    return `<div class="portfolio-item">
      <span class="pi-name">${v.variety}</span>
      <span class="pi-cat">${v.crop}</span>
      <span class="pi-score" style="color:${scoreColor(v.score)}">${v.score}</span>
      <span class="pi-dec ${dec.color}">${dec.icon}</span>
      <button class="pi-remove" onclick="removeFromPortfolio(${id})">✕</button>
    </div>`;
  }).join('');
}
function removeFromPortfolio(id) {
  portfolioIds = portfolioIds.filter(x => x !== id);
  updatePortfolioCount();
  renderPortfolioList();
}
function analysePortfolio() {
  if (portfolioIds.length === 0) { showToast('Add at least one variety to analyse.'); return; }
  const el = document.getElementById('portfolio-results');
  if (el) el.style.display = 'block';
  const emptyEl = document.getElementById('portfolio-empty');
  if (emptyEl) emptyEl.style.display = 'none';
  renderPortfolioAnalysis();
}
function renderPortfolioAnalysis() {
  const varieties = portfolioIds.map(id => VARIETIES.find(x => x.id == id)).filter(Boolean);
  const avgScore = Math.round(varieties.reduce((s,v)=>s+v.score,0)/varieties.length);
  const avgConsumer = Math.round(varieties.reduce((s,v)=>s+v.consumer,0)/varieties.length);
  const avgGrower = Math.round(varieties.reduce((s,v)=>s+v.grower,0)/varieties.length);
  const pushCount = varieties.filter(v=>v.decision==='push').length;
  const stopCount = varieties.filter(v=>v.decision==='stop').length;
  const priceCount = varieties.filter(v=>v.decision==='price').length;
  const eliteCount = varieties.filter(v=>v.decision==='elite').length;
  const riskCount = varieties.filter(v=>v.negative>=25).length;

  const summaryEl = document.getElementById('portfolio-summary');
  if (summaryEl) {
    summaryEl.innerHTML = `
      <div class="port-kpi"><div class="port-kpi-val">${varieties.length}</div><div class="port-kpi-label">Varieties</div></div>
      <div class="port-kpi"><div class="port-kpi-val" style="color:${scoreColor(avgScore)}">${avgScore}</div><div class="port-kpi-label">Avg Score</div></div>
      <div class="port-kpi"><div class="port-kpi-val" style="color:#2563EB">${avgConsumer}</div><div class="port-kpi-label">Avg Consumer</div></div>
      <div class="port-kpi"><div class="port-kpi-val" style="color:#D97706">${avgGrower}</div><div class="port-kpi-label">Avg Grower</div></div>
      <div class="port-kpi"><div class="port-kpi-val" style="color:#16A34A">${pushCount}</div><div class="port-kpi-label">Push</div></div>
      <div class="port-kpi"><div class="port-kpi-val" style="color:#DC2626">${stopCount}</div><div class="port-kpi-label">Phase Out</div></div>
      <div class="port-kpi"><div class="port-kpi-val" style="color:#7C3AED">${priceCount}</div><div class="port-kpi-label">Raise Price</div></div>
      <div class="port-kpi"><div class="port-kpi-val" style="color:#D97706">${eliteCount}</div><div class="port-kpi-label">Elite Only</div></div>
      <div class="port-kpi"><div class="port-kpi-val" style="color:${riskCount>0?'#DC2626':'#16A34A'}">${riskCount}</div><div class="port-kpi-label">At Risk</div></div>
    `;
  }

  // Portfolio risk assessment
  const riskEl = document.getElementById('portfolio-risk');
  if (riskEl) {
    const riskScore = Math.round((stopCount * 3 + riskCount * 2 + varieties.filter(v=>v.trend<0).length) / varieties.length * 10);
    const riskLevel = riskScore >= 5 ? 'High' : riskScore >= 3 ? 'Medium' : 'Low';
    const riskColor = riskScore >= 5 ? '#DC2626' : riskScore >= 3 ? '#D97706' : '#16A34A';
    riskEl.innerHTML = `
      <div class="risk-header">
        <div class="risk-level" style="color:${riskColor}">Portfolio Risk: <strong>${riskLevel}</strong></div>
        <div class="risk-score">Risk Index: ${riskScore}/10</div>
      </div>
      <div class="risk-breakdown">
        ${stopCount > 0 ? `<div class="risk-item">⚠️ ${stopCount} variet${stopCount>1?'ies':'y'} flagged for phase-out</div>` : ''}
        ${riskCount > 0 ? `<div class="risk-item">🔴 ${riskCount} variet${riskCount>1?'ies':'y'} with elevated negative sentiment (≥25%)</div>` : ''}
        ${varieties.filter(v=>v.trend<0).length > 0 ? `<div class="risk-item">📉 ${varieties.filter(v=>v.trend<0).length} variet${varieties.filter(v=>v.trend<0).length>1?'ies':'y'} with declining trend</div>` : ''}
        ${riskScore < 3 ? `<div class="risk-item risk-ok">✅ Portfolio is well-balanced with low risk exposure</div>` : ''}
      </div>
      <div class="risk-recs">
        <strong>Strategic Recommendations:</strong>
        <ul>
          ${pushCount >= varieties.length * 0.5 ? '<li>Strong push pipeline — consider accelerating go-to-market for top performers.</li>' : ''}
          ${stopCount >= 2 ? '<li>Multiple phase-out candidates — initiate wind-down planning to free up resources.</li>' : ''}
          ${priceCount >= 1 ? `<li>${priceCount} variet${priceCount>1?'ies':'y'} support price increases — implement before next season pricing cycle.</li>` : ''}
          ${avgScore < 75 ? '<li>Portfolio average score below 75 — review underperformers and consider refreshing with new introductions.</li>' : '<li>Portfolio average score is healthy — maintain current investment levels.</li>'}
        </ul>
      </div>`;
  }

  // Render portfolio chart
  renderPortfolioChart(varieties);
}

function renderPortfolioChart(varieties) {
  destroyChart('portfolio-chart');
  const canvas = document.getElementById('portfolio-chart');
  if (!canvas) return;
  activeCharts['portfolio-chart'] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: varieties.map(v => v.variety.length > 20 ? v.variety.substring(0,18)+'…' : v.variety),
      datasets: [
        { label: 'Consumer Score', data: varieties.map(v=>v.consumer), backgroundColor: 'rgba(37,99,235,0.7)', borderRadius: 3 },
        { label: 'Distributor Score', data: varieties.map(v=>v.retailer), backgroundColor: 'rgba(124,58,237,0.7)', borderRadius: 3 },
        { label: 'Grower Score', data: varieties.map(v=>v.grower), backgroundColor: 'rgba(217,119,6,0.7)', borderRadius: 3 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } } },
      scales: { y: { min: 40, max: 100, grid: { color: '#F3F4F6' } }, x: { grid: { display: false }, ticks: { font: { size: 10 } } } }
    }
  });
}

// ===== COMPARE SLOTS =====
function openSlotSearch(slotIndex) {
  const modal = document.getElementById('slot-modal');
  if (!modal) return;
  modal.style.display = 'flex';
  modal.dataset.slot = slotIndex;
  const inp = document.getElementById('slot-search-input');
  if (inp) { inp.value = ''; inp.focus(); }
  renderSlotSearchResults('');
}
function closeSlotModal(e) {
  if (!e || e.target.id === 'slot-modal') {
    const modal = document.getElementById('slot-modal');
    if (modal) modal.style.display = 'none';
  }
}
function handleSlotSearch(val) {
  renderSlotSearchResults(val);
}
function renderSlotSearchResults(query) {
  const el = document.getElementById('slot-search-results');
  if (!el) return;
  const q = query.toLowerCase();
  const matches = VARIETIES.filter(v =>
    !q || v.variety.toLowerCase().includes(q) || v.crop.toLowerCase().includes(q)
  ).sort((a,b)=>b.score-a.score).slice(0, 12);
  el.innerHTML = matches.map(v =>
    `<div class="slot-result-item" onclick="selectSlotVariety(${v.id})">
      <span class="sr-name">${v.variety}</span>
      <span class="sr-cat">${v.crop}</span>
      <span class="sr-score" style="color:${scoreColor(v.score)}">${v.score}</span>
    </div>`
  ).join('');
}
function selectSlotVariety(id) {
  const modal = document.getElementById('slot-modal');
  if (!modal) return;
  const slot = parseInt(modal.dataset.slot);
  compareSlots[slot] = id;
  modal.style.display = 'none';
  renderCompareSlots();
}
function renderCompareSlots() {
  for (let i = 0; i < 3; i++) {
    const slot = document.getElementById(`compare-slot-${i}`);
    if (!slot) continue;
    const id = compareSlots[i];
    if (!id) {
      slot.innerHTML = `<button class="slot-add-btn" onclick="openSlotSearch(${i})">+ Add Variety</button>`;
    } else {
      const v = VARIETIES.find(x => x.id == id);
      if (!v) continue;
      slot.innerHTML = `
        <div class="slot-filled">
          <button class="slot-remove" onclick="compareSlots[${i}]=null;renderCompareSlots()">✕</button>
          <div class="slot-name">${v.variety}</div>
          <div class="slot-cat">${v.crop}</div>
          <div class="slot-score" style="color:${scoreColor(v.score)}">${v.score}/100</div>
        </div>`;
    }
  }
  renderCompareCharts();
}
function renderCompareCharts() {
  const filled = compareSlots.filter(Boolean);
  if (filled.length < 2) return;
  const varieties = filled.map(id => VARIETIES.find(x => x.id == id)).filter(Boolean);
  const colors = ['#16A34A','#2563EB','#D97706'];

  // Radar
  destroyChart('compare-radar');
  const rc = document.getElementById('compare-radar');
  if (rc) {
    const dims = ['color','longevity','visualAppeal','diseaseResistance','yieldConsistency','profitability'];
    activeCharts['compare-radar'] = new Chart(rc, {
      type: 'radar',
      data: {
        labels: dims.map(dimLabel),
        datasets: varieties.map((v,i) => ({
          label: v.variety,
          data: dims.map(d => v.score),
          borderColor: colors[i], backgroundColor: colors[i].replace(')',',0.1)').replace('rgb','rgba'), pointRadius: 4
        }))
      },
      options: { responsive: true, maintainAspectRatio: false, scales: { r: { min: 40, max: 100, ticks: { display: false }, grid: { color: '#E5E7EB' }, pointLabels: { font: { size: 10 } } } }, plugins: { legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } } } }
    });
  }

  // Trend
  destroyChart('compare-trend');
  const tc = document.getElementById('compare-trend');
  if (tc) {
    const labels = getMonthLabels(12);
    activeCharts['compare-trend'] = new Chart(tc, {
      type: 'line',
      data: {
        labels,
        datasets: varieties.map((v,i) => ({
          label: v.variety, data: genMonthlyData(v, 12, 'overall'),
          borderColor: colors[i], backgroundColor: 'transparent', tension: 0.4, pointRadius: 3
        }))
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } } }, scales: { y: { min: 40, max: 100, grid: { color: '#F3F4F6' } }, x: { grid: { display: false } } } }
    });
  }

  // Compare table
  const tbl = document.getElementById('compare-table-body');
  if (tbl) {
    const rows = [
      ['Overall Score', v => v.score],
      ['Consumer Score', v => v.consumer],
      ['Distributor Score', v => v.retailer],
      ['Grower Score', v => v.grower],
      ['Monthly Trend', v => `${v.trend > 0 ? '+' : ''}${v.trend.toFixed(1)}%`],
      ['Total Mentions', v => fmt(v.mentions)],
      ['Positive Sentiment', v => v.positive + '%'],
      ['Negative Sentiment', v => v.negative + '%'],
      ['Decision', v => decisionLabel(v.decision).label]
    ];
    tbl.innerHTML = rows.map(([label, fn]) =>
      `<tr><td class="ct-label">${label}</td>${varieties.map(v=>`<td>${fn(v)}</td>`).join('')}</tr>`
    ).join('');
  }
}

// ===== EXPORT REPORTS =====
function exportVarietyReport() {
  if (!currentModalId) return;
  const v = VARIETIES.find(x => x.id == currentModalId);
  if (!v) return;
  generateAndDownloadReport(v);
}
function exportPortfolioReport() {
  if (portfolioIds.length === 0) { showToast('Add varieties to your portfolio first.'); return; }
  const varieties = portfolioIds.map(id => VARIETIES.find(x => x.id == id)).filter(Boolean);
  generateAndDownloadPortfolioReport(varieties);
}
function generateAndDownloadReport(v) {
  const dec = decisionLabel(v.decision);
  const opp = OPPORTUNITY_LABELS[v.opportunity] || {};
  const insights = generateAIInsights(v);
  const recs = generateStrategicRecs(v);
  const now = new Date().toLocaleDateString('en-GB', { year:'numeric', month:'long', day:'numeric' });
  const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Floraputation Report — ${v.variety}</title>
  <style>
    body{font-family:Arial,sans-serif;max-width:900px;margin:0 auto;padding:40px;color:#1F2937}
    h1{color:#166534;font-size:28px;border-bottom:3px solid #16A34A;padding-bottom:12px}
    h2{color:#166534;font-size:18px;margin-top:32px}
    .meta{color:#6B7280;font-size:13px;margin-bottom:24px}
    .score-row{display:flex;gap:24px;margin:20px 0;flex-wrap:wrap}
    .score-box{background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;padding:16px 24px;text-align:center}
    .score-val{font-size:36px;font-weight:700;color:#16A34A}
    .score-label{font-size:12px;color:#6B7280;margin-top:4px}
    .dec-badge{display:inline-block;padding:6px 14px;border-radius:20px;font-weight:600;background:#DCFCE7;color:#166534;margin:8px 0}
    .insight{background:#F9FAFB;border-left:4px solid #16A34A;padding:12px 16px;margin:10px 0;border-radius:0 8px 8px 0}
    .insight.risk{border-color:#DC2626;background:#FEF2F2}
    .insight.premium{border-color:#7C3AED;background:#F5F3FF}
    .rec{background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:16px;margin:10px 0}
    .rec-priority{font-size:11px;font-weight:700;text-transform:uppercase;color:#DC2626;margin-bottom:6px}
    .rec-title{font-weight:700;font-size:15px;margin-bottom:6px}
    .rec-action{background:#F0FDF4;padding:8px 12px;border-radius:6px;font-size:13px;margin-top:8px;color:#166534}
    table{width:100%;border-collapse:collapse;margin:16px 0}
    th{background:#F0FDF4;padding:10px;text-align:left;font-size:13px;color:#166534}
    td{padding:8px 10px;border-bottom:1px solid #F3F4F6;font-size:13px}
    .footer{margin-top:48px;padding-top:16px;border-top:1px solid #E5E7EB;color:#9CA3AF;font-size:12px}
    @media print{body{padding:20px}}
  </style></head><body>
  <h1>🌿 Floraputation Variety Intelligence Report</h1>
  <div class="meta">Generated: ${now} &nbsp;|&nbsp; Platform: Floraputation 1.3 &nbsp;|&nbsp; Confidential — For Internal Use Only</div>
  <h2>${v.variety}</h2>
  <p><strong>Category:</strong> ${v.crop} &nbsp;|&nbsp; <strong>Breeder:</strong> ${v.series || 'Unknown'} &nbsp;|&nbsp; <strong>Season:</strong> ${v.series}</p>
  ${v.aliases ? `<p><strong>Also known as:</strong> ${v.aliases.join(', ')}</p>` : ''}
  <div class="dec-badge">${dec.icon} Strategic Decision: ${dec.label}</div>
  <div class="score-row">
    <div class="score-box"><div class="score-val">${v.score}</div><div class="score-label">Overall Score</div></div>
    <div class="score-box"><div class="score-val" style="color:#2563EB">${v.consumer}</div><div class="score-label">Consumer Score</div></div>
    <div class="score-box"><div class="score-val" style="color:#7C3AED">${v.retailer}</div><div class="score-label">Distributor Score</div></div>
    <div class="score-box"><div class="score-val" style="color:#D97706">${v.grower}</div><div class="score-label">Grower Score</div></div>
    <div class="score-box"><div class="score-val">${v.trend > 0 ? '+' : ''}${v.trend.toFixed(1)}%</div><div class="score-label">Monthly Trend</div></div>
    <div class="score-box"><div class="score-val">${fmt(v.mentions)}</div><div class="score-label">Total Mentions</div></div>
  </div>
  <h2>Sentiment Distribution</h2>
  <table><tr><th>Positive</th><th>Neutral</th><th>Negative</th><th>Confidence</th></tr>
  <tr><td style="color:#16A34A;font-weight:700">${v.positive}%</td><td>${v.neutral}%</td><td style="color:#DC2626;font-weight:700">${v.negative}%</td><td>${v.confidence}%</td></tr></table>
  <h2>Regional Performance</h2>
  <table><thead><tr><th>Region</th><th>Overall</th><th>Consumer</th><th>Distributor</th><th>Grower</th><th>Mentions</th><th>Trend</th><th>Signal</th></tr></thead><tbody>
  ${v.regional.map(r=>`<tr><td>${r.region}</td><td>${r.score}</td><td>${r.consumer}</td><td>${r.retailer}</td><td>${r.grower}</td><td>${fmt(r.mentions)}</td><td>${r.trend>0?'+':''}${r.trend.toFixed(1)}%</td><td>${r.signal}</td></tr>`).join('')}
  </tbody></table>
  <h2>AI-Generated Insights</h2>
  ${insights.map(i=>`<div class="insight ${i.type}"><strong>${i.icon} ${i.title}</strong><br>${i.text.replace(/<[^>]+>/g,'')}</div>`).join('')}
  <h2>Strategic Recommendations</h2>
  ${recs.map(r=>`<div class="rec"><div class="rec-priority">${r.priority} priority</div><div class="rec-title">${r.icon} ${r.title}</div><p>${r.text}</p><div class="rec-action">${r.action}</div></div>`).join('')}
  <div class="footer">Floraputation 1.3 — Floral Variety Intelligence Platform &nbsp;|&nbsp; floraputation.com &nbsp;|&nbsp; Data reflects aggregated public sentiment from social media, trade forums, and e-commerce platforms. For strategic reference only.</div>
  </body></html>`;

  const blob = new Blob([html], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `Floraputation_Report_${v.variety.replace(/[^a-zA-Z0-9]/g,'_')}_${new Date().toISOString().slice(0,10)}.html`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Report downloaded successfully');
}

function generateAndDownloadPortfolioReport(varieties) {
  const now = new Date().toLocaleDateString('en-GB', { year:'numeric', month:'long', day:'numeric' });
  const avgScore = Math.round(varieties.reduce((s,v)=>s+v.score,0)/varieties.length);
  const pushCount = varieties.filter(v=>v.decision==='push').length;
  const stopCount = varieties.filter(v=>v.decision==='stop').length;
  const priceCount = varieties.filter(v=>v.decision==='price').length;
  const eliteCount = varieties.filter(v=>v.decision==='elite').length;

  const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Floraputation Quarterly Portfolio Report</title>
  <style>
    body{font-family:Arial,sans-serif;max-width:1000px;margin:0 auto;padding:40px;color:#1F2937}
    h1{color:#166534;font-size:26px;border-bottom:3px solid #16A34A;padding-bottom:12px}
    h2{color:#166534;font-size:18px;margin-top:32px}
    .meta{color:#6B7280;font-size:13px;margin-bottom:24px}
    .kpi-row{display:flex;gap:16px;flex-wrap:wrap;margin:20px 0}
    .kpi{background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;padding:14px 20px;text-align:center;min-width:100px}
    .kpi-val{font-size:28px;font-weight:700;color:#16A34A}
    .kpi-label{font-size:11px;color:#6B7280;margin-top:4px}
    table{width:100%;border-collapse:collapse;margin:16px 0;font-size:13px}
    th{background:#F0FDF4;padding:10px;text-align:left;color:#166534}
    td{padding:8px 10px;border-bottom:1px solid #F3F4F6}
    .push{color:#16A34A;font-weight:700} .stop{color:#DC2626;font-weight:700} .price{color:#7C3AED;font-weight:700} .elite{color:#D97706;font-weight:700}
    .footer{margin-top:48px;padding-top:16px;border-top:1px solid #E5E7EB;color:#9CA3AF;font-size:12px}
    @media print{body{padding:20px}}
  </style></head><body>
  <h1>🌿 Floraputation Quarterly Portfolio Report</h1>
  <div class="meta">Generated: ${now} &nbsp;|&nbsp; Floraputation 1.3 &nbsp;|&nbsp; Confidential — For Internal Use Only</div>
  <h2>Portfolio Summary</h2>
  <div class="kpi-row">
    <div class="kpi"><div class="kpi-val">${varieties.length}</div><div class="kpi-label">Varieties Tracked</div></div>
    <div class="kpi"><div class="kpi-val">${avgScore}</div><div class="kpi-label">Avg Overall Score</div></div>
    <div class="kpi"><div class="kpi-val push">${pushCount}</div><div class="kpi-label">Push</div></div>
    <div class="kpi"><div class="kpi-val stop">${stopCount}</div><div class="kpi-label">Phase Out</div></div>
    <div class="kpi"><div class="kpi-val price">${priceCount}</div><div class="kpi-label">Raise Price</div></div>
    <div class="kpi"><div class="kpi-val elite">${eliteCount}</div><div class="kpi-label">Elite Only</div></div>
  </div>
  <h2>Variety-by-Variety Breakdown</h2>
  <table><thead><tr><th>Variety</th><th>Category</th><th>Score</th><th>Consumer</th><th>Distributor</th><th>Grower</th><th>Trend</th><th>Mentions</th><th>Decision</th></tr></thead><tbody>
  ${varieties.map(v=>{const dec=decisionLabel(v.decision);return`<tr><td><strong>${v.variety}</strong></td><td>${v.crop}</td><td style="color:${scoreColor(v.score)};font-weight:700">${v.score}</td><td>${v.consumer}</td><td>${v.retailer}</td><td>${v.grower}</td><td>${v.trend>0?'+':''}${v.trend.toFixed(1)}%</td><td>${fmt(v.mentions)}</td><td class="${v.decision}">${dec.icon} ${dec.label}</td></tr>`;}).join('')}
  </tbody></table>
  <h2>Strategic Actions Required This Quarter</h2>
  <table><thead><tr><th>Priority</th><th>Variety</th><th>Action</th><th>Rationale</th></tr></thead><tbody>
  ${varieties.filter(v=>v.decision==='push').map(v=>`<tr><td><strong style="color:#16A34A">HIGH</strong></td><td>${v.variety}</td><td>Scale distribution</td><td>Score ${v.score}/100, trend +${v.trend.toFixed(1)}%/mo</td></tr>`).join('')}
  ${varieties.filter(v=>v.decision==='price').map(v=>`<tr><td><strong style="color:#7C3AED">HIGH</strong></td><td>${v.variety}</td><td>Implement price increase (10–20%)</td><td>Consumer score ${v.consumer} vs grower ${v.grower} — premium signal</td></tr>`).join('')}
  ${varieties.filter(v=>v.decision==='elite').map(v=>`<tr><td><strong style="color:#D97706">MEDIUM</strong></td><td>${v.variety}</td><td>Restrict to specialist growers</td><td>Cultivation complexity requires expert handling</td></tr>`).join('')}
  ${varieties.filter(v=>v.decision==='stop').map(v=>`<tr><td><strong style="color:#DC2626">HIGH</strong></td><td>${v.variety}</td><td>Initiate phase-out</td><td>Score ${v.score}/100, trend ${v.trend.toFixed(1)}%/mo</td></tr>`).join('')}
  </tbody></table>
  <div class="footer">Floraputation 1.3 — Floral Variety Intelligence Platform &nbsp;|&nbsp; floraputation.com &nbsp;|&nbsp; Quarterly report generated automatically from aggregated public sentiment data.</div>
  </body></html>`;

  const blob = new Blob([html], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `Floraputation_Quarterly_Report_${new Date().toISOString().slice(0,7)}.html`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Quarterly report downloaded');
}

// ===== TOAST =====
function showToast(msg) {
  let t = document.getElementById('toast');
  if (!t) {
    t = document.createElement('div');
    t.id = 'toast';
    t.style.cssText = 'position:fixed;bottom:24px;right:24px;background:#166534;color:#fff;padding:12px 20px;border-radius:8px;font-size:14px;z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,0.15);transition:opacity 0.3s';
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.style.opacity = '1';
  setTimeout(() => { t.style.opacity = '0'; }, 2500);
}

// ===== INIT =====
function updateDashboardKPIs() {
  const pushCount = VARIETIES.filter(v => v.decision === 'push').length;
  const stopCount = VARIETIES.filter(v => v.decision === 'stop').length;
  const priceCount = VARIETIES.filter(v => v.decision === 'price').length;
  const eliteCount = VARIETIES.filter(v => v.decision === 'elite').length;
  // Hero KPIs
  const kpiPush = document.getElementById('kpi-push');
  const kpiPrice = document.getElementById('kpi-price');
  const kpiRisk = document.getElementById('kpi-risk');
  if (kpiPush) kpiPush.textContent = pushCount;
  if (kpiPrice) kpiPrice.textContent = priceCount;
  if (kpiRisk) kpiRisk.textContent = stopCount;
  // Decision Hub counts
  const dcPush = document.getElementById('dec-count-push');
  const dcStop = document.getElementById('dec-count-stop');
  const dcPrice = document.getElementById('dec-count-price');
  const dcElite = document.getElementById('dec-count-elite');
  if (dcPush) dcPush.textContent = pushCount;
  if (dcStop) dcStop.textContent = stopCount;
  if (dcPrice) dcPrice.textContent = priceCount;
  if (dcElite) dcElite.textContent = eliteCount;
  // Insight strip
  const strip = document.getElementById('insight-strip');
  if (strip) {
    const topVariety = [...VARIETIES].sort((a,b) => b.score - a.score)[0];
    const topTrend = [...VARIETIES].sort((a,b) => b.trend - a.trend)[0];
    const atRisk = VARIETIES.filter(v => v.trend < -2 && v.score < 75).length;
    strip.innerHTML = `
      <div class="insight-strip-item"><span class="strip-icon">&#128640;</span><span class="strip-text">${pushCount} varieties ready to scale &mdash; strong scores &amp; positive momentum</span></div>
      <div class="insight-strip-item"><span class="strip-icon">&#11088;</span><span class="strip-text">Top performer: <strong>${topVariety ? topVariety.variety : ''}</strong> (${topVariety ? topVariety.score : 0}/100)</span></div>
      <div class="insight-strip-item"><span class="strip-icon">&#128200;</span><span class="strip-text">Fastest growing: <strong>${topTrend ? topTrend.variety : ''}</strong> (+${topTrend ? topTrend.trend.toFixed(1) : 0}%/mo)</span></div>
      <div class="insight-strip-item"><span class="strip-icon">&#9888;&#65039;</span><span class="strip-text">${atRisk} varieties showing declining trend &mdash; review recommended</span></div>
      <div class="insight-strip-item"><span class="strip-icon">&#128176;</span><span class="strip-text">${priceCount} varieties with premium pricing potential (consumer-grower gap)</span></div>
    `;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // Populate crop filter
  const cropSel = document.getElementById('filter-crop');
  const heatmapCrop = document.getElementById('heatmap-crop');
  const cats = [...new Set(VARIETIES.map(v => v.crop))].sort();
  cats.forEach(c => {
    if (cropSel) cropSel.innerHTML += `<option value="${c}">${c}</option>`;
    if (heatmapCrop) heatmapCrop.innerHTML += `<option value="${c}">${c}</option>`;
  });

  // Update dashboard KPIs
  updateDashboardKPIs();

  // Initial search
  performSearch();

  // Decision hub
  switchDecision('push');

  // Heatmap
  renderHeatmap();

  // Keyboard search
  const inp = document.getElementById('main-search');
  if (inp) {
    inp.addEventListener('keydown', e => {
      if (e.key === 'Enter') performSearch();
      if (e.key === 'Escape') {
        const ac = document.getElementById('autocomplete-list');
        if (ac) ac.style.display = 'none';
      }
    });
  }

  // Close autocomplete on outside click
  document.addEventListener('click', e => {
    const ac = document.getElementById('autocomplete-list');
    if (ac && !e.target.closest('.search-bar-wrap')) ac.style.display = 'none';
    const pac = document.getElementById('portfolio-autocomplete');
    if (pac && !e.target.closest('.portfolio-input-wrap')) pac.style.display = 'none';
  });

  // Escape closes modal
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
  });
});

// addToCompare — alias used in modal header button
function addToCompare(id) {
  // Find first empty slot
  const slot = compareSlots.indexOf(null);
  if (slot === -1) { showToast('Compare slots are full. Remove a variety first.'); return; }
  compareSlots[slot] = id;
  renderCompareSlots();
  // Scroll to compare section
  const sec = document.getElementById('compare-section');
  if (sec) sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
  showToast('Added to Compare');
}
