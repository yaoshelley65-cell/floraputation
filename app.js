/* ============================================================
   Floraputation 2.0 — Main Application Logic
   Freemium: Free users see basic score + sentiment only.
   Pro users see full intelligence suite.
   ============================================================ */

/* ===== USER AUTH ===== */
let currentUser = null;

function initAuth() {
  const saved = sessionStorage.getItem('fp_user');
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      // If stored user lacks role/tier, re-lookup from PRO_USERS for full object
      if (parsed && parsed.email && (!parsed.role && !parsed.tier)) {
        const fullUser = PRO_USERS.find(function(u) { return u.email.toLowerCase() === parsed.email.toLowerCase(); });
        currentUser = fullUser || parsed;
      } else {
        currentUser = parsed;
      }
      // Update session with full user object
      if (currentUser) sessionStorage.setItem('fp_user', JSON.stringify(currentUser));
    } catch(e) {}
  }
  renderAuthUI();
}

function renderAuthUI() {
  const navRight = document.getElementById('nav-right');
  if (!navRight) return;
  if (currentUser) {
    navRight.innerHTML =
      '<span class="nav-user-badge"><span class="nav-user-name">' + currentUser.name + '</span>' +
      '<span class="nav-pro-badge">PRO</span></span>' +
      '<button class="btn-nav-outline" onclick="signOut()">Sign Out</button>';
  } else {
    navRight.innerHTML =
      '<button class="btn-nav-outline" onclick="openSignIn()">Sign In</button>' +
      '<button class="btn-nav-primary" onclick="openUpgrade()">Get Pro Access</button>';
  }
}

function openSignIn() { document.getElementById('signin-modal').classList.add('active'); }
function closeSignIn() {
  document.getElementById('signin-modal').classList.remove('active');
  document.getElementById('signin-error').textContent = '';
}
function doSignIn() {
  const email = document.getElementById('signin-email').value.trim().toLowerCase();
  const pass  = document.getElementById('signin-pass').value;
  const user  = PRO_USERS.find(function(u) { return u.email.toLowerCase() === email && u.password === pass; });
  if (user) {
    currentUser = user;
    sessionStorage.setItem('fp_user', JSON.stringify(user));
    closeSignIn();
    renderAuthUI();
    showToast('Welcome back, ' + user.name + '! Pro access enabled.', 'success');
  } else {
    document.getElementById('signin-error').textContent = 'Invalid email or password. Please try again.';
  }
}
function signOut() {
  currentUser = null;
  sessionStorage.removeItem('fp_user');
  renderAuthUI();
  showToast('Signed out successfully.', 'info');
}
function openUpgrade()  { document.getElementById('upgrade-modal').classList.add('active'); }
function closeUpgrade() { document.getElementById('upgrade-modal').classList.remove('active'); }
function isPro() { return !!(currentUser && (currentUser.tier === 'pro' || currentUser.role === 'pro' || currentUser.role === 'admin')); }

/* ===== TOAST ===== */
function showToast(msg, type) {
  type = type || 'info';
  const t = document.createElement('div');
  t.className = 'toast toast-' + type;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(function() { t.classList.add('show'); }, 10);
  setTimeout(function() { t.classList.remove('show'); setTimeout(function() { t.remove(); }, 300); }, 3200);
}

/* ===== NAVIGATION ===== */
function navigate(page) {
  document.querySelectorAll('.page').forEach(function(p) { p.classList.remove('active'); });
  document.querySelectorAll('.nav-link').forEach(function(l) { l.classList.remove('active'); });
  const pageEl = document.getElementById('page-' + page);
  if (pageEl) pageEl.classList.add('active');
  const navEl = document.querySelector('.nav-link[data-page="' + page + '"]');
  if (navEl) navEl.classList.add('active');
  if (page === 'decision')  renderDecisionHub();
  if (page === 'heatmap')   renderHeatmap();
  if (page === 'compare')   renderCompare();
  if (page === 'portfolio') renderPortfolioPage();
}

/* ===== UTILITIES ===== */
function fmt(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000)    return (n / 1000).toFixed(1) + 'K';
  return String(n);
}
function scoreColor(s) {
  if (s >= 85) return '#16A34A';
  if (s >= 70) return '#D97706';
  return '#DC2626';
}
function scoreGrade(s) {
  if (s >= 90) return 'Excellent';
  if (s >= 80) return 'Strong';
  if (s >= 70) return 'Good';
  if (s >= 60) return 'Fair';
  return 'Weak';
}
function trendHtml(t) {
  if (t > 0) return '<span class="trend-up">\u25B2 +' + t.toFixed(1) + '%</span>';
  if (t < 0) return '<span class="trend-down">\u25BC ' + t.toFixed(1) + '%</span>';
  return '<span class="trend-flat">\u2014 0.0%</span>';
}
function decisionInfo(d) {
  const map = {
    push:  { icon: '\uD83D\uDE80', label: 'Push & Scale',      cls: 'dec-push'  },
    stop:  { icon: '\uD83D\uDED1', label: 'Phase Out',          cls: 'dec-stop'  },
    price: { icon: '\uD83D\uDCB0', label: 'Raise Price',        cls: 'dec-price' },
    elite: { icon: '\uD83C\uDF31', label: 'Elite Growers Only', cls: 'dec-elite' },
  };
  return map[d] || { icon: '\u2014', label: 'Monitor', cls: 'dec-monitor' };
}
function signalHtml(sig) {
  const s = (sig || '').toLowerCase();
  const map = {
    hot:    ['sig-hot',    '\uD83D\uDD25 Hot'],
    low:    ['sig-low',    '\uD83D\uDCCA Low'],
    risk:   ['sig-risk',   '\u26A0\uFE0F Risk'],
    stable: ['sig-stable', '\u2014 Stable'],
  };
  const pair = map[s] || map.stable;
  return '<span class="rt-signal ' + pair[0] + '">' + pair[1] + '</span>';
}

