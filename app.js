/* ============================================================
   Floraputation — App Logic & Chart Initialization
   ============================================================ */

'use strict';

// ============================================================
// DATA — powered by MASTER_VARIETY_INDEX from varieties.js
// ============================================================

// Alias for backward compatibility
const VARIETIES_DATA = typeof MASTER_VARIETY_INDEX !== 'undefined' ? MASTER_VARIETY_INDEX : [];

// Dynamically derive insight datasets from the index
function formatMentions(n) {
  if (n >= 1000000) return (n/1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n/1000).toFixed(1) + 'K';
  return String(n);
}

const TOP10_DATA = getTopVarieties(10).map((v, i) => ({
  rank: i + 1,
  name: v.name,
  category: v.category,
  score: v.score,
  trend: v.trend,
  mentions: formatMentions(v.mentions)
}));

const RISING_DATA = getRisingVarieties(10).map((v, i) => ({
  rank: i + 1,
  name: v.name,
  category: v.category,
  score: v.score,
  trend: v.trend,
  mentions: formatMentions(v.mentions)
}));

const DECLINING_DATA = getDecliningVarieties(10).map((v, i) => ({
  rank: i + 1,
  name: v.name,
  category: v.category,
  score: v.score,
  trend: v.trend,
  mentions: formatMentions(v.mentions)
}));

// Category aggregation
function buildCategoryData() {
  const map = {};
  MASTER_VARIETY_INDEX.forEach(v => {
    if (!map[v.category]) map[v.category] = { scores: [], mentions: 0, trends: [] };
    map[v.category].scores.push(v.score);
    map[v.category].mentions += v.mentions;
    map[v.category].trends.push(parseFloat(v.trend));
  });
  return Object.entries(map)
    .map(([cat, d]) => ({
      name: cat,
      category: 'Category',
      score: Math.round(d.scores.reduce((a,b)=>a+b,0)/d.scores.length),
      trend: (d.trends.reduce((a,b)=>a+b,0)/d.trends.length).toFixed(1),
      mentions: formatMentions(d.mentions)
    }))
    .sort((a,b) => b.score - a.score)
    .slice(0, 10)
    .map((d, i) => ({ ...d, rank: i+1 }));
}
const CATEGORY_DATA = buildCategoryData();

// ============================================================
// CHART INSTANCES
// ============================================================
let chartInstances = {};

function destroyChart(id) {
  if (chartInstances[id]) {
    chartInstances[id].destroy();
    delete chartInstances[id];
  }
}

// ============================================================
// HERO MINI CHART
// ============================================================
function initHeroMiniChart() {
  const container = document.getElementById('heroMiniChart');
  if (!container) return;

  const canvas = document.createElement('canvas');
  canvas.style.width = '100%';
  canvas.style.height = '100%';
  container.appendChild(canvas);

  const labels = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'];
  const data1 = [62, 68, 71, 74, 78, 82, 85, 87];
  const data2 = [58, 61, 65, 69, 72, 75, 78, 81];

  chartInstances['heroMini'] = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          data: data1,
          borderColor: '#4ade80',
          backgroundColor: 'rgba(74,222,128,0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 0,
        },
        {
          data: data2,
          borderColor: 'rgba(96,165,250,0.7)',
          backgroundColor: 'transparent',
          borderWidth: 1.5,
          fill: false,
          tension: 0.4,
          pointRadius: 0,
          borderDash: [4, 4],
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales: {
        x: { display: false },
        y: { display: false, min: 50, max: 100 }
      },
      animation: { duration: 1500, easing: 'easeInOutQuart' }
    }
  });
}

// ============================================================
// SCORE RING
// ============================================================
function initScoreRing() {
  const canvas = document.getElementById('scoreRing');
  if (!canvas) return;
  destroyChart('scoreRing');

  const score = 87;
  chartInstances['scoreRing'] = new Chart(canvas, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [score, 100 - score],
        backgroundColor: ['#1a5c3a', '#f0f4f2'],
        borderWidth: 0,
        circumference: 270,
        rotation: 225,
      }]
    },
    options: {
      responsive: false,
      cutout: '78%',
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      animation: { duration: 1200, easing: 'easeInOutQuart' }
    }
  });
}

