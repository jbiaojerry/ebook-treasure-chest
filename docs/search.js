// ====== 模块划分重构 Begin ======

// -- 数据模块 --
const DataModule = (() => {
    let metaData = null, allBooksCache = null;

    async function loadMeta() {
        try {
            const response = await fetch('data/meta.json', { cache: 'no-store' });
            if (!response.ok) throw new Error(`元数据加载失败 (${response.status})`);
            metaData = await response.json();
            if (!metaData.categories || !Array.isArray(metaData.categories)) throw new Error('元数据缺少分类信息');
            return metaData;
        } catch (e) {
            return null;
        }
    }

    async function loadAllBooks(categories) {
        if (allBooksCache) return allBooksCache;
        if (!categories || !categories.length) return [];
        try {
            const fetches = categories.map(category =>
                fetch(`data/books/${category}.json`).then(res => {
                    if (!res.ok) return [];
                    return res.json().then(books => Array.isArray(books) ? books.map(b => ({...b, category})) : []);
                }).catch(() => [])
            );
            const results = await Promise.allSettled(fetches);
            allBooksCache = results.filter(r => r.status === 'fulfilled').flatMap(r => r.value);
            return allBooksCache;
        } catch (e) {
            return [];
        }
    }

    return { loadMeta, loadAllBooks };
})();

// -- 视图模块 --
const ViewModule = (() => {
    function safeGet(id) { return document.getElementById(id); }

    function showLoading(show, message = '加载中...') {
        const loading = safeGet('loading');
        const m = safeGet('loading-message');
        if (loading) loading.style.display = show ? 'flex' : 'none';
        if (m && show) m.textContent = message;
    }

    function showError(message, onRetry) {
        // 页面统一错误区块（如无则 alert 兜底），优先使用 emptyState 区
        const empty = safeGet('emptyState');
        const container = safeGet('resultsContainer');
        if (empty) {
            empty.style.display = 'block';
            empty.innerHTML = `
                <div class="empty-icon">⚠️</div>
                <h3>发生错误</h3>
                <p>${message || '出现未知异常'}</p>
                ${onRetry ? `<button id="retryBtn" class="retry-btn">重试</button>` : ''}
            `;
            if (container) container.innerHTML = '';
            if (onRetry) {
                setTimeout(() => {
                    const btn = document.getElementById('retryBtn');
                    btn && (btn.onclick = onRetry);
                }, 50);
            }
        } else {
            alert(message);
        }
    }

    function hideError() {
        const empty = safeGet('emptyState');
        if(empty) empty.style.display = 'none';
    }

    return { showLoading, showError, hideError, safeGet };
})();

// ====== 模块划分重构 End ======


// 全局变量
let metaData = null;
let allBooksCache = null; // 用于缓存所有书籍数据，避免重复加载
let currentResults = [];
let currentPage = 1;
const resultsPerPage = 20;

// DOM 元素
const searchInput = document.getElementById('searchInput');
const searchButton = document.getElementById('searchButton');
const resultsSection = document.getElementById('resultsSection');
const resultsContainer = document.getElementById('resultsContainer');
const resultsTitle = document.getElementById('resultsTitle');
const resultsCount = document.getElementById('resultsCount');
const browseSection = document.getElementById('browseSection');
const categoryGrid = document.getElementById('categoryGrid');
const navItems = document.getElementById('navItems');
const loading = document.getElementById('loading');
const emptyState = document.getElementById('emptyState');
const pagination = document.getElementById('pagination');
const statsSection = document.getElementById('statsSection');

/* ==== 控制器主入口重构 ==== */
document.addEventListener('DOMContentLoaded', function() {
    mainInit();
});

async function mainInit() {
    ViewModule.showLoading(true, '正在初始化应用...');
    ViewModule.hideError();
    const meta = await DataModule.loadMeta();
    if (!meta) {
        ViewModule.showLoading(false);
        ViewModule.showError('数据加载失败，请检查网络或文件并重试。', mainInit);
        return;
    }
    metaData = meta;
    ViewModule.showLoading(false);
    displayStats();
    displayCategories();
    displayHotCategories();
    setupEventListeners();
}


// 设置事件监听器
// 防抖工具
function debounce(fn, delay = 250) {
    let timer = null;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

function setupEventListeners() {
    // 防抖搜索（回车或按钮）
    const debouncedSearch = debounce(handleSearch, 250);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            debouncedSearch();
        }
    });
    searchButton.addEventListener('click', debouncedSearch);

    // 分类点击防抖
    const debouncedCategory = debounce(function(e) {
        const categoryItem = e.target.closest('.nav-item, .category-item');
        if (categoryItem) {
            const category = categoryItem.dataset.category;
            searchByCategory(category);
        }
    }, 250);
    document.addEventListener('click', debouncedCategory);
}