/* ===== SEARCH ===== */
let searchResults = [];

function initSearch() {
  const input = document.getElementById('search-input');
  if (!input) return;
  input.addEventListener('keydown', function(e) { if (e.key === 'Enter') doSearch(); });
}

function doSearch() {
  const q = ((document.getElementById('search-input') || {}).value || '').trim().toLowerCase();
  if (!q) { showSearchEmpty('Please enter a variety name or crop type to search.'); return; }
  const results = VARIETIES.filter(function(v) {
    return v.variety.toLowerCase().includes(q) ||
           v.crop.toLowerCase().includes(q) ||
           (v.series || '').toLowerCase().includes(q);
  });
  searchResults = results;
  renderSearchResults(results, q);
}

function quickSearch(term) {
  document.getElementById('search-input').value = term;
  doSearch();
}

function showSearchEmpty(msg) {
  const c = document.getElementById('search-results');
  if (c) c.innerHTML = '<div class="search-empty"><p>' + msg + '</p></div>';
  const m = document.getElementById('search-meta');
  if (m) m.textContent = '';
}

function renderSearchResults(results, query) {
  const container = document.getElementById('search-results');
  const meta      = document.getElementById('search-meta');
  if (!container) return;

  if (results.length === 0) {
    container.innerHTML = '<div class="search-empty"><p>No varieties found matching <strong>' + query + '</strong>. Try a different name or crop type.</p></div>';
    if (meta) meta.textContent = '';
    return;
  }
  if (meta) meta.textContent = results.length + ' variet' + (results.length === 1 ? 'y' : 'ies') + ' found';

  container.innerHTML = results.map(function(v) {
    const dec = decisionInfo(v.decision);
    const sc  = scoreColor(v.score);
    const pct = v.score;
    return '<div class="variety-card" onclick="openVarietyModal(\'' + v.id + '\')">' +
      '<div class="vc-header">' +
        '<div class="vc-score-ring">' +
          '<svg viewBox="0 0 36 36">' +
            '<circle cx="18" cy="18" r="15.9" fill="none" stroke="#e5e7eb" stroke-width="3"/>' +
            '<circle cx="18" cy="18" r="15.9" fill="none" stroke="' + sc + '" stroke-width="3"' +
            ' stroke-dasharray="' + pct + ' ' + (100 - pct) + '" stroke-dashoffset="25" stroke-linecap="round"/>' +
          '</svg>' +
          '<span class="vc-score-num">' + v.score + '</span>' +
        '</div>' +
        '<div class="vc-info">' +
          '<div class="vc-name">' + v.variety + '</div>' +
          '<div class="vc-meta">' + v.crop + (v.series ? ' \u00B7 ' + v.series : '') + '</div>' +
          '<div class="vc-badges">' +
            '<span class="dec-badge ' + dec.cls + '">' + dec.icon + ' ' + dec.label + '</span>' +
            trendHtml(v.trend) +
          '</div>' +
        '</div>' +
      '</div>' +
      '<div class="vc-sentiment">' +
        '<div class="sent-bar">' +
          '<div class="sent-pos" style="width:' + v.positive + '%"></div>' +
          '<div class="sent-neu" style="width:' + v.neutral  + '%"></div>' +
          '<div class="sent-neg" style="width:' + v.negative + '%"></div>' +
        '</div>' +
        '<div class="sent-labels">' +
          '<span class="pos">' + v.positive + '% Positive</span>' +
          '<span class="neu">' + v.neutral  + '% Neutral</span>' +
          '<span class="neg">' + v.negative + '% Negative</span>' +
        '</div>' +
      '</div>' +
      '<div class="vc-footer">' +
        '<span class="vc-mentions">' + fmt(v.mentionsRaw) + ' mentions</span>' +
        '<span class="vc-grade" style="color:' + sc + '">' + scoreGrade(v.score) + '</span>' +
      '</div>' +
    '</div>';
  }).join('');
}

/* ===== VARIETY MODAL ===== */
let modalCharts = {};

function openVarietyModal(id) {
  const numId = parseInt(id, 10);
  const v = VARIETIES.find(function(x) { return x.id === numId; });
  if (!v) return;

  const modal = document.getElementById('variety-modal');
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';

  document.getElementById('modal-name').textContent   = v.variety;
  document.getElementById('modal-crop').textContent   = v.crop + (v.series ? ' \u00B7 ' + v.series : '');

  const dec = decisionInfo(v.decision);
  document.getElementById('modal-decision').innerHTML =
    '<span class="dec-badge ' + dec.cls + '">' + dec.icon + ' ' + dec.label + '</span>';

  drawModalRing(v.score);
  document.getElementById('modal-score-val').textContent    = v.score;
  document.getElementById('modal-score-grade').textContent  = scoreGrade(v.score);
  document.getElementById('modal-score-grade').style.color  = scoreColor(v.score);
  document.getElementById('modal-trend').innerHTML          = trendHtml(v.trend);
  document.getElementById('modal-mentions').textContent     = fmt(v.mentionsRaw) + ' total mentions';
  document.getElementById('modal-confidence').textContent   = v.confidence + '% data confidence';

  document.getElementById('modal-sent-pos').style.width     = v.positive + '%';
  document.getElementById('modal-sent-neu').style.width     = v.neutral  + '%';
  document.getElementById('modal-sent-neg').style.width     = v.negative + '%';
  document.getElementById('modal-sent-pos-val').textContent = v.positive + '% Positive';
  document.getElementById('modal-sent-neu-val').textContent = v.neutral  + '% Neutral';
  document.getElementById('modal-sent-neg-val').textContent = v.negative + '% Negative';

  const proSection = document.getElementById('modal-pro-content');
  const freeGate   = document.getElementById('modal-free-gate');
  if (isPro()) {
    proSection.style.display = 'block';
    freeGate.style.display   = 'none';
    renderProModalContent(v);
  } else {
    proSection.style.display = 'none';
    freeGate.style.display   = 'block';
  }
}

