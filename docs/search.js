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

// 初始化
document.addEventListener('DOMContentLoaded', async function() {
    await loadInitialData();
    setupEventListeners();
});

// 仅加载初始元数据
async function loadInitialData() {
    try {
        showLoading(true, '正在初始化应用...');
        const response = await fetch('data/meta.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        metaData = await response.json();
        
        displayStats();
        displayCategories();
        displayHotCategories();
        
    } catch (error) {
        console.error('加载初始元数据失败:', error);
        showError('数据加载失败，请刷新页面重试');
    } finally {
        showLoading(false);
    }
}

// 异步加载所有书籍数据（带缓存）
async function loadAllBooks() {
    if (allBooksCache) {
        return allBooksCache;
    }
    // 注意：此函数现在不再负责显示加载状态，调用者需要处理
    try {
        const categories = metaData.categories;
        const fetchPromises = categories.map(category => 
            fetch(`data/books/${category}.json`).then(res => {
                if (!res.ok) {
                    console.warn(`无法加载分类: ${category}`);
                    return []; // 如果某个文件加载失败，返回空数组
                }
                return res.json();
            }).then(books => books.map(book => ({ ...book, category }))) // 将分类信息添加回书籍对象
        );

        const results = await Promise.allSettled(fetchPromises);
        
        const allBooks = results
            .filter(result => result.status === 'fulfilled')
            .flatMap(result => result.value);

        allBooksCache = allBooks;
        console.log(`所有书籍数据加载并缓存完成，共 ${allBooksCache.length} 本。`);
        return allBooksCache;

    } catch (error) {
        console.error('加载全量书籍数据时出错:', error);
        showError('搜索数据加载时出错，请稍后重试');
        return null; // 返回 null 表示出错
    }
}

// 设置事件监听器
function setupEventListeners() {
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault(); // 阻止表单的默认提交行为
            handleSearch();
        }
    });
    searchButton.addEventListener('click', handleSearch);
    
    document.addEventListener('click', function(e) {
        const categoryItem = e.target.closest('.nav-item, .category-item');
        if (categoryItem) {
            const category = categoryItem.dataset.category;
            searchByCategory(category);
        }
    });
}

// 处理搜索
function handleSearch() {
    const query = searchInput.value.trim().toLowerCase();
    
    if (!query) {
        showBrowseSection();
        return;
    }
    
    if (!metaData) {
        showError('页面尚未初始化完成，请稍候。');
        return;
    }

    // 显示加载状态，并用 setTimeout 确保 UI 能够渲染
    showLoading(true, '正在搜索中，首次搜索可能需要一点时间...');
    
    setTimeout(async () => {
        try {
            const allBooks = await loadAllBooks();
            if (allBooks === null) { // 如果加载出错
                showLoading(false);
                return;
            }

            currentResults = allBooks.filter(book => 
                book.title.toLowerCase().includes(query) || 
                book.author.toLowerCase().includes(query)
            );
            
            currentPage = 1;
            displaySearchResults(`关键词: ${searchInput.value.trim()}`);
        } catch (error) {
            console.error('搜索时发生错误:', error);
            showError('搜索时发生未知错误，请重试。');
        } finally {
            showLoading(false);
        }
    }, 10);
}

// 按分类搜索
async function searchByCategory(category) {
    showLoading(true, `正在加载分类: ${category}...`);
    try {
        const response = await fetch(`data/books/${category}.json`);
        if (!response.ok) throw new Error('分类数据加载失败');
        
        const books = await response.json();
        currentResults = books.map(book => ({ ...book, category }));
        
        currentPage = 1;
        displaySearchResults(`分类: ${category}`);

    } catch (error) {
        console.error(`加载分类 ${category} 出错:`, error);
        showError(`加载分类 "${category}" 失败`);
    } finally {
        showLoading(false);
    }
}


// 显示搜索结果
function displaySearchResults(query) {
    hideAllSections();
    resultsSection.style.display = 'block';
    
    resultsTitle.textContent = `"${query}" 的搜索结果`;
    resultsCount.textContent = `共找到 ${currentResults.length} 本书籍`;
    
    if (currentResults.length === 0) {
        resultsContainer.innerHTML = '';
        emptyState.style.display = 'block';
        pagination.innerHTML = '';
        return;
    }
    
    emptyState.style.display = 'none';
    
    const startIndex = (currentPage - 1) * resultsPerPage;
    const endIndex = startIndex + resultsPerPage;
    const pageResults = currentResults.slice(startIndex, endIndex);
    
    resultsContainer.innerHTML = pageResults.map(book => `
        <div class="book-item">
            <div class="book-info">
                <h3 class="book-title">${highlightText(book.title, searchInput.value)}</h3>
                <p class="book-author">作者: ${highlightText(book.author, searchInput.value)}</p>
                <span class="book-category">${book.category}</span>
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
function renderPagination() {
    const totalPages = Math.ceil(currentResults.length / resultsPerPage);
    if (totalPages <= 1) {
        pagination.innerHTML = '';
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
    
    pagination.innerHTML = paginationHTML;
}

// 跳转到指定页 (逻辑简化)
function goToPage(page) {
    currentPage = page;
    displaySearchResults(searchInput.value || '分类浏览');
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// 显示统计信息
function displayStats() {
    if (!metaData) return;
    document.getElementById('totalBooks').textContent = metaData.stats.totalBooks.toLocaleString();
    document.getElementById('totalCategories').textContent = metaData.stats.totalCategories;
    const lastUpdated = new Date(metaData.stats.lastUpdated);
    document.getElementById('lastUpdated').textContent = lastUpdated.toLocaleDateString('zh-CN');
}

// 显示分类网格 (移除书籍数量显示，因为需要异步加载)
function displayCategories() {
    if (!metaData) return;
    const categoryHTML = metaData.categories.map(category => `
        <div class="category-item" data-category="${category}">
            <span class="category-name">${category}</span>
        </div>
    `).join('');
    categoryGrid.innerHTML = categoryHTML;
}

// 显示热门分类导航 (移除书籍数量显示)
function displayHotCategories() {
    if (!metaData) return;
    // 简单取前10个分类作为热门
    const hotCategories = metaData.categories.slice(0, 10);
    const navHTML = hotCategories.map(category => 
        `<span class="nav-item" data-category="${category}">${category}</span>`
    ).join('');
    navItems.innerHTML = navHTML;
}

// UI状态函数 (保持不变)
function showBrowseSection() {
    hideAllSections();
    browseSection.style.display = 'block';
    statsSection.style.display = 'block';
}
function hideAllSections() {
    resultsSection.style.display = 'none';
    browseSection.style.display = 'none';
    emptyState.style.display = 'none';
    statsSection.style.display = 'none';
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
    alert(message);
}

// 导出函数供全局使用
window.goToPage = goToPage;