// 处理搜索（模块化与健壮性重构）
function handleSearch() {
    const query = searchInput.value.trim().toLowerCase();
    if (!query) {
        showBrowseSection();
        return;
    }
    if (!metaData) {
        ViewModule.showError('页面尚未初始化完成，请稍候。', mainInit);
        return;
    }
    ViewModule.showLoading(true, '正在搜索中...');
    setTimeout(async () => {
        try {
            const allBooks = await DataModule.loadAllBooks(metaData.categories);
            if (!allBooks || !allBooks.length) {
                ViewModule.showLoading(false);
                ViewModule.showError('未能获取到任何书籍数据，请刷新或稍后再试。');
                return;
            }
            currentResults = allBooks.filter(book => {
                const t = (book.title || '').toLowerCase();
                const a = (book.author || '').toLowerCase();
                return t.includes(query) || a.includes(query);
            });
            currentPage = 1;
            displaySearchResults(`关键词: ${searchInput.value.trim()}`);
        } catch (error) {
            console.error('搜索时发生错误:', error);
            ViewModule.showError('搜索时发生未知错误，请重试。');
        } finally {
            ViewModule.showLoading(false);
        }
    }, 10);
}

// 按分类搜索（模块化与健壮性重构）
async function searchByCategory(category) {
    ViewModule.showLoading(true, `正在加载分类: ${category}...`);
    try {
        if (!metaData || !metaData.categories.includes(category)) {
            ViewModule.showLoading(false);
            ViewModule.showError(`分类 "${category}" 不存在或数据未初始化。`, mainInit);
            return;
        }
        const allBooks = await DataModule.loadAllBooks(metaData.categories);
        const books = allBooks.filter(book => book.category === category);
        currentResults = books;
        currentPage = 1;
        displaySearchResults(`分类: ${category}`);
    } catch (error) {
        console.error(`加载分类 ${category} 出错:`, error);
        ViewModule.showError(`加载分类 "${category}" 失败`);
    } finally {
        ViewModule.showLoading(false);
    }
}


// 显示搜索结果
// 渲染搜索结果 - 加强健壮性
function displaySearchResults(query) {
    hideAllSections();
    const resultsSectionEl = ViewModule.safeGet('resultsSection');
    if (resultsSectionEl) resultsSectionEl.style.display = 'block';

    const resultsTitleEl = ViewModule.safeGet('resultsTitle');
    if (resultsTitleEl) resultsTitleEl.textContent = `"${query}" 的搜索结果`;

    const resultsCountEl = ViewModule.safeGet('resultsCount');
    if (resultsCountEl) resultsCountEl.textContent = `共找到 ${currentResults.length} 本书籍`;

    const resultsContainerEl = ViewModule.safeGet('resultsContainer');
    const paginationEl = ViewModule.safeGet('pagination');
    const emptyStateEl = ViewModule.safeGet('emptyState');

    if (currentResults.length === 0) {
        if (resultsContainerEl) resultsContainerEl.innerHTML = '';
        if (emptyStateEl) emptyStateEl.style.display = 'block';
        if (paginationEl) paginationEl.innerHTML = '';
        return;
    }
    if (emptyStateEl) emptyStateEl.style.display = 'none';

    const startIndex = (currentPage - 1) * resultsPerPage;
    const endIndex = startIndex + resultsPerPage;
    const pageResults = currentResults.slice(startIndex, endIndex);

    if (resultsContainerEl) {
        resultsContainerEl.innerHTML = pageResults.map(book => `
            <div class="book-item">
                <div class="book-info">
                    <h3 class="book-title">${highlightText(book.title, searchInput.value)}</h3>
                    <p class="book-author">作者: ${highlightText(book.author, searchInput.value)}</p>
                    <span class="book-category">${book.category || '未知'}</span>
                </div>
                <div class="book-actions">
                    ${book.downloadUrl ? 
                        `<a href="${book.downloadUrl}" target="_blank" rel="noopener" class="download-btn">
                            <span class="download-icon">📥</span>
                            下载
                        </a>` : 
                        '<span class="no-download">暂无下载</span>'
                    }
                </div>
            </div>
        `).join('');
    }

    renderPagination();
}

// 高亮匹配文本 (保持不变)
function highlightText(text, query) {
    if (!query || !text) return text;
    try {
        const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    } catch (e) {
        return text;
    }
}

