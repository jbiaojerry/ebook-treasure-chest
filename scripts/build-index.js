const fs = require('fs-extra');
const path = require('path');
const { pinyin } = require('pinyin');

// (Helper functions remain the same)
// ...

// 解析 Markdown 表格
function parseMarkdownTable(content) {
    const books = [];
    const lines = content.split('\n');
    
    let inTable = false;
    let headerParsed = false;
    
    for (const line of lines) {
        const trimmedLine = line.trim();
        
        if (trimmedLine.startsWith('|') && trimmedLine.includes('书名')) {
            inTable = true;
            continue;
        }
        
        if (inTable && trimmedLine.includes('---')) {
            headerParsed = true;
            continue;
        }
        
        if (inTable && headerParsed && trimmedLine.startsWith('|')) {
            const cells = trimmedLine.split('|').map(cell => cell.trim()).filter(cell => cell);
            
            if (cells.length >= 3) {
                const title = extractTextFromMarkdown(cells[0]);
                //  去掉title中的 “(点击查看图片)”
                title = title.replace(/\(点击查看图片\)/g, '');
                const author = extractTextFromMarkdown(cells[1]);
                const downloadUrl = extractLinkFromMarkdown(cells[2]);
                
                if (title && author) {
                    books.push({
                        title,
                        author,
                        downloadUrl: downloadUrl || ''
                    });
                }
            }
        }
        
        if (inTable && !trimmedLine.startsWith('|')) {
            break;
        }
    }
    
    return books;
}

// 从 Markdown 文本中提取纯文本
function extractTextFromMarkdown(text) {
    if (!text) return '';
    text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
    text = text.replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1');
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
    const booksByCategory = {};
    
    for (const file of files) {
        if (path.extname(file) === '.md') {
            const category = path.basename(file, '.md');
            const filePath = path.join(mdDir, file);
            const content = await fs.readFile(filePath, 'utf-8');
            const books = parseMarkdownTable(content);
            
            if (books.length > 0) {
                if (!booksByCategory[category]) {
                    booksByCategory[category] = [];
                }
                booksByCategory[category].push(...books);
            }
        }
    }
    
    return booksByCategory;
}

// 主函数
async function main() {
    try {
        console.log('开始构建拆分后的优化数据文件...');
        
        // 扫描并按分类组织书籍
        const booksByCategory = await scanMdFiles();
        const categories = Object.keys(booksByCategory);
        const totalBooks = Object.values(booksByCategory).reduce((sum, books) => sum + books.length, 0);
        
        console.log(`发现 ${totalBooks} 本书籍，${categories.length} 个分类`);
        
        // 定义并清理输出目录
        const outputDir = path.join(__dirname, '../docs/data');
        const booksDir = path.join(outputDir, 'books');
        await fs.emptyDir(outputDir);
        await fs.ensureDir(booksDir);
        
        // 按分类写入拆分后的书籍数据文件
        for (const category of categories) {
            const categoryData = booksByCategory[category] || [];
            const categoryFilePath = path.join(booksDir, `${category}.json`);
            await fs.writeFile(categoryFilePath, JSON.stringify(categoryData)); // Use compact JSON
        }
        console.log(`已将书籍数据拆分到 ${categories.length} 个 JSON 文件中 (位于 docs/data/books/)`);
        
        // 创建轻量级的元数据文件
        const metaData = {
            categories: categories.sort(),
            stats: {
                totalBooks,
                totalCategories: categories.length,
                lastUpdated: new Date().toISOString()
            }
        };
        const metaFilePath = path.join(outputDir, 'meta.json');
        await fs.writeFile(metaFilePath, JSON.stringify(metaData));
        console.log('已生成元数据文件: docs/data/meta.json');
        
        console.log('优化的数据文件构建完成！');
        
    } catch (error) {
        console.error('构建优化数据时出错:', error);
        process.exit(1);
    }
}

// 运行主函数
if (require.main === module) {
    main();
}

module.exports = { main, scanMdFiles };
