let books = [];

async function loadBooks() {
  const res = await fetch("books.json");
  books = await res.json();
}

function searchBooks(keyword) {
  const k = keyword.toLowerCase();

  return books.filter(b =>
    b.title.toLowerCase().includes(k) ||
    (b.author || "").toLowerCase().includes(k) ||
    b.category.toLowerCase().includes(k) ||
    b.language.toLowerCase().includes(k) ||
    b.level.toLowerCase().includes(k)
  );
}

function renderResults(results) {
  const box = document.getElementById("search-results");
  box.innerHTML = "";

  if (results.length === 0) {
    box.innerHTML = "<p>❌ 没有找到相关书籍</p>";
    return;
  }

  results.forEach(b => {
    const div = document.createElement("div");
    div.innerHTML = `
      <p>
        <strong>${b.title}</strong> — ${b.author || ""}<br/>
        📂 ${b.category} ｜ 🌍 ${b.language} ｜ ⭐ ${b.level}<br/>
        <a href="${b.link}" target="_blank">下载</a>
      </p>
      <hr/>
    `;
    box.appendChild(div);
  });
}

async function onSearch(e) {
  const keyword = e.target.value.trim();
  if (!keyword) {
    document.getElementById("search-results").innerHTML = "";
    return;
  }
  const results = searchBooks(keyword);
  renderResults(results);
}

loadBooks();
