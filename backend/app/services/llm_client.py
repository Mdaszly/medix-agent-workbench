from __future__ import annotations

import asyncio
from typing import Dict, List
import httpx

from app.core.config import SETTINGS


# ==================== Java 类比说明 ====================
# 这个类类似于 Spring Boot 中的 RestTemplate 或 WebClient
# 作用：封装 LLM API 调用，提供重试机制和超时控制
# 等价于：@Component public class LLMClient { private final RestTemplate restTemplate; }
# ================================================

class LLMClient:
    """
    LLM 客户端（类似 Spring 的 RestTemplate/WebClient）
    
    Java 等价代码：
    @Component
    public class LLMClient {
        @Value("${llm.api-key}")
        private String apiKey;
        
        @Value("${llm.base-url}")
        private String baseUrl;
        
        private final RestTemplate restTemplate = new RestTemplate();
        private boolean enabled;
        
        // 构造函数初始化
        public LLMClient() {
            this.enabled = !apiKey.isEmpty();
        }
        
        // 带重试机制的聊天方法
        @Retryable(value = Exception.class, maxAttempts = 3, backoff = @Backoff(delay = 800))
        public CompletableFuture<String> chat(List<Map<String, String>> messages, double timeout) {
            // 调用 LLM API
        }
    }
    """
    
    def __init__(self):
        # 加载配置（类似 @Value 或 @ConfigurationProperties）
        # Java: @Value("${llm}") private Map<String, Object> config;
        self.config = SETTINGS["llm"]
        
        # 检查是否启用（类似 @ConditionalOnProperty）
        # Java: @ConditionalOnProperty(name = "features.enable-llm", havingValue = "true")
        self.enabled = bool(SETTINGS["features"].get("enable_llm")) and bool(self.config.get("api_key"))
        
        # HTTP 客户端（类似 RestTemplate 或 WebClient）
        # Java: private final AsyncOpenAI openAIclient;
        self.client = None
        self.use_sdk = False
        
        if self.enabled:
            try:
                # 尝试使用 OpenAI SDK（类似引入 spring-boot-starter-openai）
                from openai import AsyncOpenAI

                # 初始化 SDK 客户端
                # Java: this.openAIclient = new AsyncOpenAI(apiKey, baseUrl);
                self.client = AsyncOpenAI(api_key=self.config["api_key"], base_url=self.config["base_url"])
                self.use_sdk = True
            except Exception:
                # SDK 不可用时降级为 HTTP 调用
                self.client = None

    async def chat(self, messages: List[Dict[str, str]], timeout: float = 60.0) -> str:
        """
        发送聊天请求（带重试机制）
        
        Java 等价：
        @Retryable(value = Exception.class, maxAttempts = 3, backoff = @Backoff(delay = 800))
        public CompletableFuture<String> chat(List<Map<String, String>> messages, double timeout) {
            return _chatOnce(messages, timeout);
        }
        """
        if not self.enabled:
            # 类似 @ConditionalOnProperty 检查失败时抛出异常
            # Java: throw new IllegalStateException("LLM is disabled or api_key is empty");
            raise RuntimeError("LLM is disabled or api_key is empty")
        
        last_error: Exception | None = None
        
        # 获取重试次数配置（类似 @Value("${llm.max-retries:2}")）
        # Java: int maxRetries = config.getMaxRetries();
        max_retries = int(self.config.get("max_retries", 2))
        max_retries = max(1, min(max_retries, 3))  # 限制在 1-3 次
        
        # 重试循环（类似 Spring Retry 或 Resilience4j Retry）
        # Java: for (int attempt = 0; attempt < maxRetries; attempt++) { ... }
        for attempt in range(max_retries):
            try:
                text = await self._chat_once(messages, timeout)
                if text.strip() or attempt == max_retries - 1:
                    return text
            except Exception as exc:
                last_error = exc
                if attempt == max_retries - 1:
                    raise  # 最后一次重试失败，抛出异常
            
            # 指数退避等待（类似 @Backoff(delay = 800, multiplier = 1.8)）
            # Java: Thread.sleep(800 + attempt * 800);
            await asyncio.sleep(0.8 + attempt * 0.8)
        
        if last_error:
            raise last_error
        return ""

    async def _chat_once(self, messages: List[Dict[str, str]], timeout: float = 60.0) -> str:
        """
        单次聊天请求（类似 RestTemplate.postForObject）
        
        Java 等价：
        private String _chatOnce(List<Map<String, String>> messages, double timeout) {
            if (useSdk) {
                return callWithSDK(messages);
            } else {
                return callWithHTTP(messages);
            }
        }
        """
        if self.use_sdk and self.client is not None:
            # 使用 OpenAI SDK（类似使用 spring-ai-openai-starter）
            # Java: CompletionResponse response = openAIclient.chat().completions().create(...);
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.config["model_name"],
                    messages=messages,
                    temperature=float(self.config.get("temperature", 0.3)),
                    max_tokens=int(self.config.get("max_tokens", 1200)),
                ),
                timeout=timeout,
            )
            return response.choices[0].message.content or ""

        # 降级为 HTTP 调用（类似 RestTemplate.postForObject）
        # Java: ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);
        url = self.config["base_url"].rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {self.config['api_key']}", "Content-Type": "application/json"}
        payload = {
            "model": self.config["model_name"],
            "messages": messages,
            "temperature": float(self.config.get("temperature", 0.3)),
            "max_tokens": int(self.config.get("max_tokens", 1200)),
        }
        
        async def post_once() -> Dict:
            # 创建 HTTP 客户端（类似 new RestTemplate()）
            # Java: HttpHeaders headers = new HttpHeaders(); headers.setBearerAuth(apiKey);
            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=8.0, read=timeout, write=10.0, pool=5.0)) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()  # 类似 response.getStatusCode().is2xxSuccessful()
                return resp.json()

        # 执行 POST 请求（类似 restTemplate.postForObject(url, request, Map.class)）
        data = await asyncio.wait_for(post_once(), timeout=timeout + 2)
        return data["choices"][0]["message"]["content"] or ""
