let books = [];
let searchTimeout = null;
const MAX_RESULTS = 100; // 最多显示100条结果

async function loadBooks() {
  try {
    // 优先加载 all-books.json（包含所有 md 文件的数据）
    const res = await fetch("all-books.json");
    if (res.ok) {
      books = await res.json();
      console.log(`✅ 已加载 ${books.length} 本书籍`);
      return;
    }
  } catch (e) {
    console.warn("⚠️  all-books.json 加载失败，尝试加载 books.json");
  }
  
  // 降级到 books.json（metadata 数据）
  try {
    const res = await fetch("books.json");
    books = await res.json();
    console.log(`✅ 已加载 ${books.length} 本书籍（metadata）`);
  } catch (e) {
    console.error("❌ 无法加载书籍数据", e);
  }
}

function searchBooks(keyword) {
  if (!keyword || keyword.trim() === "") {
    return [];
  }
  
  const k = keyword.toLowerCase().trim();
  const keywords = k.split(/\s+/); // 支持多关键词搜索

  return books.filter(b => {
    const title = (b.title || "").toLowerCase();
    const author = (b.author || "").toLowerCase();
    const category = (b.category || "").toLowerCase();
    
    // 多关键词匹配：所有关键词都要匹配
    return keywords.every(keyword => 
      title.includes(keyword) ||
      author.includes(keyword) ||
      category.includes(keyword)
    );
  }).slice(0, MAX_RESULTS); // 限制结果数量
}

function highlightText(text, keyword) {
  if (!keyword) return text;
  const regex = new RegExp(`(${keyword})`, 'gi');
  return text.replace(regex, '<mark>$1</mark>');
}

function renderResults(results, keyword) {
  const box = document.getElementById("search-results");
  box.innerHTML = "";

  if (results.length === 0) {
    box.innerHTML = "<p style='padding: 20px; text-align: center; color: #666;'>❌ 没有找到相关书籍</p>";
    return;
  }

  const keywordLower = keyword.toLowerCase();
  
  // 显示结果数量
  const countDiv = document.createElement("div");
  countDiv.style.cssText = "padding: 10px; background: #f6f8fa; border-radius: 4px; margin-bottom: 10px;";
  countDiv.innerHTML = `<strong>找到 ${results.length}${results.length === MAX_RESULTS ? '+' : ''} 条结果</strong>`;
  box.appendChild(countDiv);

  results.forEach(b => {
    const div = document.createElement("div");
    div.style.cssText = "padding: 15px; margin: 10px 0; background: #fff; border: 1px solid #e1e4e8; border-radius: 6px;";
    
    const highlightedTitle = highlightText(b.title || "未知", keywordLower);
    const highlightedAuthor = highlightText(b.author || "未知", keywordLower);
    const highlightedCategory = highlightText(b.category || "", keywordLower);
    
    div.innerHTML = `
      <div style="margin-bottom: 8px;">
        <strong style="font-size: 16px; color: #0366d6;">${highlightedTitle}</strong>
      </div>
      <div style="color: #586069; font-size: 14px; margin-bottom: 8px;">
        <span>👤 ${highlightedAuthor}</span>
        <span style="margin: 0 10px;">|</span>
        <span>📂 ${highlightedCategory}</span>
      </div>
      <div>
        <a href="${b.link}" target="_blank" style="
          display: inline-block;
          padding: 6px 12px;
          background: #0366d6;
          color: white;
          text-decoration: none;
          border-radius: 4px;
          font-size: 14px;
        ">📥 下载</a>
      </div>
    `;
    box.appendChild(div);
  });
  
  // 添加样式
  if (!document.getElementById('search-results-style')) {
    const style = document.createElement('style');
    style.id = 'search-results-style';
    style.textContent = `
      mark {
        background: #ffeb3b;
        padding: 2px 4px;
        border-radius: 2px;
      }
    `;
    document.head.appendChild(style);
  }
}

function onSearch(e) {
  const keyword = e.target.value.trim();
  
  // 清除之前的定时器
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }
  
  // 如果输入为空，清空结果
  if (!keyword) {
    document.getElementById("search-results").innerHTML = "";
    return;
  }
  
  // 防抖：300ms 后执行搜索
  searchTimeout = setTimeout(() => {
    const results = searchBooks(keyword);
    renderResults(results, keyword);
  }, 300);
}

// 页面加载完成后加载数据
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', loadBooks);
} else {
  loadBooks();
}