// ============================================================
// MENTIONS CHART
// ============================================================
const mentionsData = {
  '6m': {
    labels: ['Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'],
    positive: [2800, 3100, 3400, 3600, 3900, 4200],
    neutral: [800, 850, 900, 920, 950, 980],
    negative: [350, 380, 400, 420, 440, 460],
  },
  '1y': {
    labels: ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'],
    positive: [2100, 2400, 3200, 3600, 3100, 2800, 2800, 3100, 3400, 3600, 3900, 4200],
    neutral: [600, 680, 820, 900, 780, 750, 800, 850, 900, 920, 950, 980],
    negative: [280, 310, 390, 430, 380, 360, 350, 380, 400, 420, 440, 460],
  },
  '3y': {
    labels: ['2023 Q1', 'Q2', 'Q3', 'Q4', '2024 Q1', 'Q2', 'Q3', 'Q4', '2025 Q1', 'Q2', 'Q3', 'Q4'],
    positive: [1200, 1800, 2100, 2400, 2600, 3400, 3100, 3600, 3900, 4200, 4500, 4800],
    neutral: [400, 520, 600, 680, 720, 900, 780, 920, 950, 980, 1020, 1100],
    negative: [180, 240, 280, 310, 330, 430, 380, 420, 440, 460, 480, 510],
  }
};

function initMentionsChart(period = '1y') {
  const canvas = document.getElementById('mentionsChart');
  if (!canvas) return;
  destroyChart('mentionsChart');

  const d = mentionsData[period];
  chartInstances['mentionsChart'] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: d.labels,
      datasets: [
        {
          label: 'Positive',
          data: d.positive,
          backgroundColor: 'rgba(22,163,74,0.75)',
          borderRadius: 4,
          stack: 'stack',
        },
        {
          label: 'Neutral',
          data: d.neutral,
          backgroundColor: 'rgba(148,163,184,0.75)',
          borderRadius: 4,
          stack: 'stack',
        },
        {
          label: 'Negative',
          data: d.negative,
          backgroundColor: 'rgba(220,38,38,0.6)',
          borderRadius: 4,
          stack: 'stack',
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'top',
          labels: { font: { size: 11, family: 'Inter' }, boxWidth: 12, padding: 16 }
        },
        tooltip: {
          callbacks: {
            footer: (items) => {
              const total = items.reduce((s, i) => s + i.parsed.y, 0);
              return `Total: ${total.toLocaleString()}`;
            }
          }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 11, family: 'Inter' } } },
        y: {
          grid: { color: 'rgba(0,0,0,0.04)' },
          ticks: { font: { size: 11, family: 'Inter' }, callback: v => v >= 1000 ? (v/1000).toFixed(0)+'K' : v }
        }
      },
      animation: { duration: 800 }
    }
  });
}

function switchMentionChart(period, btn) {
  document.querySelectorAll('.chart-tab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
  initMentionsChart(period);
}

// ============================================================
// SENTIMENT CHART
// ============================================================
function initSentimentChart() {
  const canvas = document.getElementById('sentimentChart');
  if (!canvas) return;
  destroyChart('sentimentChart');

  chartInstances['sentimentChart'] = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: ['Positive', 'Neutral', 'Negative'],
      datasets: [{
        data: [72, 19, 9],
        backgroundColor: ['#16a34a', '#94a3b8', '#dc2626'],
        borderWidth: 0,
        hoverOffset: 8,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { font: { size: 11, family: 'Inter' }, boxWidth: 12, padding: 16 }
        },
        tooltip: {
          callbacks: { label: (c) => ` ${c.label}: ${c.parsed}%` }
        }
      },
      animation: { duration: 1000 }
    }
  });
}

// ============================================================
// REGIONAL CHART
// ============================================================
function initRegionalChart() {
  const canvas = document.getElementById('regionalChart');
  if (!canvas) return;
  destroyChart('regionalChart');

  const regions = ['Europe', 'N. America', 'Japan', 'China', 'Australia', 'S. America'];
  const scores = [91, 88, 85, 79, 82, 74];
  const colors = scores.map(s =>
    s >= 88 ? '#16a34a' : s >= 80 ? '#2d7a52' : s >= 74 ? '#3b82f6' : '#94a3b8'
  );

  chartInstances['regionalChart'] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: regions,
      datasets: [{
        label: 'Reputation Score',
        data: scores,
        backgroundColor: colors,
        borderRadius: 6,
        borderSkipped: false,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (c) => ` Score: ${c.parsed.x}` } }
      },
      scales: {
        x: {
          min: 60, max: 100,
          grid: { color: 'rgba(0,0,0,0.04)' },
          ticks: { font: { size: 11, family: 'Inter' } }
        },
        y: { grid: { display: false }, ticks: { font: { size: 11, family: 'Inter' } } }
      },
      animation: { duration: 800 }
    }
  });
}

