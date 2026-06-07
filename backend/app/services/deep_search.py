from __future__ import annotations

import asyncio
import re
from html import unescape
from urllib.parse import quote_plus
from typing import List

import httpx

from app.schemas.chat import Evidence


# ==================== Java 类比说明 ====================
# 这个文件类似于 Spring Boot 中的外部搜索服务（如 WebSearchService）
# 作用：联网搜索医学资料，提供降级策略
# 等价于：@Component public class DeepSearchService { private final RestTemplate restTemplate; }
# ================================================

def _search_sync(query: str, limit: int) -> List[Evidence]:
    """
    同步搜索方法（使用 DuckDuckGo API）
    
    Java 等价：
    private List<Evidence> searchSync(String query, int limit) {
        DDGS ddgs = new DDGS();
        List<Evidence> results = new ArrayList<>();
        
        for (SearchResult item : ddgs.text(query + " 医学 指南 健康 科普", limit)) {
            results.add(new Evidence(
                item.getHref(),
                item.getTitle(),
                0.5,
                item.getBody()
            ));
        }
        
        return results;
    }
    """
    from duckduckgo_search import DDGS

    rows = []
    with DDGS() as ddgs:
        # 调用 DuckDuckGo 搜索 API（类似 restTemplate.getForObject(url, SearchResult.class)）
        # Java: List<SearchResult> items = ddgsClient.search(query + " 医学 指南", limit);
        for item in ddgs.text(query + " 医学 指南 健康 科普", max_results=limit):
            rows.append(
                Evidence(
                    source=item.get("href", "web"),
                    title=item.get("title", "联网资料"),
                    score=0.5,
                    content=item.get("body", ""),
                )
            )
    return rows


async def web_search(query: str, limit: int = 2, timeout: float = 8.0) -> List[Evidence]:
    """
    异步网络搜索（带降级策略）
    
    Java 等价：
    @Component
    public class DeepSearchService {
        
        @Async
        public CompletableFuture<List<Evidence>> webSearch(String query, int limit, double timeout) {
            try {
                // 主搜索策略：使用 DuckDuckGo SDK
                return CompletableFuture.supplyAsync(() -> searchSync(query, limit))
                    .orTimeout((long) (timeout * 1000), TimeUnit.MILLISECONDS);
            } catch (Exception e) {
                try {
                    // 降级策略1：HTML 解析
                    return searchDuckDuckGoHtml(query, limit, timeout);
                } catch (Exception ex) {
                    // 降级策略2：返回默认提示
                    return CompletableFuture.completedFuture(Arrays.asList(
                        new Evidence("web-search-fallback", "联网搜索自动降级", 0.0, 
                            "当前环境未成功获取联网资料...")
                    ));
                }
            }
        }
    }
    """
    try:
        # 主搜索策略：使用 DuckDuckGo SDK（在单独线程中执行以避免阻塞）
        # Java: return CompletableFuture.supplyAsync(() -> searchSync(query, limit))
        return await asyncio.wait_for(asyncio.to_thread(_search_sync, query, limit), timeout=timeout)
    except Exception:
        try:
            # 降级策略1：尝试 HTML 解析方式
            # Java: return searchDuckDuckGoHtml(query, limit, timeout);
            return await _search_duckduckgo_html(query, limit=limit, timeout=timeout)
        except Exception:
            # 降级策略2：返回默认提示信息
            # Java: return Collections.singletonList(new Evidence(...));
            return [
                Evidence(
                    source="web-search-fallback",
                    title="联网搜索自动降级",
                    score=0.0,
                    content="当前环境未成功获取联网资料，系统将基于本地医学知识库和安全规则回答。",
                )
            ]


async def _search_duckduckgo_html(query: str, limit: int = 2, timeout: float = 6.0) -> List[Evidence]:
    """
    通过 HTML 解析方式搜索（降级策略）
    
    Java 等价：
    private CompletableFuture<List<Evidence>> searchDuckDuckGoHtml(String query, int limit, double timeout) {
        String url = "https://duckduckgo.com/html/?q=" + URLEncoder.encode(query + " 医学 指南", StandardCharsets.UTF_8);
        
        HttpHeaders headers = new HttpHeaders();
        headers.set("User-Agent", "Mozilla/5.0");
        
        ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, 
            new HttpEntity<>(headers), String.class);
        
        String html = response.getBody();
        Pattern pattern = Pattern.compile("<a rel=\"nofollow\" class=\"result__a\"...", Pattern.DOTALL);
        Matcher matcher = pattern.matcher(html);
        
        List<Evidence> results = new ArrayList<>();
        while (matcher.find() && results.size() < limit) {
            String title = Jsoup.parse(matcher.group("title")).text();
            String body = Jsoup.parse(matcher.group("body")).text();
            String href = matcher.group("href");
            
            if (!title.isEmpty() && !body.isEmpty()) {
                results.add(new Evidence(href, title, 0.45, body));
            }
        }
        
        if (results.isEmpty()) {
            throw new RuntimeException("no web result parsed");
        }
        
        return CompletableFuture.completedFuture(results);
    }
    """
    # 构建搜索 URL（类似 URLEncoder.encode(query, "UTF-8")）
    # Java: String url = "https://duckduckgo.com/html/?q=" + URLEncoder.encode(query, "UTF-8");
    url = "https://duckduckgo.com/html/?q=" + quote_plus(query + " 医学 指南 健康 科普")
    
    # 发送 HTTP GET 请求（类似 restTemplate.getForEntity(url, String.class)）
    # Java: ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()  # 检查响应状态码（类似 response.getStatusCode().is2xxSuccessful()）
    
    html = resp.text
    
    # 使用正则表达式解析 HTML（类似 Jsoup 或 HTML Parser）
    # Java: Pattern pattern = Pattern.compile("<a rel=\"nofollow\" class=\"result__a\"...", Pattern.DOTALL);
    pattern = re.compile(r'<a rel="nofollow" class="result__a" href="(?P<href>.*?)".*?>(?P<title>.*?)</a>.*?<a class="result__snippet".*?>(?P<body>.*?)</a>', re.S)
    rows = []
    
    # 遍历匹配结果（类似 while (matcher.find()) { ... }）
    for match in pattern.finditer(html):
        # 提取标题并去除 HTML 标签（类似 Jsoup.parse(title).text()）
        # Java: String title = Jsoup.parse(matcher.group("title")).text();
        title = re.sub("<.*?>", "", unescape(match.group("title"))).strip()
        
        # 提取摘要并去除 HTML 标签
        # Java: String body = Jsoup.parse(matcher.group("body")).text();
        body = re.sub("<.*?>", "", unescape(match.group("body"))).strip()
        
        # 提取链接
        href = unescape(match.group("href")).strip()
        
        if title and body:
            rows.append(Evidence(source=href, title=title, score=0.45, content=body))
        
        # 达到限制数量则停止
        # Java: if (results.size() >= limit) break;
        if len(rows) >= limit:
            break
    
    if not rows:
        raise RuntimeError("no web result parsed")
    
    return rows
