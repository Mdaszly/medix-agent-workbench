from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List

from app.core.config import SETTINGS
from app.schemas.chat import Evidence


# ==================== Java 类比说明 ====================
# 这个类类似于 Spring Boot 中的搜索引擎服务（如 Elasticsearch Service）
# 作用：本地知识库检索，使用 TF-IDF 算法计算相似度
# 等价于：@Component public class RAGService { private List<Document> documents; }
# ================================================

def tokenize(text: str) -> List[str]:
    """
    文本分词（类似 IKAnalyzer 或 HanLP 的分词器）
    
    Java 等价：
    public List<String> tokenize(String text) {
        // 提取中文词汇（1-2个字）
        List<String> chinese = extractChineseWords(text);
        // 提取英文和数字
        List<String> latin = extractLatinWords(text);
        return concat(chinese, latin);
    }
    """
    # 提取中文字符（1-2个字的组合）
    # Java: Pattern.compile("[\\u4e00-\\u9fff]{1,2}").matcher(text).results()
    chinese = re.findall(r"[\u4e00-\u9fff]{1,2}", text)
    
    # 提取英文和数字
    # Java: Pattern.compile("[A-Za-z0-9]+").matcher(text.toLowerCase()).results()
    latin = re.findall(r"[A-Za-z0-9]+", text.lower())
    
    return chinese + latin