// ============================================================
// KEYWORD CLOUD
// ============================================================
function initKeywordCloud() {
  const container = document.getElementById('keywordCloud');
  if (!container) return;

  const keywords = [
    { text: 'flowering', weight: 9, color: '#1a5c3a' },
    { text: 'fragrance', weight: 8, color: '#2d7a52' },
    { text: 'beautiful', weight: 8, color: '#16a34a' },
    { text: 'disease resistant', weight: 7, color: '#3b82f6' },
    { text: 'long-lasting', weight: 7, color: '#1a5c3a' },
    { text: 'color', weight: 6, color: '#2d7a52' },
    { text: 'pruning', weight: 5, color: '#94a3b8' },
    { text: 'vase life', weight: 6, color: '#3b82f6' },
    { text: 'repeat bloom', weight: 7, color: '#16a34a' },
    { text: 'shipping', weight: 4, color: '#dc2626' },
    { text: 'premium', weight: 5, color: '#94a3b8' },
    { text: 'garden', weight: 6, color: '#1a5c3a' },
    { text: 'cut flower', weight: 5, color: '#2d7a52' },
    { text: 'romantic', weight: 4, color: '#db2777' },
    { text: 'classic', weight: 4, color: '#94a3b8' },
    { text: 'award winning', weight: 6, color: '#ca8a04' },
  ];

  const sizes = [0.75, 0.85, 0.95, 1.05, 1.2, 1.4, 1.6, 1.8, 2.0];
  const maxW = Math.max(...keywords.map(k => k.weight));
  const minW = Math.min(...keywords.map(k => k.weight));

  keywords.sort(() => Math.random() - 0.5).forEach(kw => {
    const ratio = (kw.weight - minW) / (maxW - minW);
    const sizeIdx = Math.round(ratio * (sizes.length - 1));
    const fontSize = sizes[sizeIdx];
    const opacity = 0.6 + ratio * 0.4;

    const tag = document.createElement('span');
    tag.className = 'keyword-tag';
    tag.textContent = kw.text;
    tag.style.fontSize = `${fontSize}rem`;
    tag.style.color = kw.color;
    tag.style.opacity = opacity;
    tag.style.background = kw.color + '15';
    tag.style.border = `1px solid ${kw.color}30`;
    container.appendChild(tag);
  });
}

// ============================================================
// PRAISE CHART
// ============================================================
function initPraiseChart() {
  const canvas = document.getElementById('praiseChart');
  if (!canvas) return;
  destroyChart('praiseChart');

  const categories = ['Aesthetics', 'Fragrance', 'Durability', 'Disease Resist.', 'Ease of Care', 'Value'];
  chartInstances['praiseChart'] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: categories,
      datasets: [
        {
          label: 'Praise',
          data: [82, 76, 71, 68, 55, 60],
          backgroundColor: 'rgba(22,163,74,0.7)',
          borderRadius: 4,
        },
        {
          label: 'Complaints',
          data: [-8, -5, -12, -9, -22, -18],
          backgroundColor: 'rgba(220,38,38,0.6)',
          borderRadius: 4,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'top',
          labels: { font: { size: 11, family: 'Inter' }, boxWidth: 12, padding: 16 }
        },
        tooltip: {
          callbacks: { label: (c) => ` ${c.dataset.label}: ${Math.abs(c.parsed.y)}%` }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10, family: 'Inter' } } },
        y: {
          grid: { color: 'rgba(0,0,0,0.04)' },
          ticks: {
            font: { size: 11, family: 'Inter' },
            callback: v => Math.abs(v) + '%'
          }
        }
      },
      animation: { duration: 800 }
    }
  });
}