function drawModalRing(score) {
  const canvas = document.getElementById('modal-ring-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const cx = canvas.width / 2, cy = canvas.height / 2, r = 55;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.strokeStyle = '#e5e7eb'; ctx.lineWidth = 10; ctx.stroke();
  const end = (score / 100) * Math.PI * 2 - Math.PI / 2;
  ctx.beginPath(); ctx.arc(cx, cy, r, -Math.PI / 2, end);
  ctx.strokeStyle = scoreColor(score); ctx.lineWidth = 10; ctx.lineCap = 'round'; ctx.stroke();
}

function renderProModalContent(v) {
  document.getElementById('modal-consumer-score').textContent = v.consumer;
  document.getElementById('modal-grower-score').textContent   = v.grower;
  document.getElementById('modal-retailer-score').textContent = v.retailer;

  const gap   = v.consumer - v.grower;
  const gapEl = document.getElementById('modal-cvg-gap');
  if (Math.abs(gap) >= 10) {
    gapEl.innerHTML = '<div class="cvg-gap-alert ' + (gap > 0 ? 'gap-pos' : 'gap-neg') + '">' +
      '<strong>' + (gap > 0 ? '+' : '') + gap + ' pt Consumer\u2013Grower gap</strong>' +
      (gap > 0 ? ' \u2192 Strong premium pricing signal' : ' \u2192 Grower satisfaction exceeds consumer demand') +
      '</div>';
  } else {
    gapEl.innerHTML = '<div class="cvg-gap-neutral">Consumer and grower scores are well-aligned (gap: ' +
      (gap > 0 ? '+' : '') + gap + ' pt)</div>';
  }

  renderMentionsChart(v, '1y');
  renderSegmentsChart(v);
  renderRegionTable(v);
  renderAIInsights(v);
  renderBenchmarkChart(v);
  document.getElementById('variety-modal').dataset.varietyId = v.id;
}

function switchPeriod(period, btn) {
  document.querySelectorAll('.period-btn').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  const id = document.getElementById('variety-modal').dataset.varietyId;
  const v  = VARIETIES.find(function(x) { return x.id === id; });
  if (v) renderMentionsChart(v, period);
}

function genMonthlyData(v, months) {
  const result = [];
  const now    = new Date();
  const base   = Math.round(v.mentionsRaw / 12);
  for (let i = months - 1; i >= 0; i--) {
    const d     = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const label = d.toLocaleString('en', { month: 'short', year: months > 12 ? '2-digit' : undefined });
    const seed  = (v.id.charCodeAt(0) + i * 7) % 40;
    result.push({ label: label, value: Math.max(10, base + seed - 20) });
  }
  return result;
}

function genSegmentTrend(base, months) {
  const result = [];
  for (let i = 0; i < months; i++) {
    const noise = Math.sin(i * 0.8) * 5 + (Math.random() * 4 - 2);
    result.push(Math.min(100, Math.max(30, Math.round(base + noise))));
  }
  return result;
}

function renderMentionsChart(v, period) {
  const canvas = document.getElementById('chart-mentions');
  if (!canvas) return;
  if (modalCharts.mentions) { modalCharts.mentions.destroy(); }
  const months = { '3m': 3, '6m': 6, '1y': 12, '3y': 36 }[period] || 12;
  const data   = genMonthlyData(v, months);
  modalCharts.mentions = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: data.map(function(d) { return d.label; }),
      datasets: [{ label: 'Monthly Mentions', data: data.map(function(d) { return d.value; }),
        backgroundColor: 'rgba(22,163,74,0.7)', borderColor: '#16A34A', borderWidth: 1, borderRadius: 4 }]
    },
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } }, x: { grid: { display: false } } }
    }
  });
}

function renderSegmentsChart(v) {
  const canvas = document.getElementById('chart-segments');
  if (!canvas) return;
  if (modalCharts.segments) { modalCharts.segments.destroy(); }
  const months = 12;
  const labels = genMonthlyData(v, months).map(function(d) { return d.label; });
  modalCharts.segments = new Chart(canvas, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        { label: 'Consumer', data: genSegmentTrend(v.consumer, months),
          borderColor: '#3B82F6', backgroundColor: 'rgba(59,130,246,0.1)', tension: 0.4, fill: false },
        { label: 'Grower',   data: genSegmentTrend(v.grower,   months),
          borderColor: '#16A34A', backgroundColor: 'rgba(22,163,74,0.1)',  tension: 0.4, fill: false },
        { label: 'Retailer', data: genSegmentTrend(v.retailer, months),
          borderColor: '#D97706', backgroundColor: 'rgba(217,119,6,0.1)',  tension: 0.4, fill: false },
      ]
    },
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'top', labels: { boxWidth: 12 } } },
      scales: { y: { min: 40, max: 100, grid: { color: 'rgba(0,0,0,0.05)' } }, x: { grid: { display: false } } }
    }
  });
}

function renderRegionTable(v) {
  const tbody = document.getElementById('region-tbody');
  if (!tbody) return;
  tbody.innerHTML = (v.regional || []).map(function(r) {
    return '<tr>' +
      '<td><strong>' + r.region + '</strong></td>' +
      '<td><span style="color:' + scoreColor(r.overall) + ';font-weight:600">' + r.overall + '</span></td>' +
      '<td>' + r.consumer + '</td><td>' + r.grower + '</td><td>' + r.retailer + '</td>' +
      '<td>' + fmt(r.mentions) + '</td>' +
      '<td>' + trendHtml(r.trend) + '</td>' +
      '<td>' + signalHtml(r.signal) + '</td>' +
    '</tr>';
  }).join('');
}

