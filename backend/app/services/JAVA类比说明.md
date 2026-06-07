# Services 层 Java 类比说明文档

## 概述
本文档详细说明了 FastAPI 项目 services 层代码与 Java Spring Boot 的对应关系，帮助 Java 开发者快速理解 Python 代码。

---

## 1. agent_orchestrator.py - 编排器

### Java 类比：Facade Pattern / Workflow Engine

```python
class MedicalAgentOrchestrator:
    def __init__(self):
        self.service = ConsultationService()  # 类似 @Autowired
    
    async def handle(self, req: ChatRequest) -> ChatResponse:
        return await self.service.chat(req, scene="consultation")
```

**等价 Java 代码：**
```java
@Component
public class MedicalAgentOrchestrator {
    @Autowired
    private ConsultationService consultationService;
    
    public CompletableFuture<ChatResponse> handle(ChatRequest request) {
        return consultationService.chat(request, "consultation");
    }
}
```

**设计模式：**
- Facade（外观模式）：统一入口，简化调用
- Dependency Injection（依赖注入）：通过构造函数注入服务

---

## 2. llm_client.py - LLM 客户端

### Java 类比：RestTemplate / WebClient + Spring Retry

```python
class LLMClient:
    def __init__(self):
        self.config = SETTINGS["llm"]  # 类似 @Value
        self.enabled = bool(...)  # 类似 @ConditionalOnProperty
        self.client = AsyncOpenAI(...)  # 类似 RestTemplate
    
    async def chat(self, messages, timeout):
        # 重试循环（类似 @Retryable）
        for attempt in range(max_retries):
            try:
                return await self._chat_once(messages, timeout)
            except Exception:
                await asyncio.sleep(0.8 + attempt * 0.8)  # 指数退避
```

**等价 Java 代码：**
```java
@Component
public class LLMClient {
    @Value("${llm.api-key}")
    private String apiKey;
    
    @Value("${llm.base-url}")
    private String baseUrl;
    
    private final RestTemplate restTemplate = new RestTemplate();
    
    @Retryable(value = Exception.class, maxAttempts = 3, backoff = @Backoff(delay = 800))
    public CompletableFuture<String> chat(List<Map<String, String>> messages, double timeout) {
        return _chatOnce(messages, timeout);
    }
    
    private String _chatOnce(List<Map<String, String>> messages, double timeout) {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(apiKey);
        
        HttpEntity<Map<String, Object>> request = new HttpEntity<>(buildPayload(messages), headers);
        ResponseEntity<Map> response = restTemplate.postForEntity(baseUrl + "/chat/completions", request, Map.class);
        
        return response.getBody().get("choices").get(0).get("message").get("content");
    }
}
```

**关键特性：**
- 重试机制：类似 Spring Retry 或 Resilience4j
- 超时控制：类似 `@Timeout` 或 `CompletableFuture.orTimeout()`
- 降级策略：SDK → HTTP API

---

## 3. rag_service.py - RAG 检索服务

### Java 类比：Elasticsearch Service / Lucene Service

```python
class RAGService:
    def __init__(self):
        self.knowledge_dir = Path(SETTINGS["rag"]["knowledge_dir"])  # @Value
        self.top_k = int(SETTINGS["rag"].get("top_k", 5))
        self.documents = self._load_docs()  # @PostConstruct
    
    def search(self, query, top_k):
        # 余弦相似度计算
        q = Counter(tokenize(query))
        for doc in self.documents:
            score = cosine_similarity(q, doc["tokens"])
        return sorted_results[:top_k]
```

**等价 Java 代码：**
```java
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
    
    private List<Document> loadDocuments() {
        // 从文件系统加载 Markdown 文件并分块
        return Files.list(Paths.get(knowledgeDir))
            .filter(p -> p.toString().endsWith(".md"))
            .flatMap(this::splitIntoChunks)
            .collect(Collectors.toList());
    }
}
```

**算法说明：**
- 文本分词：类似 IKAnalyzer 或 HanLP
- 余弦相似度：cos(θ) = A·B / (||A|| * ||B||)
- Top-K 排序：类似 Elasticsearch 的相关性评分

---

## 4. skills.py - 技能工具类

### Java 类比：Utils / Rule Engine / AOP Interceptor

```python
# 常量定义
HIGH_RISK_KEYWORDS = ["胸痛", "呼吸困难", ...]  # 类似 public static final List

def analyze_symptoms(question):
    # 症状分类（类似规则引擎）
    if "胸痛" in question:
        body_system = "心血管系统"
    elif "咳嗽" in question:
        body_system = "呼吸系统"
    return {"symptoms": symptoms, "body_system": body_system}

def assess_risk(question):
    # 风险评估（类似规则引擎）
    if any(word in question for word in HIGH_RISK_KEYWORDS):
        return {"risk_level": "高风险", ...}
    return {"risk_level": "低风险", ...}

def compliance_guard(answer):
    # 合规检查（类似 AOP After Advice）
    answer = answer.replace("确诊为", "需要由医生评估是否为")
    answer += "\n\n免责声明..."
    return answer
```