// ============================================================
// RADAR CHART (COMPARE)
// ============================================================
function initRadarChart() {
  const canvas = document.getElementById('radarChart');
  if (!canvas) return;
  destroyChart('radarChart');

  chartInstances['radarChart'] = new Chart(canvas, {
    type: 'radar',
    data: {
      labels: ['Reputation', 'Mentions', 'Pos. Sentiment', 'Growth', 'Confidence', 'Stability'],
      datasets: [
        {
          label: "Rosa 'Eden'",
          data: [87, 82, 72, 78, 91, 85],
          borderColor: '#1a5c3a',
          backgroundColor: 'rgba(26,92,58,0.12)',
          borderWidth: 2,
          pointBackgroundColor: '#1a5c3a',
          pointRadius: 4,
        },
        {
          label: "Rosa 'Queen Elizabeth'",
          data: [81, 68, 65, 52, 87, 74],
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59,130,246,0.1)',
          borderWidth: 2,
          pointBackgroundColor: '#3b82f6',
          pointRadius: 4,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { font: { size: 11, family: 'Inter' }, boxWidth: 12, padding: 16 }
        }
      },
      scales: {
        r: {
          min: 40, max: 100,
          ticks: { font: { size: 10, family: 'Inter' }, stepSize: 20 },
          pointLabels: { font: { size: 11, family: 'Inter', weight: '600' } },
          grid: { color: 'rgba(0,0,0,0.06)' },
          angleLines: { color: 'rgba(0,0,0,0.06)' }
        }
      },
      animation: { duration: 1000 }
    }
  });
}

// ============================================================
// TREND COMPARE CHART
// ============================================================
function initTrendCompareChart() {
  const canvas = document.getElementById('trendCompareChart');
  if (!canvas) return;
  destroyChart('trendCompareChart');

  const labels = ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'];
  chartInstances['trendCompareChart'] = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: "Rosa 'Eden'",
          data: [78, 79, 81, 82, 80, 81, 83, 84, 84, 85, 86, 87],
          borderColor: '#1a5c3a',
          backgroundColor: 'rgba(26,92,58,0.06)',
          borderWidth: 2.5,
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointBackgroundColor: '#1a5c3a',
        },
        {
          label: "Rosa 'Queen Elizabeth'",
          data: [83, 83, 82, 82, 83, 82, 81, 82, 81, 80, 81, 81],
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59,130,246,0.04)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointBackgroundColor: '#3b82f6',
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { font: { size: 11, family: 'Inter' }, boxWidth: 12, padding: 16 }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 11, family: 'Inter' } } },
        y: {
          min: 70, max: 95,
          grid: { color: 'rgba(0,0,0,0.04)' },
          ticks: { font: { size: 11, family: 'Inter' } }
        }
      },
      animation: { duration: 800 }
    }
  });
}

// ============================================================
// CATEGORY CHART
// ============================================================
function initCategoryChart() {
  const canvas = document.getElementById('categoryChart');
  if (!canvas) return;
  destroyChart('categoryChart');

  const cats = ['Rose', 'Chrysanthemum', 'Petunia', 'Lavender', 'Hydrangea', 'Tulip', 'Orchid'];
  const scores = [82, 78, 72, 88, 85, 74, 80];
  const colors = scores.map(s =>
    s >= 85 ? '#16a34a' : s >= 78 ? '#2d7a52' : s >= 72 ? '#3b82f6' : '#94a3b8'
  );

  chartInstances['categoryChart'] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: cats,
      datasets: [{
        label: 'Avg. Reputation Score',
        data: scores,
        backgroundColor: colors,
        borderRadius: 6,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (c) => ` Score: ${c.parsed.y}` } }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 11, family: 'Inter' } } },
        y: {
          min: 60, max: 100,
          grid: { color: 'rgba(0,0,0,0.04)' },
          ticks: { font: { size: 11, family: 'Inter' } }
        }
      },
      animation: { duration: 800 }
    }
  });
}

// ============================================================
// VOLUME CHART
// ============================================================
function initVolumeChart() {
  const canvas = document.getElementById('volumeChart');
  if (!canvas) return;
  destroyChart('volumeChart');

  const labels = ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'];
  const data = [210, 240, 320, 380, 290, 260, 270, 310, 340, 360, 390, 420];

  chartInstances['volumeChart'] = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Total Mentions (K)',
        data,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59,130,246,0.08)',
        borderWidth: 2.5,
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointBackgroundColor: '#3b82f6',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (c) => ` ${c.parsed.y}K mentions` } }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 11, family: 'Inter' } } },
        y: {
          grid: { color: 'rgba(0,0,0,0.04)' },
          ticks: { font: { size: 11, family: 'Inter' }, callback: v => v + 'K' }
        }
      },
      animation: { duration: 800 }
    }
  });
}

