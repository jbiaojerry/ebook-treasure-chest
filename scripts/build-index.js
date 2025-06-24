const fs = require('fs-extra');
const path = require('path');
const lunr = require('lunr');
const { pinyin } = require('pinyin');

// 中文分词和拼音处理
function processChinese(text) {
    if (!text) return '';
    
    // 转换为拼音
    const pinyinArray = pinyin(text, {
        style: 'normal',
        heteronym: false
    });
    
    const pinyinText = pinyinArray.map(item => item[0]).join('');
    
    return {
        original: text,
        pinyin: pinyinText,
        searchable: `${text} ${pinyinText}`
    };
}

// 解析 Markdown 表格
function parseMarkdownTable(content) {
    const books = [];
    const lines = content.split('\n');
    
    let inTable = false;
    let headerParsed = false;
    
    for (const line of lines) {
        const trimmedLine = line.trim();
        
        // 检测表格开始
        if (trimmedLine.startsWith('|') && trimmedLine.includes('书名')) {
            inTable = true;
            continue;
        }
        
        // 跳过分隔行
        if (inTable && trimmedLine.includes('---')) {
            headerParsed = true;
            continue;
        }
        
        // 解析表格数据行
        if (inTable && headerParsed && trimmedLine.startsWith('|')) {
            const cells = trimmedLine.split('|').map(cell => cell.trim()).filter(cell => cell);
            
            if (cells.length >= 3) {
                const title = extractTextFromMarkdown(cells[0]);
                const author = extractTextFromMarkdown(cells[1]);
                const downloadUrl = extractLinkFromMarkdown(cells[2]);
                
                if (title && author) {
                    books.push({
                        title,
                        author,
                        downloadUrl: downloadUrl || '',
                        titleProcessed: processChinese(title),
                        authorProcessed: processChinese(author)
                    });
                }
            }
        }
        
        // 表格结束
        if (inTable && !trimmedLine.startsWith('|')) {
            break;
        }
    }
    
    return books;
}

// 从 Markdown 文本中提取纯文本
function extractTextFromMarkdown(text) {
    if (!text) return '';
    
    // 移除链接格式 [text](url)
    text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
    
    // 移除图片格式 ![alt](url)
    text = text.replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1');
    
    // 移除其他 markdown 标记
    text = text.replace(/[*_`#]/g, '');
    
    return text.trim();
}

// 从 Markdown 中提取链接
function extractLinkFromMarkdown(text) {
    if (!text) return '';
    
    const linkMatch = text.match(/\[([^\]]+)\]\(([^)]+)\)/);
    return linkMatch ? linkMatch[2] : '';
}

// 扫描所有 md 文件
async function scanMdFiles() {
    const mdDir = path.join(__dirname, '../md');
    const files = await fs.readdir(mdDir);
    const allBooks = [];
    const categories = [];
    
    for (const file of files) {
        if (path.extname(file) === '.md') {
            const category = path.basename(file, '.md');
            const filePath = path.join(mdDir, file);
            const content = await fs.readFile(filePath, 'utf-8');
            
            const books = parseMarkdownTable(content);
            
            if (books.length > 0) {
                categories.push(category);
                
                books.forEach((book, index) => {
                    allBooks.push({
                        id: `${category}_${index}`,
                        title: book.title,
                        author: book.author,
                        category: category,
                        downloadUrl: book.downloadUrl,
                        titleProcessed: book.titleProcessed,
                        authorProcessed: book.authorProcessed
                    });
                });
            }
        }
    }
    
    return { books: allBooks, categories };
}

// 构建搜索索引
function buildSearchIndex(books) {
    const idx = lunr(function () {
        this.ref('id');
        this.field('title', { boost: 10 });
        this.field('author', { boost: 5 });
        this.field('category', { boost: 3 });
        this.field('titlePinyin');
        this.field('authorPinyin');
        
        books.forEach(book => {
            this.add({
                id: book.id,
                title: book.title,
                author: book.author,
                category: book.category,
                titlePinyin: book.titleProcessed.pinyin,
                authorPinyin: book.authorProcessed.pinyin
            });
        });
    });
    
    return idx;
}

// 主函数
async function main() {
    try {
        console.log('开始构建搜索索引...');
        
        // 扫描 md 文件
        const { books, categories } = await scanMdFiles();
        console.log(`发现 ${books.length} 本书籍，${categories.length} 个分类`);
        
        // 构建搜索索引
        const searchIndex = buildSearchIndex(books);
        
        // 准备输出数据
        const booksData = {
            books: books.map(book => ({
                id: book.id,
                title: book.title,
                author: book.author,
                category: book.category,
                downloadUrl: book.downloadUrl
            })),
            categories: categories.sort(),
            stats: {
                totalBooks: books.length,
                totalCategories: categories.length,
                lastUpdated: new Date().toISOString()
            }
        };
        
        // 确保输出目录存在
        const outputDir = path.join(__dirname, '../docs/data');
        await fs.ensureDir(outputDir);
        
        // 写入文件
        await fs.writeFile(
            path.join(outputDir, 'books-index.json'),
            JSON.stringify(booksData, null, 2)
        );
        
        await fs.writeFile(
            path.join(outputDir, 'search-index.json'),
            JSON.stringify(searchIndex)
        );
        
        console.log('搜索索引构建完成！');
        console.log(`- 书籍数据: docs/data/books-index.json`);
        console.log(`- 搜索索引: docs/data/search-index.json`);
        
    } catch (error) {
        console.error('构建索引时出错:', error);
        process.exit(1);
    }
}

// 运行主函数
if (require.main === module) {
    main();
}

module.exports = { main, scanMdFiles, buildSearchIndex };