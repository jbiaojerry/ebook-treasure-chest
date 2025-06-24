// 全局变量
let booksData = null;
let searchIndex = null;
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
    await loadData();
    setupEventListeners();
    displayStats();
    displayCategories();
    displayHotCategories();
});

// 加载数据
async function loadData() {
    try {
        showLoading(true);
        
        // 加载书籍数据
        const booksResponse = await fetch('data/books-index.json');
        booksData = await booksResponse.json();
        
        // 加载搜索索引
        const indexResponse = await fetch('data/search-index.json');
        const indexData = await indexResponse.json();
        searchIndex = lunr.Index.load(indexData);
        
        console.log('数据加载完成:', {
            books: booksData.books.length,
            categories: booksData.categories.length
        });
        
    } catch (error) {
        console.error('加载数据失败:', error);
        showError('数据加载失败，请刷新页面重试');
    } finally {
        showLoading(false);
    }
}

// 设置事件监听器
function setupEventListeners() {
    // 搜索输入框
    searchInput.addEventListener('input', debounce(handleSearch, 300));
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });
    
    // 搜索按钮
    searchButton.addEventListener('click', handleSearch);
    
    // 分类导航点击
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('nav-item') || e.target.classList.contains('category-item')) {
            const category = e.target.textContent.trim();
            searchByCategory(category);
        }
    });
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 处理搜索
function handleSearch() {
    const query = searchInput.value.trim();
    
    if (!query) {
        showBrowseSection();
        return;
    }
    
    if (!searchIndex || !booksData) {
        console.error('搜索数据未加载完成');
        return;
    }
    
    try {
        showLoading(true);
        
        // 执行搜索
        const searchResults = searchIndex.search(query);
        
        // 获取书籍详细信息
        currentResults = searchResults.map(result => {
            const book = booksData.books.find(b => b.id === result.ref);
            return {
                ...book,
                score: result.score
            };
        }).filter(book => book);
        
        // 显示结果
        currentPage = 1;
        displaySearchResults(query);
        
    } catch (error) {
        console.error('搜索出错:', error);
        showError('搜索出错，请重试');
    } finally {
        showLoading(false);
    }
}

// 按分类搜索
function searchByCategory(category) {
    if (!booksData) return;
    
    currentResults = booksData.books.filter(book => 
        book.category === category
    );
    
    currentPage = 1;
    displaySearchResults(`分类: ${category}`);
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
    
    // 分页显示结果
    const startIndex = (currentPage - 1) * resultsPerPage;
    const endIndex = startIndex + resultsPerPage;
    const pageResults = currentResults.slice(startIndex, endIndex);
    
    // 渲染结果
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
    
    // 渲染分页
    renderPagination();
}

// 高亮匹配文本
function highlightText(text, query) {
    if (!query) return text;
    
    const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

// 转义正则表达式特殊字符
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// 渲染分页
function renderPagination() {
    const totalPages = Math.ceil(currentResults.length / resultsPerPage);
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // 上一页
    if (currentPage > 1) {
        paginationHTML += `<button class="page-btn" onclick="goToPage(${currentPage - 1})">上一页</button>`;
    }
    
    // 页码
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) {
        paginationHTML += `<button class="page-btn" onclick="goToPage(1)">1</button>`;
        if (startPage > 2) {
            paginationHTML += `<span class="page-ellipsis">...</span>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHTML += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHTML += `<span class="page-ellipsis">...</span>`;
        }
        paginationHTML += `<button class="page-btn" onclick="goToPage(${totalPages})">${totalPages}</button>`;
    }
    
    // 下一页
    if (currentPage < totalPages) {
        paginationHTML += `<button class="page-btn" onclick="goToPage(${currentPage + 1})">下一页</button>`;
    }
    
    pagination.innerHTML = paginationHTML;
}

// 跳转到指定页
function goToPage(page) {
    currentPage = page;
    displaySearchResults(searchInput.value || '分类搜索');
    
    // 滚动到结果顶部
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// 显示统计信息
function displayStats() {
    if (!booksData) return;
    
    document.getElementById('totalBooks').textContent = booksData.stats.totalBooks.toLocaleString();
    document.getElementById('totalCategories').textContent = booksData.stats.totalCategories;
    
    const lastUpdated = new Date(booksData.stats.lastUpdated);
    document.getElementById('lastUpdated').textContent = lastUpdated.toLocaleDateString('zh-CN');
}

// 显示分类网格
function displayCategories() {
    if (!booksData) return;
    
    const categoryHTML = booksData.categories.map(category => {
        const count = booksData.books.filter(book => book.category === category).length;
        return `
            <div class="category-item" data-category="${category}">
                <span class="category-name">${category}</span>
                <span class="category-count">${count}</span>
            </div>
        `;
    }).join('');
    
    categoryGrid.innerHTML = categoryHTML;
}

// 显示热门分类导航
function displayHotCategories() {
    if (!booksData) return;
    
    // 按书籍数量排序，取前10个
    const hotCategories = booksData.categories
        .map(category => ({
            name: category,
            count: booksData.books.filter(book => book.category === category).length
        }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10);
    
    const navHTML = hotCategories.map(category => 
        `<span class="nav-item" data-category="${category.name}">${category.name}</span>`
    ).join('');
    
    navItems.innerHTML = navHTML;
}

// 显示浏览区域
function showBrowseSection() {
    hideAllSections();
    browseSection.style.display = 'block';
    statsSection.style.display = 'block';
}

// 隐藏所有主要区域
function hideAllSections() {
    resultsSection.style.display = 'none';
    browseSection.style.display = 'none';
    emptyState.style.display = 'none';
    statsSection.style.display = 'none';
}

// 显示/隐藏加载状态
function showLoading(show) {
    loading.style.display = show ? 'block' : 'none';
}

// 显示错误信息
function showError(message) {
    // 简单的错误提示，可以后续改进为更好的UI
    alert(message);
}

// 导出函数供全局使用
window.goToPage = goToPage;