// ============================================================
// SEARCH LOGIC
// ============================================================
let currentQuery = '';

function handleSearch(val) {
  currentQuery = val;
  const ac = document.getElementById('searchAutocomplete');
  if (!val || val.length < 1) {
    ac.style.display = 'none';
    return;
  }

  // Use new fuzzy search engine
  const matches = typeof getAutocompleteSuggestions === 'function'
    ? getAutocompleteSuggestions(val)
    : VARIETIES_DATA.filter(v =>
        v.name.toLowerCase().includes(val.toLowerCase()) ||
        (v.aka && v.aka.toLowerCase().includes(val.toLowerCase())) ||
        v.category.toLowerCase().includes(val.toLowerCase())
      ).slice(0, 8);

  if (matches.length === 0) {
    ac.style.display = 'none';
    return;
  }

  ac.innerHTML = matches.map(v => `
    <div class="autocomplete-item" onclick="quickSearch('${v.name.replace(/'/g, "\\'")}")">
      <span>
        ${v.name}
        ${v.zhName ? `<small style="color:var(--primary-light);margin-left:4px">${v.zhName}</small>` : ''}
        <small style="color:var(--text-muted);margin-left:4px">${v.category}</small>
      </span>
      <span class="autocomplete-score">${v.score}</span>
    </div>
  `).join('');
  ac.style.display = 'block';
}

function performSearch() {
  const ac = document.getElementById('searchAutocomplete');
  ac.style.display = 'none';
  renderSearchResults(currentQuery);
}

function quickSearch(name) {
  document.getElementById('searchInput').value = name;
  currentQuery = name;
  document.getElementById('searchAutocomplete').style.display = 'none';
  renderSearchResults(name);
  document.getElementById('search-section').scrollIntoView({ behavior: 'smooth' });
}

function filterResults() {
  renderSearchResults(currentQuery);
}