function generateAIInsights(v) {
  const insights = [];
  const gap = v.consumer - v.grower;
  if (v.decision === 'push')  insights.push({ type: 'positive', icon: '\uD83D\uDE80', title: 'Scale Recommendation',       text: 'Strong performance across all segments. Prioritise distribution expansion in top-performing regions.' });
  if (v.decision === 'price') insights.push({ type: 'pricing',  icon: '\uD83D\uDCB0', title: 'Premium Pricing Signal',     text: 'Consumer demand significantly outpaces grower supply pressure. A ' + Math.round(gap * 0.3 + 5) + '\u2013' + Math.round(gap * 0.5 + 10) + '% price increase is supportable.' });
  if (v.decision === 'stop')  insights.push({ type: 'warning',  icon: '\u26A0\uFE0F', title: 'Phase-Out Advisory',         text: 'Declining sentiment and below-threshold scores suggest this variety is reaching end-of-life. Plan a 2-season wind-down.' });
  if (v.decision === 'elite') insights.push({ type: 'elite',    icon: '\uD83C\uDF31', title: 'Elite Channel Strategy',     text: 'High consumer appeal with cultivation complexity. Restrict to certified premium growers to protect brand equity.' });
  if (gap >= 15)              insights.push({ type: 'pricing',  icon: '\uD83D\uDCC8', title: 'Consumer\u2013Grower Gap Detected', text: 'A ' + gap + '-point gap is a classic premium pricing indicator. Review wholesale pricing.' });
  if (v.negative > 20) insights.push({ type: 'warning', icon: '\uD83D\uDD0D', title: 'Negative Sentiment Alert', text: v.negative + '% negative mentions detected. Review recent feedback for recurring issues.' });
  if (v.trend > 5)            insights.push({ type: 'positive', icon: '\uD83D\uDCCA', title: 'Momentum Accelerating',      text: '+' + v.trend.toFixed(1) + '% trend growth. Increase production allocation for next season.' });
  if (v.trend < -5)           insights.push({ type: 'warning',  icon: '\uD83D\uDCC9', title: 'Declining Momentum',         text: v.trend.toFixed(1) + '% trend decline. Investigate before committing further investment.' });
  const top = (v.regional || []).slice().sort(function(a, b) { return b.overall - a.overall; })[0];
  if (top) insights.push({ type: 'regional', icon: '\uD83C\uDF0D', title: 'Regional Strength', text: top.region + ' is your strongest market (score: ' + top.overall + '). Consider targeted marketing investment.' });
  if (v.confidence >= 90) insights.push({ type: 'data', icon: '\u2705', title: 'High Data Confidence', text: v.confidence + '% confidence based on ' + fmt(v.mentionsRaw) + ' data points. Low analytical risk.' });
  return insights.slice(0, 6);
}

function renderAIInsights(v) {
  const grid = document.getElementById('ai-insights-grid');
  if (!grid) return;
  grid.innerHTML = generateAIInsights(v).map(function(ins) {
    return '<div class="insight-card insight-' + ins.type + '">' +
      '<div class="insight-icon">' + ins.icon + '</div>' +
      '<div class="insight-body"><div class="insight-title">' + ins.title + '</div>' +
      '<div class="insight-text">' + ins.text + '</div></div></div>';
  }).join('');
}

function renderBenchmarkChart(v) {
  const canvas = document.getElementById('chart-benchmark');
  if (!canvas) return;
  if (modalCharts.benchmark) { modalCharts.benchmark.destroy(); }
  const peers = VARIETIES.filter(function(x) { return x.crop === v.crop && x.id !== v.id; })
    .sort(function(a, b) { return b.score - a.score; }).slice(0, 4);
  const all = [v].concat(peers);
  modalCharts.benchmark = new Chart(canvas, {
    type: 'radar',
    data: {
      labels: ['Overall Score', 'Consumer', 'Grower', 'Retailer', 'Sentiment', 'Trend'],
      datasets: all.map(function(x, i) {
        return {
          label: x.variety,
          data: [x.score, x.consumer, x.grower, x.retailer,
                 x.positive, Math.max(0, Math.min(100, 50 + x.trend * 5))],
          borderColor: i === 0 ? '#16A34A' : 'hsl(' + (i * 60 + 200) + ',60%,55%)',
          backgroundColor: i === 0 ? 'rgba(22,163,74,0.15)' : 'transparent',
          borderWidth: i === 0 ? 2.5 : 1.5, pointRadius: 3,
        };
      })
    },
    options: { responsive: true, maintainAspectRatio: false,
      scales: { r: { min: 0, max: 100, ticks: { stepSize: 20 } } },
      plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } } }
    }
  });
}

function closeVarietyModal() {
  document.getElementById('variety-modal').classList.remove('active');
  document.body.style.overflow = '';
  Object.values(modalCharts).forEach(function(c) { try { c.destroy(); } catch(e) {} });
  modalCharts = {};
}

/* ===== DECISION HUB ===== */
let decisionFilter = 'push';
let decisionCharts = {};

function renderDecisionHub() {
  if (!isPro()) {
    document.getElementById('decision-pro-gate').style.display = 'flex';
    document.getElementById('decision-content').style.display = 'none';
    return;
  }
  document.getElementById('decision-pro-gate').style.display = 'none';
  document.getElementById('decision-content').style.display = 'block';

  const counts = { push: 0, stop: 0, price: 0, elite: 0 };
  VARIETIES.forEach(function(v) { if (counts[v.decision] !== undefined) counts[v.decision]++; });
  document.getElementById('dec-count-push').textContent  = counts.push;
  document.getElementById('dec-count-stop').textContent  = counts.stop;
  document.getElementById('dec-count-price').textContent = counts.price;
  document.getElementById('dec-count-elite').textContent = counts.elite;

  renderDecisionGrid(decisionFilter);
  renderDecisionChart(counts);
}

