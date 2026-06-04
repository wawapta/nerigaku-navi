/**
 * ねりがくナビ — メインJS
 * RSS取得、Fuse.js検索、共通UI処理
 */

// ========================================
// RSS フィード読み込み
// ========================================
async function loadRssSection(jsonPath, containerId, maxItems = 5) {
  const container = document.getElementById(containerId);
  if (!container) return;

  try {
    const res = await fetch(jsonPath + '?_=' + Date.now());
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();

    if (!data.items || data.items.length === 0) {
      container.innerHTML = '<div class="news-error">現在、情報を取得できませんでした。<br>しばらくしてから再度お試しください。</div>';
      return;
    }

    const items = data.items.slice(0, maxItems);
    container.innerHTML = '';
    items.forEach(item => {
      const el = document.createElement('a');
      el.className = 'news-item ext-icon';
      el.href = item.url;
      el.target = '_blank';
      el.rel = 'noopener noreferrer';
      el.setAttribute('aria-label', item.title + '（外部リンク）');

      const dateStr = item.date ? formatDate(item.date) : '';
      el.innerHTML = `
        <span class="news-date">${escHtml(dateStr)}</span>
        <span class="news-title">${escHtml(item.title)}</span>
        <span class="news-arrow">›</span>
      `;
      container.appendChild(el);
    });
  } catch (err) {
    console.warn('RSS load error:', jsonPath, err);
    container.innerHTML = '<div class="news-error">情報を取得できませんでした</div>';
  }
}

function formatDate(dateStr) {
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return `${d.getMonth() + 1}/${d.getDate()}`;
  } catch { return dateStr; }
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ========================================
// Fuse.js 全文検索
// ========================================
let searchIndex = null;
let fuseInstance = null;

async function initSearch() {
  try {
    const [soudanRes, hinagataRes] = await Promise.all([
      fetch('/data/soudan.json'),
      fetch('/data/hinagata.json'),
    ]);
    const soudan = await soudanRes.json();
    const hinagata = await hinagataRes.json();

    const docs = [
      ...soudan.map(d => ({
        type: 'soudan',
        typeLabel: '相談先',
        title: d.title,
        description: d.description,
        tags: (d.tags || []).join(' '),
        url: '/soudan#' + d.category,
      })),
      ...hinagata.map(d => ({
        type: 'hinagata',
        typeLabel: 'ひな型',
        title: d.title,
        description: d.description,
        tags: (d.tags || []).join(' '),
        url: d.url,
        externalUrl: true,
      })),
    ];

    // Fuse.js CDN版をロード済みであること前提
    fuseInstance = new Fuse(docs, {
      keys: [
        { name: 'title', weight: 0.6 },
        { name: 'description', weight: 0.3 },
        { name: 'tags', weight: 0.1 },
      ],
      threshold: 0.4,
      includeScore: true,
      minMatchCharLength: 2,
    });
  } catch (err) {
    console.warn('Search init error:', err);
  }
}

function performSearch(query) {
  const resultsEl = document.getElementById('search-results');
  if (!resultsEl) return;

  query = query.trim();
  if (!query || query.length < 1) {
    resultsEl.innerHTML = '';
    resultsEl.classList.remove('active');
    return;
  }

  if (!fuseInstance) {
    resultsEl.innerHTML = '<div class="news-loading">検索の準備中...</div>';
    resultsEl.classList.add('active');
    return;
  }

  const results = fuseInstance.search(query).slice(0, 8);

  if (results.length === 0) {
    resultsEl.innerHTML = '<div class="news-loading">「' + escHtml(query) + '」の検索結果はありません</div>';
    resultsEl.classList.add('active');
    return;
  }

  resultsEl.innerHTML = '';
  results.forEach(({ item }) => {
    const el = document.createElement('div');
    el.className = 'search-result-item';
    const isExt = item.externalUrl && item.url !== 'PLACEHOLDER_DRIVE_URL';
    el.innerHTML = `
      <span class="search-result-label">${escHtml(item.typeLabel)}</span>
      <span class="search-result-title">${escHtml(item.title)}</span>
      <span class="search-result-desc">${escHtml(item.description)}</span>
    `;
    el.addEventListener('click', () => {
      if (item.url === 'PLACEHOLDER_DRIVE_URL') {
        alert('このひな型は準備中です');
        return;
      }
      if (isExt) {
        window.open(item.url, '_blank', 'noopener');
      } else {
        window.location.href = item.url;
      }
    });
    resultsEl.appendChild(el);
  });

  resultsEl.classList.add('active');
}

// ========================================
// 検索 UI バインド
// ========================================
function bindSearchUI() {
  const input = document.getElementById('search-input');
  if (!input) return;

  let debounceTimer;
  input.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => performSearch(input.value), 250);
  });

  input.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      input.value = '';
      performSearch('');
      input.blur();
    }
  });

  // 検索ボタン
  const btn = document.getElementById('search-btn');
  if (btn) {
    btn.addEventListener('click', () => performSearch(input.value));
  }
}

// ========================================
// ボトムナビ アクティブ制御
// ========================================
function setActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.remove('active');
    const href = el.getAttribute('href') || '';
    if (path === '/' && href === '/') el.classList.add('active');
    else if (href !== '/' && path.startsWith(href)) el.classList.add('active');
  });
}

// ========================================
// ページ初期化
// ========================================
document.addEventListener('DOMContentLoaded', () => {
  initSearch();
  bindSearchUI();
  setActiveNav();

  // トップページのみRSSロード
  if (document.getElementById('rss-nerima-news')) {
    loadRssSection('/data/nerima-news.json', 'rss-nerima-news', 5);
  }
  if (document.getElementById('rss-nerima-events')) {
    loadRssSection('/data/nerima-events.json', 'rss-nerima-events', 3);
  }
  if (document.getElementById('rss-kopren-note')) {
    loadRssSection('/data/kopren-note.json', 'rss-kopren-note', 3);
  }
});