function renderSearchResults(query = '') {
  const grid = document.getElementById('resultsGrid');

  // Get filter values by ID
  const filters = {
    category: (document.getElementById('filterCategory') || {}).value || '',
    region:   (document.getElementById('filterRegion')   || {}).value || '',
    season:   (document.getElementById('filterSeason')   || {}).value || ''
  };

  // Use the new search engine from varieties.js
  let results = typeof searchVarieties === 'function'
    ? searchVarieties(query, filters)
    : VARIETIES_DATA.filter(v =>
        !query ||
        v.name.toLowerCase().includes(query.toLowerCase()) ||
        (v.aka && v.aka.toLowerCase().includes(query.toLowerCase())) ||
        v.category.toLowerCase().includes(query.toLowerCase())
      );

  if (results.length === 0) {
    // Suggest similar categories
    const cats = typeof getAllCategories === 'function' ? getAllCategories().slice(0,6) : [];
    grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;color:var(--text-muted);padding:3rem 1rem">
      <div style="font-size:2.5rem;margin-bottom:1rem">🔍</div>
      <div style="font-size:1.1rem;font-weight:600;color:var(--text-primary);margin-bottom:0.5rem">No varieties found for "${query}"</div>
      <div style="font-size:0.9rem;margin-bottom:1.5rem">Try searching by cultivar name, Chinese name, category, breeder, or trait keyword.</div>
      ${cats.length ? `<div style="font-size:0.85rem;color:var(--text-muted)">Browse categories: ${cats.map(c => `<span onclick="quickSearch('${c}')" style="cursor:pointer;color:var(--primary-light);margin:0 4px">${c}</span>`).join('')}</div>` : ''}
    </div>`;
    return;
  }

  // Limit display to 24 cards
  const display = results.slice(0, 24);
  grid.innerHTML = display.map(v => `
    <div class="variety-card animate-in" onclick="scrollTo('#variety-detail')">
      <div class="vc-category">${v.category}</div>
      <div class="vc-name">${v.name}${v.aka ? ` <small style="font-weight:400;color:var(--text-muted)">(${v.aka})</small>` : ''}${v.zhName ? ` <small style="font-weight:400;color:var(--primary-light)">${v.zhName}</small>` : ''}</div>
      <div class="vc-score-row">
        <div class="vc-score">
          <span class="vc-score-num">${v.score}</span>
          <span class="vc-score-max">/100</span>
        </div>
        <span class="${v.trendDir === 'up' ? 'vc-trend-up' : 'vc-trend-down'}">
          ${v.trendDir === 'up' ? '↑' : '↓'} ${v.trend}
        </span>
      </div>
      <div class="vc-sentiment-bar">
        <div class="vc-sent-pos" style="width:${v.pos}%"></div>
        <div class="vc-sent-neu" style="width:${v.neu}%"></div>
        <div class="vc-sent-neg" style="width:${v.neg}%"></div>
      </div>
      <div class="vc-meta">
        <span class="vc-mentions">${(v.mentions/1000).toFixed(1)}K mentions</span>
        <span>${v.region}</span>
      </div>
      ${v.confidence === 'low' ? '<div style="font-size:0.7rem;color:#f59e0b;margin-top:4px">⚠ Low confidence data</div>' : ''}
    </div>
  `).join('');

  if (results.length > 24) {
    grid.innerHTML += `<div style="grid-column:1/-1;text-align:center;color:var(--text-muted);padding:1rem;font-size:0.9rem">
      Showing 24 of ${results.length} results. Refine your search to narrow down.
    </div>`;
  }
}

// ============================================================
// INSIGHTS TABS
// ============================================================
function switchInsightTab(tab, btn) {
  document.querySelectorAll('.ins-tab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');

  let data;
  let isAlert = false;
  switch (tab) {
    case 'top10': data = TOP10_DATA; break;
    case 'rising': data = RISING_DATA; break;
    case 'declining': data = DECLINING_DATA; isAlert = true; break;
    case 'category': data = CATEGORY_DATA; break;
  }
  renderInsightsList(data, isAlert);
}

function renderInsightsList(data, isAlert = false) {
  const container = document.getElementById('insightsContent');
  const rankClasses = ['gold', 'silver', 'bronze'];

  container.innerHTML = `
    <div class="insights-list fade-in">
      ${data.map((item, i) => `
        <div class="insight-row">
          <div class="insight-rank ${rankClasses[i] || ''}">${item.rank}</div>
          <div class="insight-info">
            <div class="insight-name">${item.name}</div>
            <div class="insight-category">${item.category}</div>
          </div>
          <div class="insight-score">${item.score}</div>
          <div class="insight-trend ${isAlert || item.trend.startsWith('-') ? 'down' : 'up'}">
            ${item.trend.startsWith('-') ? '↓' : '↑'} ${item.trend}
          </div>
          <div class="insight-mentions">${item.mentions}<br/><span style="font-size:0.7rem">mentions</span></div>
        </div>
      `).join('')}
    </div>
  `;
}

// ============================================================
// COMPARE LOGIC
// ============================================================
function addToCompare(name) {
  const slot3 = document.getElementById('slot3');
  const content = slot3.querySelector('.slot-content');
  if (content && content.classList.contains('empty')) {
    content.classList.remove('empty');
    content.classList.add('active');
    content.innerHTML = `
      <div class="slot-name">${name}</div>
      <div class="slot-score">87</div>
      <button class="slot-remove" onclick="removeFromCompare(3)">×</button>
    `;
    showToast(`"${name}" added to comparison`);
  }
}

function removeFromCompare(slot) {
  const el = document.getElementById(`slot${slot}`);
  const content = el.querySelector('.slot-content');
  content.classList.remove('active');
  content.classList.add('empty');
  content.innerHTML = `
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
    <span>Add Variety</span>
  `;
  content.onclick = () => showModal('add-variety-modal');
}

function handleCompareSearch(val) {
  const container = document.getElementById('compareSearchResults');
  if (!val || val.length < 2) {
    container.innerHTML = '';
    return;
  }

  const matches = VARIETIES_DATA.filter(v =>
    v.name.toLowerCase().includes(val.toLowerCase()) ||
    v.category.toLowerCase().includes(val.toLowerCase())
  ).slice(0, 8);

  container.innerHTML = matches.map(v => `
    <div class="compare-result-item" onclick="selectCompareVariety('${v.name.replace(/'/g, "\\'")}', ${v.score})">
      <span>${v.name} <small style="color:var(--text-muted)">${v.category}</small></span>
      <span style="font-weight:700;color:var(--primary)">${v.score}</span>
    </div>
  `).join('');
}

function selectCompareVariety(name, score) {
  closeModal('add-variety-modal');
  const slot3 = document.getElementById('slot3');
  const content = slot3.querySelector('.slot-content');
  content.classList.remove('empty');
  content.classList.add('active');
  content.innerHTML = `
    <div class="slot-name">${name}</div>
    <div class="slot-score">${score}</div>
    <button class="slot-remove" onclick="removeFromCompare(3)">×</button>
  `;
  showToast(`"${name}" added to comparison`);
}

// ============================================================
// MODAL LOGIC
// ============================================================
function showModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.remove('open');
    document.body.style.overflow = '';
  }
}

function closeModalOnOverlay(e, id) {
  if (e.target === e.currentTarget) closeModal(id);
}

function switchModalTab(tab, btn) {
  document.querySelectorAll('.modal-tab').forEach(t => t.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('modal-login-form').style.display = tab === 'login' ? 'block' : 'none';
  document.getElementById('modal-signup-form').style.display = tab === 'signup' ? 'block' : 'none';
}

// ============================================================
// TOAST
// ============================================================
function showToast(msg) {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = msg;
  toast.style.cssText = `
    position:fixed;bottom:5rem;left:50%;transform:translateX(-50%);
    background:var(--primary);color:white;padding:0.75rem 1.5rem;
    border-radius:100px;font-size:0.875rem;font-weight:600;
    box-shadow:var(--shadow-lg);z-index:3000;
    animation:fadeInUp 0.3s ease;
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2500);
}