function switchDecision(filter, btn) {
  decisionFilter = filter;
  document.querySelectorAll('.dec-tab').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  renderDecisionGrid(filter);
}

function renderDecisionGrid(filter) {
  const grid = document.getElementById('decision-grid');
  if (!grid) return;
  const list = VARIETIES.filter(function(v) { return v.decision === filter; })
    .sort(function(a, b) { return b.score - a.score; });
  grid.innerHTML = list.map(function(v) {
    return '<div class="dh-card" onclick="openVarietyModal(\'' + v.id + '\')">' +
      '<div class="dh-card-header">' +
        '<div><div class="dh-name">' + v.variety + '</div><div class="dh-crop">' + v.crop + '</div></div>' +
        '<div class="dh-score" style="color:' + scoreColor(v.score) + '">' + v.score + '</div>' +
      '</div>' +
      '<div class="dh-segments">' +
        '<span>\uD83D\uDED2 ' + v.consumer + '</span>' +
        '<span>\uD83C\uDF31 ' + v.grower   + '</span>' +
        '<span>\uD83C\uDFEA ' + v.retailer + '</span>' +
      '</div>' +
      '<div class="dh-footer">' + trendHtml(v.trend) +
        '<span class="dh-mentions">' + fmt(v.mentionsRaw) + ' mentions</span>' +
      '</div>' +
    '</div>';
  }).join('');
}

function renderDecisionChart(counts) {
  const canvas = document.getElementById('chart-decision-dist');
  if (!canvas) return;
  if (decisionCharts.dist) { decisionCharts.dist.destroy(); }
  decisionCharts.dist = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: ['Push & Scale', 'Phase Out', 'Raise Price', 'Elite Only'],
      datasets: [{ data: [counts.push, counts.stop, counts.price, counts.elite],
        backgroundColor: ['#16A34A', '#DC2626', '#D97706', '#7C3AED'], borderWidth: 2, borderColor: '#fff' }]
    },
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } }
    }
  });
}