// 转义正则表达式特殊字符 (保持不变)
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// 渲染分页 (保持不变)
// 分页健壮化
function renderPagination() {
    const paginationEl = ViewModule.safeGet('pagination');
    const totalPages = Math.ceil(currentResults.length / resultsPerPage);
    if (!paginationEl) return;
    if (totalPages <= 1) {
        paginationEl.innerHTML = '';
        return;
    }
    let paginationHTML = '';
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (currentPage > 1) paginationHTML += `<button class="page-btn" onclick="goToPage(${currentPage - 1})">上一页</button>`;
    if (startPage > 1) paginationHTML += `<button class="page-btn" onclick="goToPage(1)">1</button>`;
    if (startPage > 2) paginationHTML += `<span class="page-ellipsis">...</span>`;

    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }

    if (endPage < totalPages - 1) paginationHTML += `<span class="page-ellipsis">...</span>`;
    if (endPage < totalPages) paginationHTML += `<button class="page-btn" onclick="goToPage(${totalPages})">${totalPages}</button>`;
    if (currentPage < totalPages) paginationHTML += `<button class="page-btn" onclick="goToPage(${currentPage + 1})">下一页</button>`;

    paginationEl.innerHTML = paginationHTML;
}

// 跳转到指定页 (逻辑简化)
// 分页跳转（安全处理）
function goToPage(page) {
    currentPage = page;
    displaySearchResults(searchInput.value || '分类浏览');
    const resultsSectionEl = ViewModule.safeGet('resultsSection');
    if (resultsSectionEl && resultsSectionEl.scrollIntoView) {
        resultsSectionEl.scrollIntoView({ behavior: 'smooth' });
    }
}

// 显示统计信息
function displayStats() {
    if (!metaData) return;
    const booksEl = ViewModule.safeGet('totalBooks');
    const catsEl = ViewModule.safeGet('totalCategories');
    const dateEl = ViewModule.safeGet('lastUpdated');
    if (booksEl) booksEl.textContent = (metaData.stats.totalBooks || 0).toLocaleString();
    if (catsEl) catsEl.textContent = metaData.stats.totalCategories || '-';
    if (dateEl) {
        const lastUpdated = metaData.stats.lastUpdated ? new Date(metaData.stats.lastUpdated) : '';
        dateEl.textContent = lastUpdated ? lastUpdated.toLocaleDateString('zh-CN') : '-';
    }
}

// 显示分类网格 (移除书籍数量显示，因为需要异步加载)
function displayCategories() {
    if (!metaData) return;
    const gridEl = ViewModule.safeGet('categoryGrid');
    if (!gridEl) return;
    const categoryHTML = metaData.categories.map(category => `
        <div class="category-item" data-category="${category}">
            <span class="category-name">${category}</span>
        </div>
    `).join('');
    gridEl.innerHTML = categoryHTML;
}

// 显示热门分类导航 (移除书籍数量显示)
function displayHotCategories() {
    if (!metaData) return;
    const navItemsEl = ViewModule.safeGet('navItems');
    if (!navItemsEl) return;
    // 简单取前10个分类作为热门
    const hotCategories = metaData.categories.slice(0, 10);
    const navHTML = hotCategories.map(category => 
        `<span class="nav-item" data-category="${category}">${category}</span>`
    ).join('');
    navItemsEl.innerHTML = navHTML;
}

// UI状态函数 (保持不变)
function showBrowseSection() {
    hideAllSections();
    const browseSectionEl = ViewModule.safeGet('browseSection');
    const statsSectionEl = ViewModule.safeGet('statsSection');
    if (browseSectionEl) browseSectionEl.style.display = 'block';
    if (statsSectionEl) statsSectionEl.style.display = 'block';
}
function hideAllSections() {
    const resultsSectionEl = ViewModule.safeGet('resultsSection');
    const browseSectionEl = ViewModule.safeGet('browseSection');
    const emptyStateEl = ViewModule.safeGet('emptyState');
    const statsSectionEl = ViewModule.safeGet('statsSection');
    if (resultsSectionEl) resultsSectionEl.style.display = 'none';
    if (browseSectionEl) browseSectionEl.style.display = 'none';
    if (emptyStateEl) emptyStateEl.style.display = 'none';
    if (statsSectionEl) statsSectionEl.style.display = 'none';
}
function showLoading(show, message = '加载中...') {
    // 为了显示自定义消息, 请确保您的 index.html 中 #loading 元素内有一个 id 为 'loading-message' 的子元素
    // 例如: <div id="loading"><div class="spinner"></div><span id="loading-message"></span></div>
    const loadingMessageEl = document.getElementById('loading-message');
    if (show) {
        if (loadingMessageEl) {
            loadingMessageEl.textContent = message;
        }
        loading.style.display = 'flex';
    } else {
        loading.style.display = 'none';
    }
}
function showError(message) {
    // 兼容旧调用，自动转向新模块
    ViewModule.showError(message);
}

// 导出函数供全局使用
window.goToPage = goToPage;