**等价 Java 代码：**
```java
@Component
public class MedicalSkills {
    public static final List<String> HIGH_RISK_KEYWORDS = Arrays.asList(
        "胸痛", "呼吸困难", "意识不清", "抽搐", "便血", "咯血"
    );
    
    // 症状分析（类似规则引擎）
    public Map<String, Object> analyzeSymptoms(String question) {
        List<String> symptoms = HIGH_RISK_KEYWORDS.stream()
            .filter(question::contains)
            .collect(Collectors.toList());
        
        String bodySystem = classifyBodySystem(question);
        return Map.of("symptoms", symptoms, "body_system", bodySystem);
    }
    
    // 风险评估
    public Map<String, String> assessRisk(String question) {
        if (HIGH_RISK_KEYWORDS.stream().anyMatch(question::contains)) {
            return Map.of("risk_level", "高风险", "advice", "建议立即线下就医");
        }
        return Map.of("risk_level", "低风险", "advice", "可先进行健康观察");
    }
    
    // 合规检查（类似 AOP）
    public String complianceGuard(String answer) {
        answer = answer.replace("确诊为", "需要由医生评估是否为");
        answer = answer.replace("一定是", "可能为");
        
        if (!answer.contains("免责声明")) {
            answer += "\n\n以上内容仅用于健康科普...";
        }
        return answer;
    }
}
```

**设计模式：**
- 规则引擎：基于关键词的模式匹配
- AOP（面向切面编程）：合规检查作为横切关注点
- 策略模式：不同症状对应不同建议

---

## 5. deep_search.py - 深度搜索服务

### Java 类比：WebSearchService + Circuit Breaker

```python
async def web_search(query, limit=2, timeout=8.0):
    try:
        # 主策略：DuckDuckGo SDK
        return await asyncio.to_thread(_search_sync, query, limit)
    except Exception:
        try:
            # 降级策略1：HTML 解析
            return await _search_duckduckgo_html(query, limit, timeout)
        except Exception:
            # 降级策略2：返回默认提示
            return [Evidence("fallback", "联网搜索自动降级", 0.0, "...")]
```

**等价 Java 代码：**
```java
@Component
public class DeepSearchService {
    
    @Async
    public CompletableFuture<List<Evidence>> webSearch(String query, int limit, double timeout) {
        try {
            // 主策略：使用 DuckDuckGo SDK
            return CompletableFuture.supplyAsync(() -> searchSync(query, limit))
                .orTimeout((long) (timeout * 1000), TimeUnit.MILLISECONDS);
        } catch (Exception e) {
            try {
                // 降级策略1：HTML 解析
                return searchDuckDuckGoHtml(query, limit, timeout);
            } catch (Exception ex) {
                // 降级策略2：返回默认提示
                return CompletableFuture.completedFuture(Collections.singletonList(
                    new Evidence("web-search-fallback", "联网搜索自动降级", 0.0, 
                        "当前环境未成功获取联网资料...")
                ));
            }
        }
    }
    
    private List<Evidence> searchSync(String query, int limit) {
        DDGS ddgs = new DDGS();
        return ddgs.text(query + " 医学 指南", limit).stream()
            .map(item -> new Evidence(item.getHref(), item.getTitle(), 0.5, item.getBody()))
            .collect(Collectors.toList());
    }
    
    private CompletableFuture<List<Evidence>> searchDuckDuckGoHtml(String query, int limit, double timeout) {
        String url = "https://duckduckgo.com/html/?q=" + URLEncoder.encode(query, StandardCharsets.UTF_8);
        
        HttpHeaders headers = new HttpHeaders();
        headers.set("User-Agent", "Mozilla/5.0");
        
        ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, 
            new HttpEntity<>(headers), String.class);
        
        // 使用 Jsoup 解析 HTML
        Document doc = Jsoup.parse(response.getBody());
        return doc.select(".result__a").stream()
            .limit(limit)
            .map(element -> new Evidence(element.attr("href"), element.text(), 0.45, 
                element.siblingElements().text()))
            .collect(Collectors.toList());
    }
}
```

**关键特性：**
- 多重降级策略：SDK → HTML 解析 → 默认提示
- 异步执行：类似 `@Async` + `CompletableFuture`
- 超时控制：类似 `orTimeout()`

---

## 6. medical_business.py - 核心业务逻辑

### Java 类比：@Service + Workflow Engine + Strategy Pattern

这是最核心的文件，包含两个主要类：