// ============================================================
// COUNTER ANIMATION
// ============================================================
function animateCounters() {
  document.querySelectorAll('.stat-num[data-target]').forEach(el => {
    const target = parseInt(el.dataset.target);
    const duration = 2000;
    const start = performance.now();

    function update(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(eased * target);

      if (target >= 1000000) {
        el.textContent = (current / 1000000).toFixed(1) + 'M+';
      } else if (target >= 10000) {
        el.textContent = (current / 1000).toFixed(1) + 'K+';
      } else if (target === 98) {
        el.textContent = current + '%';
      } else {
        el.textContent = current.toLocaleString() + '+';
      }

      if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  });
}

// ============================================================
// SCROLL EFFECTS
// ============================================================
function initScrollEffects() {
  const navbar = document.getElementById('navbar');
  const scrollTop = document.getElementById('scrollTop');

  window.addEventListener('scroll', () => {
    const y = window.scrollY;
    navbar.classList.toggle('scrolled', y > 20);
    scrollTop.classList.toggle('visible', y > 400);
  });

  // Intersection Observer for scroll-in animations
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('anim-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.05 });

  document.querySelectorAll('.method-step, .role-card, .ai-card').forEach(el => {
    el.classList.add('anim-hidden');
    observer.observe(el);
  });
}

// ============================================================
// SCROLL HELPER
// ============================================================
function scrollTo(selector) {
  const el = document.querySelector(selector);
  if (el) el.scrollIntoView({ behavior: 'smooth' });
}

// ============================================================
// MOBILE MENU
// ============================================================
function toggleMobileMenu() {
  const menu = document.getElementById('mobile-menu');
  menu.classList.toggle('open');
}

// Close mobile menu on link click
document.addEventListener('click', (e) => {
  if (e.target.tagName === 'A' && e.target.closest('.mobile-menu')) {
    document.getElementById('mobile-menu').classList.remove('open');
  }
});

// ============================================================
// INIT
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  // Init charts
  initHeroMiniChart();
  initScoreRing();
  initMentionsChart('1y');
  initSentimentChart();
  initRegionalChart();
  initKeywordCloud();
  initPraiseChart();
  initRadarChart();
  initTrendCompareChart();
  initCategoryChart();
  initVolumeChart();

  // Init search results (show all by default)
  renderSearchResults();

  // Init insights
  renderInsightsList(TOP10_DATA);

  // Init scroll effects
  initScrollEffects();

  // Animate counters when hero is visible
  const heroObserver = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      animateCounters();
      heroObserver.disconnect();
    }
  }, { threshold: 0.3 });
  const heroStats = document.querySelector('.hero-stats');
  if (heroStats) heroObserver.observe(heroStats);

  // Close autocomplete on outside click
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-box')) {
      document.getElementById('searchAutocomplete').style.display = 'none';
    }
  });

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.open').forEach(m => {
        m.classList.remove('open');
        document.body.style.overflow = '';
      });
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      document.getElementById('searchInput').focus();
      document.getElementById('search-section').scrollIntoView({ behavior: 'smooth' });
    }
  });
});
