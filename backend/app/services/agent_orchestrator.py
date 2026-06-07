from __future__ import annotations

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.medical_business import ConsultationService


# ==================== Java 类比说明 ====================
# 这个类类似于 Spring Boot 中的 Facade 模式或 Workflow Engine
# 作用：统一入口，编排业务流程
# 等价于：@Component public class MedicalAgentOrchestrator { @Autowired private ConsultationService service; }
# ================================================

class MedicalAgentOrchestrator:
    """
    医疗智能体编排器（类似 Spring 的 Facade/Workflow Engine）
    
    Java 等价代码：
    @Component
    public class MedicalAgentOrchestrator {
        @Autowired
        private ConsultationService consultationService;
        
        public CompletableFuture<ChatResponse> handle(ChatRequest request) {
            return consultationService.chat(request, "consultation");
        }
    }
    """
    
    def __init__(self):
        # 类似 @Autowired 或构造函数注入
        # Java: this.service = new ConsultationService();
        self.service = ConsultationService()

    async def handle(self, req: ChatRequest) -> ChatResponse:
        """
        处理聊天请求（类似 Controller 调用 Service）
        
        Java 等价：
        @PostMapping("/chat")
        public ResponseEntity<ChatResponse> chat(@RequestBody ChatRequest req) {
            return ResponseEntity.ok(service.chat(req, "consultation"));
        }
        """
        # 委托给业务服务层处理，固定场景为"线上问诊"
        # Java: return service.chat(req, "consultation");
        return await self.service.chat(req, scene="consultation")