### 6.1 MedicalSwarm - AI 编排引擎

```python
class MedicalSwarm:
    def __init__(self):
        self.rag = RAGService()  # @Autowired
        self.llm = LLMClient()   # @Autowired
    
    async def run(self, scene, message, patient, history):
        # 1. 路由识别
        step("RouterAgent", "route", "...")
        
        # 2. 症状分析（本地规则引擎）
        symptom_profile = analyze_symptoms(message)
        risk_hint = assess_risk(message)
        
        # 3. 并行检索（RAG + Web Search）
        local_task = asyncio.to_thread(self.rag.search, query, 6)
        web_task = web_search(query, limit=3, timeout=6.0)
        local_evidence, web_evidence = await asyncio.gather(local_task, web_task)
        
        # 4. LLM 推理（带多重降级策略）
        structured = await self._reason_with_llm(...)
        
        # 5. Fallback 处理
        if not structured:
            structured = fallback_structured(...)
        
        # 6. 结果规范化
        department = normalize_department(structured.get("recommended_department"), scene)
        risk_level = normalize_risk(structured.get("risk_level"))
        answer = render_answer(scene, structured, department, risk_level)
        
        # 7. 合规检查（AOP）
        answer = compliance_guard(answer)
        
        return SwarmResult(answer, risk_level, department, ...)
```

**等价 Java 代码：**
```java
@Component
public class MedicalSwarm {
    @Autowired
    private RAGService ragService;
    
    @Autowired
    private LLMClient llmClient;
    
    @Autowired
    private MedicalSkills skillsService;
    
    @Async
    public CompletableFuture<SwarmResult> run(String scene, String message, 
                                               Map<String, Object> patient,
                                               List<Map<String, Object>> history) {
        List<String> thinkingSteps = new ArrayList<>();
        List<AgentTrace> trace = new ArrayList<>();
        
        // 1. 路由识别
        step("RouterAgent", "route", "识别业务场景为 " + SCENE_NAMES.get(scene));
        
        // 2. 症状分析
        Map<String, Object> symptomProfile = skillsService.analyzeSymptoms(message);
        Map<String, Object> riskHint = skillsService.assessRisk(message);
        List<String> suggestions = skillsService.lifestyleRecommendations(message);
        
        // 3. 并行检索
        String query = buildSearchQuery(scene, message, patient, history);
        CompletableFuture<List<Evidence>> localFuture = 
            CompletableFuture.supplyAsync(() -> ragService.search(query, 6));
        CompletableFuture<List<Evidence>> webFuture = 
            deepSearchService.webSearch(query, 3, 6.0);
        
        List<Evidence> allEvidence = CompletableFuture.allOf(localFuture, webFuture)
            .thenApply(v -> Stream.concat(localFuture.join().stream(), 
                                          webFuture.join().stream())
                                  .collect(Collectors.toList()));
        
        // 4. LLM 推理
        Map<String, Object> structured = reasonWithLLM(scene, message, patient, 
            history, symptomProfile, riskHint, allEvidence, suggestions).join();
        
        // 5. Fallback
        if (structured == null) {
            structured = fallbackStrategy.execute(scene, message, riskHint, suggestions);
        }
        
        // 6. 结果规范化
        String department = normalizeDepartment(structured.get("recommended_department"), scene);
        String riskLevel = normalizeRisk(structured.get("risk_level"));
        String answer = renderAnswer(scene, structured, department, riskLevel);
        
        // 7. 合规检查（AOP）
        answer = complianceGuard(answer);
        
        // 8. 构建指标
        Map<String, Object> metrics = buildMetrics(trace, allEvidence);
        
        return CompletableFuture.completedFuture(new SwarmResult(
            answer, riskLevel, department, suggestions, thinkingSteps, 
            allEvidence.subList(0, 8), trace, metrics
        ));
    }
    
    // LLM 推理（带多重降级策略）
    private CompletableFuture<Map<String, Object>> reasonWithLLM(...) {
        // 尝试1: JSON 格式输出
        String raw = llmClient.chat(buildPrompt(...)).join();
        Map<String, Object> structured = parseJsonObject(raw);
        if (structured != null) return CompletableFuture.completedFuture(structured);
        
        // 尝试2: 自然语言解析
        Map<String, Object> narrative = parseNarrativeAnswer(raw);
        if (narrative != null) return CompletableFuture.completedFuture(narrative);
        
        // 尝试3: JSON 修复
        Map<String, Object> repaired = repairJson(raw).join();
        if (repaired != null) return CompletableFuture.completedFuture(repaired);
        
        // 尝试4: 紧凑 Prompt
        return compactReason(...);
    }
}
```

### 6.2 ConsultationService - 问诊服务