class RAGService:
    """
    RAG 检索服务（类似 Elasticsearch Service 或 Lucene Service）
    
    Java 等价代码：
    @Component
    public class RAGService {
        @Value("${rag.knowledge-dir}")
        private String knowledgeDir;
        
        @Value("${rag.top-k:5}")
        private int topK;
        
        private List<Document> documents;
        
        @PostConstruct
        public void init() {
            this.documents = loadDocuments();
        }
        
        public List<Evidence> search(String query, Integer topK) {
            // 使用余弦相似度计算相关性
            return calculateCosineSimilarity(query, documents)
                .sorted(Comparator.comparingDouble(Evidence::getScore).reversed())
                .limit(topK != null ? topK : this.topK)
                .collect(Collectors.toList());
        }
    }
    """
    
    def __init__(self):
        # 加载配置（类似 @Value("${rag.knowledge-dir}")）
        # Java: @Value("${rag.knowledge-dir}") private String knowledgeDir;
        self.knowledge_dir = Path(SETTINGS["rag"]["knowledge_dir"])
        
        # 设置返回结果数量（类似 @Value("${rag.top-k:5}")）
        # Java: @Value("${rag.top-k:5}") private int topK;
        self.top_k = int(SETTINGS["rag"].get("top_k", 5))
        
        # 初始化时加载文档（类似 @PostConstruct）
        # Java: @PostConstruct public void init() { this.documents = loadDocs(); }
        self.documents = self._load_docs()

    def _load_docs(self) -> List[Dict]:
        """
        加载知识库文档（类似从文件系统或数据库加载索引）
        
        Java 等价：
        private List<Document> loadDocuments() {
            List<Document> docs = new ArrayList<>();
            Path knowledgeDir = Paths.get(config.getKnowledgeDir());
            
            if (!Files.exists(knowledgeDir)) {
                return docs;
            }
            
            // 遍历所有 Markdown 文件
            try (Stream<Path> paths = Files.walk(knowledgeDir)) {
                paths.filter(p -> p.toString().endsWith(".md"))
                     .forEach(path -> {
                         String content = Files.readString(path);
                         List<String> chunks = splitIntoChunks(content);
                         for (int i = 0; i < chunks.size(); i++) {
                             docs.add(new Document(path.getFileName(), chunks.get(i), i));
                         }
                     });
            }
            return docs;
        }
        """
        docs = []
        if not self.knowledge_dir.exists():
            return docs
        
        # 遍历所有 .md 文件（类似 Files.walk().filter(p -> p.endsWith(".md"))）
        # Java: Files.list(knowledgeDir).filter(p -> p.toString().endsWith(".md"))
        for path in self.knowledge_dir.glob("*.md"):
            text = path.read_text(encoding="utf-8")
            
            # 提取标题（第一行去掉 # 号）
            # Java: String title = lines.get(0).replace("#", "").trim();
            title = text.splitlines()[0].replace("#", "").strip() if text.splitlines() else path.stem
            
            # 按二级/三级标题分割成块（类似文本分块策略）
            # Java: List<String> chunks = Arrays.asList(text.split("\\n#{2,3}\\s+"));
            chunks = [chunk.strip() for chunk in re.split(r"\n#{2,3}\s+", text) if chunk.strip()]
            
            for idx, chunk in enumerate(chunks):
                docs.append(
                    {
                        "source": path.name,
                        "title": title,
                        "chunk_id": idx,
                        "content": chunk[:1600],  # 限制长度
                        "tokens": Counter(tokenize(chunk)),  # 预计算词频（类似建立倒排索引）
                    }
                )
        return docs

    def search(self, query: str, top_k: int | None = None) -> List[Evidence]:
        """
        搜索相关文档（使用余弦相似度算法）
        
        Java 等价：
        public List<Evidence> search(String query, Integer topK) {
            Map<String, Integer> queryTokens = tokenize(query);
            double queryNorm = calculateNorm(queryTokens);
            
            return documents.stream()
                .map(doc -> {
                    double dotProduct = calculateDotProduct(queryTokens, doc.getTokens());
                    double docNorm = calculateNorm(doc.getTokens());
                    double score = dotProduct / (queryNorm * docNorm);
                    return new Evidence(doc.getSource(), doc.getTitle(), score, doc.getContent());
                })
                .filter(e -> e.getScore() > 0)
                .sorted(Comparator.comparingDouble(Evidence::getScore).reversed())
                .limit(topK != null ? topK : this.topK)
                .collect(Collectors.toList());
        }
        """
        # 对查询进行分词并统计词频（类似构建查询向量）
        # Java: Map<String, Integer> queryTokens = tokenize(query);
        q = Counter(tokenize(query))
        if not q:
            return []
        
        results = []
        
        # 计算查询向量的范数（用于余弦相似度）
        # Java: double queryNorm = Math.sqrt(queryTokens.values().stream().mapToDouble(v -> v*v).sum());
        q_norm = math.sqrt(sum(v * v for v in q.values()))
        
        # 遍历所有文档，计算余弦相似度
        # Java: for (Document doc : documents) { ... }
        for doc in self.documents:
            # 计算点积（分子）
            # Java: double dot = queryTokens.entrySet().stream()
            #          .mapToDouble(e -> e.getValue() * doc.getTokens().getOrDefault(e.getKey(), 0))
            #          .sum();
            dot = sum(q[t] * doc["tokens"].get(t, 0) for t in q)
            
            # 计算文档向量的范数（分母）
            # Java: double docNorm = Math.sqrt(doc.getTokens().values().stream().mapToDouble(v -> v*v).sum());
            d_norm = math.sqrt(sum(v * v for v in doc["tokens"].values())) or 1
            
            # 计算余弦相似度：cos(θ) = A·B / (||A|| * ||B||)
            # Java: double score = dot / (queryNorm * docNorm);
            score = dot / (q_norm * d_norm or 1)
            
            if score > 0:
                results.append(
                    Evidence(
                        source=doc["source"],
                        title=doc["title"],
                        score=round(float(score), 4),
                        content=doc["content"],
                    )
                )
        
        # 按分数降序排序（类似 sorted(Comparator.comparingDouble(Evidence::getScore).reversed())）
        # Java: results.sort(Comparator.comparingDouble(Evidence::getScore).reversed());
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 返回 Top-K 结果（类似 stream().limit(topK).collect(toList())）
        # Java: return results.subList(0, Math.min(topK != null ? topK : this.topK, results.size()));
        return results[: top_k or self.top_k]