function exportQReport() {
  if (!isPro()) { openUpgrade(); return; }
  const counts = { push: 0, stop: 0, price: 0, elite: 0 };
  VARIETIES.forEach(function(v) { if (counts[v.decision] !== undefined) counts[v.decision]++; });
  const topPush  = VARIETIES.filter(function(v) { return v.decision === 'push';  }).sort(function(a,b) { return b.score - a.score; }).slice(0, 5);
  const topStop  = VARIETIES.filter(function(v) { return v.decision === 'stop';  }).sort(function(a,b) { return a.score - b.score; }).slice(0, 5);
  const topPrice = VARIETIES.filter(function(v) { return v.decision === 'price'; }).sort(function(a,b) { return b.score - a.score; }).slice(0, 5);
  const now = new Date();
  const quarter = 'Q' + Math.ceil((now.getMonth() + 1) / 3) + ' ' + now.getFullYear();

  const html = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Floraputation ' + quarter + ' Report</title>' +
    '<style>body{font-family:Segoe UI,sans-serif;max-width:900px;margin:40px auto;color:#1f2937}' +
    'h1{color:#16A34A;border-bottom:3px solid #16A34A;padding-bottom:10px}h2{color:#374151;margin-top:30px}' +
    '.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:20px 0}' +
    '.kpi{background:#f9fafb;border-radius:8px;padding:16px;text-align:center}' +
    '.kpi-num{font-size:2em;font-weight:700}.kpi-label{font-size:.85em;color:#6b7280}' +
    'table{width:100%;border-collapse:collapse;margin:12px 0}' +
    'th{background:#f3f4f6;padding:8px 12px;text-align:left;font-size:.85em}' +
    'td{padding:8px 12px;border-bottom:1px solid #e5e7eb;font-size:.9em}' +
    '.footer{margin-top:40px;color:#9ca3af;font-size:.8em;border-top:1px solid #e5e7eb;padding-top:16px}' +
    '</style></head><body>' +
    '<h1>\uD83C\uDF38 Floraputation \u2014 ' + quarter + ' Strategic Intelligence Report</h1>' +
    '<p>Generated: ' + now.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }) +
    ' | Portfolio: ' + VARIETIES.length + ' varieties</p>' +
    '<h2>Portfolio Overview</h2>' +
    '<div class="kpi-grid">' +
    '<div class="kpi"><div class="kpi-num" style="color:#16A34A">' + counts.push  + '</div><div class="kpi-label">\uD83D\uDE80 Push &amp; Scale</div></div>' +
    '<div class="kpi"><div class="kpi-num" style="color:#DC2626">' + counts.stop  + '</div><div class="kpi-label">\uD83D\uDED1 Phase Out</div></div>' +
    '<div class="kpi"><div class="kpi-num" style="color:#D97706">' + counts.price + '</div><div class="kpi-label">\uD83D\uDCB0 Raise Price</div></div>' +
    '<div class="kpi"><div class="kpi-num" style="color:#7C3AED">' + counts.elite + '</div><div class="kpi-label">\uD83C\uDF31 Elite Only</div></div>' +
    '</div>' +
    '<h2>Top Varieties to Push &amp; Scale</h2>' +
    '<table><tr><th>Variety</th><th>Crop</th><th>Score</th><th>Consumer</th><th>Grower</th><th>Retailer</th><th>Trend</th></tr>' +
    topPush.map(function(v) {
      return '<tr><td><strong>' + v.variety + '</strong></td><td>' + v.crop + '</td>' +
        '<td style="color:#16A34A;font-weight:700">' + v.score + '</td>' +
        '<td>' + v.consumer + '</td><td>' + v.grower + '</td><td>' + v.retailer + '</td>' +
        '<td>' + (v.trend > 0 ? '+' : '') + v.trend.toFixed(1) + '%</td></tr>';
    }).join('') + '</table>' +
    '<h2>Varieties Recommended for Phase-Out</h2>' +
    '<table><tr><th>Variety</th><th>Crop</th><th>Score</th><th>Negative Sentiment</th><th>Trend</th></tr>' +
    topStop.map(function(v) {
      return '<tr><td><strong>' + v.variety + '</strong></td><td>' + v.crop + '</td>' +
        '<td style="color:#DC2626;font-weight:700">' + v.score + '</td>' +
        '<td>' + v.negative + '%</td><td style="color:#DC2626">' + v.trend.toFixed(1) + '%</td></tr>';
    }).join('') + '</table>' +
    '<h2>Varieties with Premium Pricing Potential</h2>' +
    '<table><tr><th>Variety</th><th>Crop</th><th>Consumer</th><th>Grower</th><th>Gap</th><th>Suggested Increase</th></tr>' +
    topPrice.map(function(v) {
      const g = v.consumer - v.grower;
      return '<tr><td><strong>' + v.variety + '</strong></td><td>' + v.crop + '</td>' +
        '<td>' + v.consumer + '</td><td>' + v.grower + '</td>' +
        '<td style="color:#D97706;font-weight:700">+' + g + '</td>' +
        '<td>' + Math.round(g * 0.4 + 5) + '\u2013' + Math.round(g * 0.6 + 10) + '%</td></tr>';
    }).join('') + '</table>' +
    '<div class="footer"><p>Floraputation Intelligence Platform \u00B7 Confidential \u2014 For internal use only \u00B7 floraputation.com</p></div>' +
    '</body></html>';

  const blob = new Blob([html], { type: 'text/html' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = 'Floraputation_' + quarter.replace(' ', '_') + '_Report.html'; a.click();
  URL.revokeObjectURL(url);
  showToast('Quarterly report exported successfully.', 'success');
}

/* ===== REGIONAL HEATMAP ===== */
const HEATMAP_REGIONS = ['Netherlands', 'Germany', 'France', 'UK', 'USA', 'Japan', 'Australia', 'China'];
let heatmapView = 'overall';

function renderHeatmap() {
  if (!isPro()) {
    document.getElementById('heatmap-pro-gate').style.display = 'flex';
    document.getElementById('heatmap-content').style.display = 'none';
    return;
  }
  document.getElementById('heatmap-pro-gate').style.display = 'none';
  document.getElementById('heatmap-content').style.display = 'block';
  renderHeatmapGrid(heatmapView);
}

function switchHeatmapView(view, btn) {
  heatmapView = view;
  document.querySelectorAll('.heatmap-view-btn').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  renderHeatmapGrid(view);
}

function scoreToHeatColor(score) {
  if (score >= 90) return '#15803D';
  if (score >= 80) return '#16A34A';
  if (score >= 70) return '#4ADE80';
  if (score >= 60) return '#FCD34D';
  if (score >= 50) return '#F97316';
  return '#DC2626';
}

function renderHeatmapGrid(view) {
  const grid = document.getElementById('heatmap-grid');
  if (!grid) return;
  const top   = VARIETIES.slice().sort(function(a, b) { return b.score - a.score; }).slice(0, 20);
  const field = { overall: 'overall', consumer: 'consumer', grower: 'grower', retailer: 'retailer' }[view] || 'overall';

  let html = '<div class="hm-table-wrap"><table class="hm-table"><thead><tr><th>Variety</th><th>Crop</th>' +
    HEATMAP_REGIONS.map(function(r) { return '<th>' + r + '</th>'; }).join('') + '</tr></thead><tbody>';

  top.forEach(function(v) {
    html += '<tr><td class="hm-variety-name">' + v.variety + '</td><td class="hm-crop">' + v.crop + '</td>';
    HEATMAP_REGIONS.forEach(function(region) {
      const rd    = (v.regional || []).find(function(r) { return r.region === region; });
      const score = rd ? (field === 'overall' ? rd.overall : rd[field]) : null;
      if (score !== null && score !== undefined) {
        const bg = scoreToHeatColor(score);
        html += '<td class="hm-cell" style="background:' + bg + ';color:' + (score >= 70 ? '#fff' : '#374151') + '" title="' + region + ': ' + score + '">' + score + '</td>';
      } else {
        html += '<td class="hm-cell hm-no-data">\u2014</td>';
      }
    });
    html += '</tr>';
  });
  html += '</tbody></table></div>';
  grid.innerHTML = html;
}

/* ===== COMPARE ===== */
let compareSelections = [];
let compareChart = null;

function renderCompare() {
  if (!isPro()) {
    document.getElementById('compare-pro-gate').style.display = 'flex';
    document.getElementById('compare-content').style.display = 'none';
    return;
  }
  document.getElementById('compare-pro-gate').style.display = 'none';
  document.getElementById('compare-content').style.display = 'block';
  const input = document.getElementById('compare-search');
  if (input && !input._init) {
    input._init = true;
    input.addEventListener('input', function() {
      const q = this.value.toLowerCase();
      renderCompareDropdown(VARIETIES.filter(function(v) {
        return v.variety.toLowerCase().includes(q) || v.crop.toLowerCase().includes(q);
      }).slice(0, 10));
    });
  }
}

function renderCompareDropdown(matches) {
  const dd = document.getElementById('compare-dropdown');
  if (!dd) return;
  if (!matches.length) { dd.style.display = 'none'; return; }
  dd.style.display = 'block';
  dd.innerHTML = matches.map(function(v) {
    return '<div class="compare-dd-item" onclick="addToCompare(\'' + v.id + '\')">' +
      '<strong>' + v.variety + '</strong> <span class="compare-dd-crop">' + v.crop + '</span></div>';
  }).join('');
}

function addToCompare(id) {
  if (compareSelections.includes(id)) { showToast('Already in comparison.', 'info'); return; }
  if (compareSelections.length >= 5)  { showToast('Maximum 5 varieties.', 'warning'); return; }
  compareSelections.push(id);
  document.getElementById('compare-dropdown').style.display = 'none';
  document.getElementById('compare-search').value = '';
  renderCompareTags(); renderCompareChart();
}

function removeFromCompare(id) {
  compareSelections = compareSelections.filter(function(x) { return x !== id; });
  renderCompareTags(); renderCompareChart();
}

function renderCompareTags() {
  const tags = document.getElementById('compare-tags');
  if (!tags) return;
  tags.innerHTML = compareSelections.map(function(id) {
    const numId = parseInt(id, 10);
  const v = VARIETIES.find(function(x) { return x.id === numId; });
    return v ? '<span class="compare-tag">' + v.variety + ' <button onclick="removeFromCompare(\'' + id + '\')">\u00D7</button></span>' : '';
  }).join('');
}

function renderCompareChart() {
  const canvas = document.getElementById('chart-compare');
  if (!canvas) return;
  if (compareChart) { compareChart.destroy(); compareChart = null; }
  if (!compareSelections.length) {
    document.getElementById('compare-empty').style.display = 'block';
    canvas.style.display = 'none'; return;
  }
  document.getElementById('compare-empty').style.display = 'none';
  canvas.style.display = 'block';
  const varieties = compareSelections.map(function(id) { return VARIETIES.find(function(x) { return x.id === id; }); }).filter(Boolean);
  const colors = ['#16A34A', '#3B82F6', '#D97706', '#7C3AED', '#EC4899'];
  compareChart = new Chart(canvas, {
    type: 'radar',
    data: {
      labels: ['Overall', 'Consumer', 'Grower', 'Retailer', 'Sentiment', 'Momentum'],
      datasets: varieties.map(function(v, i) {
        return { label: v.variety,
          data: [v.score, v.consumer, v.grower, v.retailer,
                 v.positive, Math.max(0, Math.min(100, 50 + v.trend * 5))],
          borderColor: colors[i], backgroundColor: colors[i] + '22', borderWidth: 2, pointRadius: 4 };
      })
    },
    options: { responsive: true, maintainAspectRatio: false,
      scales: { r: { min: 0, max: 100, ticks: { stepSize: 20 } } },
      plugins: { legend: { position: 'bottom' } }
    }
  });
  renderCompareTable(varieties);
}

function renderCompareTable(varieties) {
  const table = document.getElementById('compare-table');
  if (!table) return;
  const rows = [
    ['Overall Score',      function(v) { return v.score; }],
    ['Consumer Score',     function(v) { return v.consumer; }],
    ['Grower Score',       function(v) { return v.grower; }],
    ['Retailer Score',     function(v) { return v.retailer; }],
    ['Positive Sentiment', function(v) { return v.positive + '%'; }],
    ['Trend',              function(v) { return (v.trend > 0 ? '+' : '') + v.trend.toFixed(1) + '%'; }],
    ['Total Mentions',     function(v) { return fmt(v.mentionsRaw); }],
    ['Decision',           function(v) { return decisionInfo(v.decision).label; }],
  ];
  table.innerHTML = '<table><thead><tr><th>Metric</th>' +
    varieties.map(function(v) { return '<th>' + v.variety + '</th>'; }).join('') + '</tr></thead><tbody>' +
    rows.map(function(row) {
      return '<tr><td>' + row[0] + '</td>' + varieties.map(function(v) { return '<td>' + row[1](v) + '</td>'; }).join('') + '</tr>';
    }).join('') + '</tbody></table>';
}

/* ===== PORTFOLIO ===== */
let portfolioSelections = [];
let portfolioChart = null;

function renderPortfolioPage() {
  if (!isPro()) {
    document.getElementById('portfolio-pro-gate').style.display = 'flex';
    document.getElementById('portfolio-content').style.display = 'none';
    return;
  }
  document.getElementById('portfolio-pro-gate').style.display = 'none';
  document.getElementById('portfolio-content').style.display = 'block';
  const input = document.getElementById('portfolio-search');
  if (input && !input._init) {
    input._init = true;
    input.addEventListener('input', function() {
      const q = this.value.toLowerCase();
      renderPortfolioDropdown(VARIETIES.filter(function(v) {
        return v.variety.toLowerCase().includes(q) || v.crop.toLowerCase().includes(q);
      }).slice(0, 10));
    });
  }
}

function renderPortfolioDropdown(matches) {
  const dd = document.getElementById('portfolio-dropdown');
  if (!dd) return;
  if (!matches.length) { dd.style.display = 'none'; return; }
  dd.style.display = 'block';
  dd.innerHTML = matches.map(function(v) {
    return '<div class="compare-dd-item" onclick="addToPortfolio(\'' + v.id + '\')">' +
      '<strong>' + v.variety + '</strong> <span class="compare-dd-crop">' + v.crop + '</span></div>';
  }).join('');
}

function addToPortfolio(id) {
  if (portfolioSelections.includes(id)) { showToast('Already in portfolio.', 'info'); return; }
  portfolioSelections.push(id);
  document.getElementById('portfolio-dropdown').style.display = 'none';
  document.getElementById('portfolio-search').value = '';
  renderPortfolioTags();
}

function removeFromPortfolio(id) {
  portfolioSelections = portfolioSelections.filter(function(x) { return x !== id; });
  renderPortfolioTags();
}

function renderPortfolioTags() {
  const tags = document.getElementById('portfolio-tags');
  if (!tags) return;
  tags.innerHTML = portfolioSelections.map(function(id) {
    const numId = parseInt(id, 10);
  const v = VARIETIES.find(function(x) { return x.id === numId; });
    return v ? '<span class="compare-tag">' + v.variety + ' <button onclick="removeFromPortfolio(\'' + id + '\')">\u00D7</button></span>' : '';
  }).join('');
}

function analysePortfolio() {
  if (!isPro()) { openUpgrade(); return; }
  if (portfolioSelections.length < 2) { showToast('Please add at least 2 varieties to analyse.', 'warning'); return; }
  const varieties    = portfolioSelections.map(function(id) { return VARIETIES.find(function(x) { return x.id === id; }); }).filter(Boolean);
  const avgScore     = Math.round(varieties.reduce(function(s, v) { return s + v.score; }, 0) / varieties.length);
  const avgTrend     = (varieties.reduce(function(s, v) { return s + v.trend; }, 0) / varieties.length).toFixed(1);
  const stopCount    = varieties.filter(function(v) { return v.decision === 'stop'; }).length;
  const riskScore    = Math.round((stopCount / varieties.length) * 100 +
                       (varieties.filter(function(v) { return v.trend < -3; }).length / varieties.length) * 50);
  const crops        = [];
  varieties.forEach(function(v) { if (!crops.includes(v.crop)) crops.push(v.crop); });
  const diversityScore = Math.min(100, Math.round((crops.length / varieties.length) * 100 + 20));

  let riskLevel, riskColor;
  if (riskScore < 20)      { riskLevel = 'Low';      riskColor = '#16A34A'; }
  else if (riskScore < 50) { riskLevel = 'Moderate'; riskColor = '#D97706'; }
  else                     { riskLevel = 'High';     riskColor = '#DC2626'; }

  document.getElementById('portfolio-empty').style.display   = 'none';
  document.getElementById('portfolio-results').style.display = 'block';
  document.getElementById('port-avg-score').textContent  = avgScore;
  document.getElementById('port-avg-score').style.color  = scoreColor(avgScore);
  document.getElementById('port-risk-score').textContent = riskScore + '%';
  document.getElementById('port-risk-score').style.color = riskColor;
  document.getElementById('port-risk-level').textContent = riskLevel + ' Risk';
  document.getElementById('port-diversity').textContent  = diversityScore + '%';
  document.getElementById('port-trend').textContent      = (avgTrend > 0 ? '+' : '') + avgTrend + '%';
  document.getElementById('port-trend').style.color      = avgTrend >= 0 ? '#16A34A' : '#DC2626';

  const recs = [];
  if (stopCount > 0)   recs.push('\u26A0\uFE0F ' + stopCount + ' variet' + (stopCount > 1 ? 'ies' : 'y') + ' flagged for phase-out \u2014 consider replacing with higher-performing alternatives.');
  if (crops.length === 1) recs.push('\uD83D\uDCE6 Single-crop portfolio (' + crops[0] + ') \u2014 high concentration risk. Diversifying across 2\u20133 crop types is recommended.');
  if (avgScore >= 80)  recs.push('\u2705 Strong average portfolio score (' + avgScore + '/100) \u2014 well-positioned for the upcoming season.');
  if (avgTrend < 0)    recs.push('\uD83D\uDCC9 Negative average trend (' + avgTrend + '%) \u2014 review whether declining varieties should be replaced or repositioned.');
  const priceOpp = varieties.filter(function(v) { return v.decision === 'price'; }).length;
  if (priceOpp > 0)    recs.push('\uD83D\uDCB0 ' + priceOpp + ' variet' + (priceOpp > 1 ? 'ies' : 'y') + ' with premium pricing potential \u2014 review wholesale pricing before next season.');
  document.getElementById('port-recommendations').innerHTML = recs.map(function(r) { return '<div class="port-rec">' + r + '</div>'; }).join('');

  renderPortfolioChart(varieties);
}

function renderPortfolioChart(varieties) {
  const canvas = document.getElementById('chart-portfolio');
  if (!canvas) return;
  if (portfolioChart) { portfolioChart.destroy(); portfolioChart = null; }
  const decColors = { push: '#16A34A', stop: '#DC2626', price: '#D97706', elite: '#7C3AED' };
  portfolioChart = new Chart(canvas, {
    type: 'bubble',
    data: {
      datasets: [{
        label: 'Varieties',
        data: varieties.map(function(v) {
          return { x: v.consumer, y: v.grower, r: Math.max(5, v.mentionsRaw / 1000), name: v.variety };
        }),
        backgroundColor: varieties.map(function(v) { return (decColors[v.decision] || '#6B7280') + 'AA'; }),
        borderColor:     varieties.map(function(v) { return  decColors[v.decision] || '#6B7280'; }),
        borderWidth: 2
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false },
        tooltip: { callbacks: { label: function(ctx) { return ctx.raw.name + ' | C: ' + ctx.raw.x + ', G: ' + ctx.raw.y; } } }
      },
      scales: {
        x: { title: { display: true, text: 'Consumer Score' }, min: 0, max: 100 },
        y: { title: { display: true, text: 'Grower Score'   }, min: 0, max: 100 }
      }
    }
  });
}

/* ===== INIT ===== */
document.addEventListener('DOMContentLoaded', function() {
  initAuth();
  initSearch();

  document.querySelectorAll('.nav-link').forEach(function(link) {
    link.addEventListener('click', function(e) { e.preventDefault(); navigate(link.dataset.page); });
  });

  ['variety-modal', 'signin-modal', 'upgrade-modal'].forEach(function(id) {
    const el = document.getElementById(id);
    if (el) el.addEventListener('click', function(e) {
      if (e.target !== e.currentTarget) return;
      if (id === 'variety-modal') closeVarietyModal();
      else if (id === 'signin-modal') closeSignIn();
      else closeUpgrade();
    });
  });

  const passEl = document.getElementById('signin-pass');
  if (passEl) passEl.addEventListener('keydown', function(e) { if (e.key === 'Enter') doSignIn(); });
});