```python
class ConsultationService:
    def __init__(self):
        self.swarm = MedicalSwarm()
    
    async def chat(self, req: ChatRequest, scene="consultation"):
        # 1. 会话管理
        session_id = req.session_id or str(uuid.uuid4())
        upsert_session(session_id, req.message[:30])
        
        # 2. 保存用户消息
        add_message(session_id, "user", req.message, {...})
        
        # 3. 获取历史对话
        history = list_messages(session_id, limit=12)
        
        # 4. 调用 AI 引擎
        result = await self.swarm.run(scene, req.message, 
                                      req.patient_context.model_dump(), history)
        
        # 5. 保存 AI 回复
        add_message(session_id, "assistant", result.answer, {...})
        
        # 6. 记录问诊档案
        add_encounter(session_id, req.user_id, scene, req.message, 
                     result.risk_level, result.department, result.answer, {...})
        
        # 7. 返回响应
        return ChatResponse(session_id, result.answer, result.risk_level, ...)
```

**等价 Java 代码：**
```java
@Service
@Transactional
public class ConsultationService {
    @Autowired
    private MedicalSwarm swarm;
    
    @Autowired
    private SessionRepository sessionRepo;
    
    @Autowired
    private MessageRepository messageRepo;
    
    @Autowired
    private EncounterRepository encounterRepo;
    
    public CompletableFuture<ChatResponse> chat(ChatRequest req, String scene) {
        // 1. 会话管理
        String sessionId = Optional.ofNullable(req.getSessionId())
            .orElse(UUID.randomUUID().toString());
        sessionRepo.upsert(sessionId, req.getMessage().substring(0, 30));
        
        // 2. 保存消息
        messageRepo.save(new Message(sessionId, "user", req.getMessage()));
        
        // 3. 获取历史
        List<Message> history = messageRepo.findBySessionId(sessionId, Limit.of(12));
        
        // 4. AI 推理
        SwarmResult result = swarm.run(scene, req.getMessage(), 
            req.getPatientContext(), history).join();
        
        // 5. 保存回复
        messageRepo.save(new Message(sessionId, "assistant", result.getAnswer()));
        
        // 6. 记录档案
        encounterRepo.save(new Encounter.Builder()
            .sessionId(sessionId)
            .userId(req.getUserId())
            .scene(scene)
            .chiefComplaint(req.getMessage())
            .riskLevel(result.getRiskLevel())
            .department(result.getDepartment())
            .summary(result.getAnswer())
            .build());
        
        // 7. 构建响应
        return CompletableFuture.completedFuture(ChatResponse.builder()
            .sessionId(sessionId)
            .answer(result.getAnswer())
            .riskLevel(result.getRiskLevel())
            .suggestions(result.getSuggestions())
            .recommendedDepartment(result.getDepartment())
            .thinkingSteps(result.getThinkingSteps())
            .disclaimer(DISCLAIMER)
            .evidence(result.getEvidence())
            .agentTrace(result.getTrace())
            .metrics(result.getMetrics())
            .build());
    }
}
```

---

## 总结对比表

| Python (FastAPI) | Java (Spring Boot) | 说明 |
|------------------|-------------------|------|
| `class XxxService` | `@Service public class XxxService` | 服务层 |
| `self.xxx = Yyy()` | `@Autowired private Yyy xxx;` | 依赖注入 |
| `async def method()` | `@Async public CompletableFuture<T> method()` | 异步方法 |
| `await asyncio.gather(a, b)` | `CompletableFuture.allOf(a, b)` | 并行执行 |
| `asyncio.to_thread(func)` | `CompletableFuture.supplyAsync(() -> func())` | 线程池执行 |
| `SETTINGS["key"]` | `@Value("${key}")` | 配置注入 |
| `@dataclass` | `@Data` 或 `record` | 数据类 |
| `BaseModel` (Pydantic) | `@Validated` DTO | 数据验证 |
| `json.loads()` | `ObjectMapper.readValue()` | JSON 解析 |
| `re.findall()` | `Pattern.compile().matcher()` | 正则表达式 |
| `Counter(tokens)` | `Map<String, Integer> tokenFreq` | 词频统计 |
| `list.sort(key=lambda x: x.score)` | `list.sort(Comparator.comparingDouble(X::getScore))` | 排序 |

---

## 学习建议

1. **先看入口**：`agent_orchestrator.py` → `ConsultationService.chat()` → `MedicalSwarm.run()`
2. **理解流程**：路由 → 症状分析 → 并行检索 → LLM 推理 → Fallback → 规范化 → 合规检查
3. **关注降级**：LLM 推理有 4 重降级策略，确保系统稳定性
4. **注意异步**：大量使用 `async/await`，类似 Java 的 `CompletableFuture`
5. **规则引擎**：`skills.py` 中的关键词匹配是简单的规则引擎实现
