from __future__ import annotations

import asyncio
import json
import random
import re
import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, List

from app.core.database import add_encounter, add_message, list_messages, upsert_session
from app.schemas.chat import AgentTrace, ChatRequest, ChatResponse, Evidence
from app.services.deep_search import web_search
from app.services.llm_client import LLMClient
from app.services.rag_service import RAGService
from app.services.skills import analyze_symptoms, assess_risk, compliance_guard, lifestyle_recommendations


# ==================== Java 类比说明 ====================
# 这个文件是核心业务逻辑层，类似于 Spring Boot 中的 @Service 层
# 主要包含：
# 1. MedicalSwarm - AI 编排引擎（类似 Workflow Engine + Strategy Pattern）
# 2. ConsultationService - 问诊服务（类似 @Transactional Service）
# 3. 各种工具函数 - Prompt 构建、结果解析等（类似 Utils/Helper）
#
# 整体架构：
# Controller (api/chat.py) 
#   -> Orchestrator (agent_orchestrator.py)
#     -> Service (ConsultationService)
#       -> Swarm Engine (MedicalSwarm)
#         -> RAG Service + LLM Client + Deep Search + Skills
# ================================================

# 免责声明（类似常量配置）
# Java: public static final String DISCLAIMER = "...";
DISCLAIMER = "以上内容仅用于健康科普、预问诊和就医参考，不能替代医生诊断、处方或治疗。"

# 科室列表（类似枚举或常量列表）
# Java: public static final List<String> DEPARTMENTS = Arrays.asList(...);
DEPARTMENTS = [
    "消化科",
    "妇产科",
    "皮肤科",
    "内分泌科",
    "神经内科",
    "骨科",
    "外科",
    "内科",
    "男科",
    "生殖医学科",
    "眼科",
    "肾脏病中心",
    "泌尿外科",
    "呼吸科",
    "药学门诊",
]

# 场景名称映射（类似 Enum Map）
# Java: public static final Map<String, String> SCENE_NAMES = Map.of(...);
SCENE_NAMES = {
    "triage": "智能分诊",
    "consultation": "线上问诊",
    "medication": "用药咨询",
}

# JSON 响应模板（类似 DTO 结构定义）
# Java: public static final Map<String, Object> BASE_JSON_SCHEMA = Map.of(...);
BASE_JSON_SCHEMA = {
    "risk_level": "低风险/中风险/高风险",
    "recommended_department": "必须从科室列表中选择一个",
    "conclusion": "一句话结论",
    "reasoning": "结合患者信息、RAG和联网证据的推理依据",
    "red_flags": ["需要立即线下就医或急诊的信号"],
    "next_questions": ["还需要补充追问的问题"],
    "care_advice": ["健康科普建议"],
    "evidence_summary": "引用证据摘要",
}


# 数据类（类似 Java Record 或 Lombok @Data）
# Java: public record SwarmResult(String answer, String riskLevel, String department, ...) { }
@dataclass
class SwarmResult:
    """
    AI 编排结果（类似 Java Record 或 DTO）
    
    Java 等价：
    public record SwarmResult(
        String answer,
        String riskLevel,
        String department,
        List<String> suggestions,
        List<String> thinkingSteps,
        List<Evidence> evidence,
        List<AgentTrace> trace,
        Map<String, Object> metrics
    ) {}
    """
    answer: str
    risk_level: str
    department: str
    suggestions: List[str]
    thinking_steps: List[str]
    evidence: List[Evidence]
    trace: List[AgentTrace]
    metrics: Dict[str, Any]


class MedicalSwarm:
    """
    AI 编排引擎（类似 Spring 的 Workflow Engine + Strategy Pattern）
    
    Java 等价代码：
    @Component
    public class MedicalSwarm {
        @Autowired
        private RAGService ragService;
        
        @Autowired
        private LLMClient llmClient;
        
        // 主流程：AI + RAG + DeepResearch 综合推理
        public CompletableFuture<SwarmResult> run(String scene, String message, 
                                                   Map<String, Object> patient, 
                                                   List<Map<String, Object>> history) {
            // 1. 路由识别
            // 2. 症状分析
            // 3. 并行检索 (RAG + Web Search)
            // 4. LLM 推理
            // 5. Fallback 处理
            // 6. 结果规范化
            // 7. 合规检查
        }
        
        // LLM 推理（带多重降级策略）
        private CompletableFuture<Map<String, Object>> reasonWithLLM(...) {
            // 尝试1: JSON 格式输出
            // 尝试2: 自然语言解析
            // 尝试3: JSON 修复
            // 尝试4: 紧凑 Prompt
        }
    }
    """
    
    def __init__(self):
        # 依赖注入（类似 @Autowired）
        # Java: @Autowired private RAGService ragService;
        self.rag = RAGService()
        # Java: @Autowired private LLMClient llmClient;
        self.llm = LLMClient()

    async def run(
        self,
        scene: str,
        message: str,
        patient: Dict[str, Any],
        history: List[Dict[str, Any]] | None = None,
    ) -> SwarmResult:
        """
        AI 编排主流程（类似 Workflow Engine 的主执行方法）
        
        Java 等价：
        @Async
        public CompletableFuture<SwarmResult> run(String scene, String message, 
                                                   Map<String, Object> patient,
                                                   List<Map<String, Object>> history) {
            // 1. 初始化上下文
            List<String> thinkingSteps = new ArrayList<>();
            List<AgentTrace> trace = new ArrayList<>();
            
            // 2. 路由识别
            step("RouterAgent", "route", "识别业务场景...");
            
            // 3. 症状分析（本地规则引擎）
            Map<String, Object> symptomProfile = skillsService.analyzeSymptoms(message);
            Map<String, Object> riskHint = skillsService.assessRisk(message);
            List<String> suggestions = skillsService.lifestyleRecommendations(message);
            
            // 4. 并行检索（RAG + Web Search）
            String query = buildSearchQuery(scene, message, patient, history);
            CompletableFuture<List<Evidence>> localFuture = 
                CompletableFuture.supplyAsync(() -> ragService.search(query, 6));
            CompletableFuture<List<Evidence>> webFuture = 
                deepSearchService.webSearch(query, 3, 6.0);
            
            List<Evidence> allEvidence = CompletableFuture.allOf(localFuture, webFuture)
                .thenApply(v -> Stream.concat(localFuture.join().stream(), 
                                              webFuture.join().stream())
                                      .collect(Collectors.toList()));
            
            // 5. LLM 推理（带多重降级策略）
            Map<String, Object> structured = reasonWithLLM(...).join();
            
            // 6. Fallback 处理
            if (structured == null) {
                structured = fallbackStructured(scene, message, riskHint, suggestions);
            }
            
            // 7. 结果规范化
            String department = normalizeDepartment(structured.get("recommended_department"), scene);
            String riskLevel = normalizeRisk(structured.get("risk_level"));
            String answer = renderAnswer(scene, structured, department, riskLevel);
            answer = complianceGuard(answer);
            
            // 8. 构建指标
            Map<String, Object> metrics = buildMetrics(trace, localEvidence, webEvidence);
            
            return new SwarmResult(answer, riskLevel, department, ...);
        }
        """
        history = history or []
        thinking_steps: List[str] = []
        trace: List[AgentTrace] = []

        # 内部函数：记录思考步骤（类似 Logger 或 Audit Trail）
        # Java: private void step(String agent, String action, String detail) { ... }
        def step(agent: str, action: str, detail: str) -> None:
            thinking_steps.append(f"{agent}: {detail}")
            trace.append(AgentTrace(agent=agent, action=action, detail=detail))

        # 第1步：路由识别（类似 Strategy Pattern）
        # Java: step("RouterAgent", "route", "识别业务场景为 " + SCENE_NAMES.get(scene));
        step("RouterAgent", "route", f"识别业务场景为 {SCENE_NAMES.get(scene, scene)}，进入 AI + RAG + DeepResearch 综合推理链路")

        # 第2步：症状分析（本地规则引擎，类似 RuleEngine.evaluate()）
        # Java: Map<String, Object> symptomProfile = skillsService.analyzeSymptoms(message);
        symptom_profile = analyze_symptoms(message)
        # Java: Map<String, Object> riskHint = skillsService.assessRisk(message);
        risk_hint = assess_risk(message)
        # Java: List<String> suggestions = skillsService.lifestyleRecommendations(message);
        suggestions = lifestyle_recommendations(message)
        step(
            "ContextAgent",
            "profile",
            f"整理患者上下文、历史对话和基础症状线索；本地风险提示为 {risk_hint['risk_level']}，仅作为参考",
        )

        # 第3步：构建搜索查询（类似 QueryBuilder）
        # Java: String query = buildSearchQuery(scene, message, patient, history);
        query = build_search_query(scene, message, patient, history)
        
        # 第4步：并行检索（类似 CompletableFuture.allOf）
        # Java: CompletableFuture<List<Evidence>> localFuture = CompletableFuture.supplyAsync(() -> ragService.search(query, 6));
        local_task = asyncio.to_thread(self.rag.search, query, 6)
        # Java: CompletableFuture<List<Evidence>> webFuture = deepSearchService.webSearch(query, 3, 6.0);
        web_task = web_search(query, limit=3, timeout=6.0)
        # Java: List<Evidence> allEvidence = CompletableFuture.allOf(localFuture, webFuture).thenApply(...);
        local_evidence, web_evidence = await asyncio.gather(local_task, web_task)
        evidence = list(local_evidence) + list(web_evidence)
        step("RAGAgent", "retrieve", f"本地知识库召回 {len(local_evidence)} 条证据")
        step("ResearchAgent", "deep_search", f"联网搜索返回 {len(web_evidence)} 条证据")

        # 第5步：LLM 推理（核心 AI 逻辑，带多重降级策略）
        # Java: Map<String, Object> structured = reasonWithLLM(...).join();
        structured = await self._reason_with_llm(
            scene=scene,
            message=message,
            patient=patient,
            history=history,
            symptom_profile=symptom_profile,
            risk_hint=risk_hint,
            evidence=evidence,
            suggestions=suggestions,
            step=step,
        )

        # 第6步：Fallback 处理（类似 Hystrix Fallback 或 Circuit Breaker）
        # Java: if (structured == null) { structured = fallbackStrategy.execute(...); }
        if not structured:
            structured = fallback_structured(scene, message, risk_hint, suggestions)
            step("ReasoningAgent", "fallback", "远程模型未返回可解析 JSON，启用降级结果并提示信息不足")

        # 第7步：结果规范化（类似 Data Transformer）
        # Java: String department = normalizeDepartment(structured.get("recommended_department"), scene);
        department = normalize_department(structured.get("recommended_department"), scene)
        # Java: String riskLevel = normalizeRisk(structured.get("risk_level"));
        risk_level = normalize_risk(structured.get("risk_level"))
        # Java: String answer = renderAnswer(scene, structured, department, riskLevel);
        answer = render_answer(scene, structured, department, risk_level)
        # Java: answer = complianceGuard(answer);  // AOP 合规检查
        answer = compliance_guard(answer)
        step("SafetyAgent", "guard", "完成医疗安全边界、免责声明和非诊断化表达检查")

        # 第8步：构建指标（类似 Metrics Collector）
        # Java: Map<String, Object> metrics = buildMetrics(trace, localEvidence, webEvidence);
        metrics = {
            "agent_count": len({item.agent for item in trace}),
            "local_evidence_count": len(local_evidence),
            "web_evidence_count": len(web_evidence),
            "evidence_count": len(evidence),
            "ai_structured": bool(structured),
        }
        
        # 返回结果（类似 return new SwarmResult(...)）
        return SwarmResult(answer, risk_level, department, structured.get("care_advice", suggestions), thinking_steps, evidence[:8], trace, metrics)

    async def _reason_with_llm(
        self,
        scene: str,
        message: str,
        patient: Dict[str, Any],
        history: List[Dict[str, Any]],
        symptom_profile: Dict[str, Any],
        risk_hint: Dict[str, Any],
        evidence: List[Evidence],
        suggestions: List[str],
        step,
    ) -> Dict[str, Any] | None:
        if not self.llm.enabled:
            step("ReasoningAgent", "skip", "远程大模型未启用，无法执行 AI 主导推理")
            return None

        system_prompt = build_system_prompt(scene)
        user_prompt = build_user_prompt(scene, message, patient, history, symptom_profile, risk_hint, evidence, suggestions)
        try:
            raw = await self.llm.chat(
                [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                timeout=45,
            )
            structured = parse_json_object(raw)
            if structured:
                step("ReasoningAgent", "json_reasoning", "模型已基于患者上下文、RAG证据与联网资料输出结构化 JSON")
                return structured
            if raw.strip():
                narrative = parse_narrative_answer(raw, scene)
                if narrative:
                    step("ReasoningAgent", "narrative_reasoning", "模型返回自然语言证据整合结果，已抽取科室、风险和建议")
                    return narrative
                repaired = await self._repair_json(raw, scene)
                if repaired:
                    step("FormatterAgent", "repair_json", "模型首轮输出不是合法 JSON，已完成结构化修复")
                    return repaired
            narrative = await self._narrative_reason(scene, message, patient, history, symptom_profile, risk_hint, evidence, suggestions)
            if narrative:
                step("ReasoningAgent", "narrative_retry", "JSON 模式未产出稳定内容，已切换自然语言 Prompt 完成证据整合")
                return narrative
            step("FormatterAgent", "parse_failed", "模型输出无法解析，且自然语言重试失败")
        except Exception as exc:
            step("ReasoningAgent", "llm_error", f"远程模型调用失败：{type(exc).__name__}")
            narrative = await self._narrative_reason(scene, message, patient, history, symptom_profile, risk_hint, evidence, suggestions)
            if narrative:
                step("ReasoningAgent", "narrative_retry", "结构化推理异常后，已切换自然语言 Prompt 完成证据整合")
                return narrative
        return None

    async def _compact_reason(
        self,
        scene: str,
        message: str,
        patient: Dict[str, Any],
        history: List[Dict[str, Any]],
        evidence: List[Evidence],
    ) -> Dict[str, Any] | None:
        compact_prompt = build_compact_medical_prompt(scene, message, patient, history, evidence)
        try:
            compact_text = await self.llm.chat(
                [
                    {
                        "role": "system",
                        "content": (
                            "你是中文互联网医院分诊、问诊与用药咨询助手。你需要结合患者信息、RAG证据和联网资料进行医学科普级推理，"
                            "不要只按关键词分类。不能确诊、不能开处方。回答必须包含推荐科室、风险等级、可能原因、证据依据和建议。"
                        ),
                    },
                    {"role": "user", "content": compact_prompt},
                ],
                timeout=45,
            )
            return parse_narrative_answer(compact_text, scene)
        except Exception:
            return None

    async def _repair_json(self, raw: str, scene: str) -> Dict[str, Any] | None:
        prompt = (
            "请把下面内容改写成一个合法 JSON 对象，不要输出 Markdown，不要输出解释。\n"
            f"业务场景：{SCENE_NAMES.get(scene, scene)}\n"
            f"JSON字段模板：{json.dumps(BASE_JSON_SCHEMA, ensure_ascii=False)}\n"
            f"原始内容：{raw[:3000]}"
        )
        try:
            fixed = await self.llm.chat(
                [{"role": "system", "content": "你是 JSON 格式修复器，只输出合法 JSON。"}, {"role": "user", "content": prompt}],
                timeout=20,
            )
            return parse_json_object(fixed)
        except Exception:
            return None

    async def _narrative_reason(
        self,
        scene: str,
        message: str,
        patient: Dict[str, Any],
        history: List[Dict[str, Any]],
        symptom_profile: Dict[str, Any],
        risk_hint: Dict[str, Any],
        evidence: List[Evidence],
        suggestions: List[str],
    ) -> Dict[str, Any] | None:
        if not self.llm.enabled:
            return None
        prompt = build_narrative_prompt(scene, message, patient, history, symptom_profile, risk_hint, evidence, suggestions)
        try:
            text = await self.llm.chat(
                [
                    {"role": "system", "content": "你是互联网医院医疗助手，请基于证据给出清晰、谨慎、患者友好的中文回答。"},
                    {"role": "user", "content": prompt},
                ],
                timeout=45,
            )
            parsed = parse_narrative_answer(text, scene)
            if parsed:
                return parsed
            compact_prompt = build_compact_medical_prompt(scene, message, patient, history, evidence)
            compact_text = await self.llm.chat(
                [
                    {
                        "role": "system",
                        "content": (
                            "你是中文互联网医院分诊与问诊助手。必须结合患者信息、RAG证据和联网资料进行医学科普级推理，"
                            "不要只按关键词分类。不能确诊、不能开处方。回答必须包含推荐科室、风险等级、可能原因和建议。"
                        ),
                    },
                    {"role": "user", "content": compact_prompt},
                ],
                timeout=45,
            )
            return parse_narrative_answer(compact_text, scene)
        except Exception:
            return None


class ConsultationService:
    def __init__(self):
        self.swarm = MedicalSwarm()

    async def chat(self, req: ChatRequest, scene: str = "consultation") -> ChatResponse:
        session_id = req.session_id or str(uuid.uuid4())
        upsert_session(session_id, req.message[:30] or "线上问诊")
        add_message(session_id, "user", req.message, {"scene": scene, "patient_context": req.patient_context.model_dump()})
        history = list_messages(session_id, limit=12)
        result = await self.swarm.run(scene, req.message, req.patient_context.model_dump(), history)
        add_message(
            session_id,
            "assistant",
            result.answer,
            {"scene": scene, "risk_level": result.risk_level, "department": result.department, "trace": [x.model_dump() for x in result.trace]},
        )
        add_encounter(
            session_id=session_id,
            user_id=req.user_id,
            scene=scene,
            chief_complaint=req.message,
            risk_level=result.risk_level,
            department=result.department,
            summary=result.answer,
            metadata={"evidence_count": len(result.evidence), "thinking_steps": result.thinking_steps},
        )
        return ChatResponse(
            session_id=session_id,
            answer=result.answer,
            risk_level=result.risk_level,
            suggestions=result.suggestions,
            recommended_department=result.department,
            thinking_steps=result.thinking_steps,
            disclaimer=DISCLAIMER,
            evidence=result.evidence,
            agent_trace=result.trace,
            metrics=result.metrics,
        )


def build_system_prompt(scene: str) -> str:
    if scene == "medication":
        role = (
            "你是互联网医院的用药咨询 Agent，擅长结合患者信息、药品说明、RAG证据和联网资料，"
            "分析药物相互作用、禁忌、慎用人群和就医边界。"
        )
    elif scene == "triage":
        role = (
            "你是互联网医院的智能分诊 Agent，擅长根据主诉、持续时间、伴随症状、患者基础信息、"
            "本地知识库和联网资料判断风险等级与推荐挂号科室。"
        )
    else:
        role = (
            "你是互联网医院的线上问诊 Agent，擅长连续对话、患者上下文记忆、RAG证据整合和健康科普建议。"
        )
    return f"""{role}

硬性要求：
1. 必须综合患者信息、本地RAG证据、联网DeepResearch资料和对话记忆，不要只做关键词分类。
2. recommended_department 必须从以下列表选择一个：{DEPARTMENTS}。
3. 用药咨询优先选择“药学门诊”，但如果涉及明显疾病就诊，也可以在 reasoning 中建议同时咨询相关专科。
4. 不能确诊，不能开处方，不能给具体处方剂量。
5. 如果信息不足，要写 next_questions，而不是强行下结论。
6. 必须只输出合法 JSON，不要 Markdown，不要代码块。

JSON 字段模板：
{json.dumps(BASE_JSON_SCHEMA, ensure_ascii=False)}
"""


def build_user_prompt(
    scene: str,
    message: str,
    patient: Dict[str, Any],
    history: List[Dict[str, Any]],
    symptom_profile: Dict[str, Any],
    risk_hint: Dict[str, Any],
    evidence: List[Evidence],
    suggestions: List[str],
) -> str:
    return f"""业务场景：{SCENE_NAMES.get(scene, scene)}

用户当前输入：
{message}

患者信息：
{json.dumps(patient, ensure_ascii=False)}

最近对话记忆：
{json.dumps(history[-8:], ensure_ascii=False)}

本地症状线索，仅作为参考，不得直接当最终结论：
{json.dumps(symptom_profile, ensure_ascii=False)}

本地风险提示，仅作为参考，不得直接当最终结论：
{json.dumps(risk_hint, ensure_ascii=False)}

本地基础建议，仅作为参考：
{json.dumps(suggestions, ensure_ascii=False)}

RAG 与 DeepResearch 证据：
{build_context(evidence)}

请你基于以上所有信息进行医学科普级推理，输出合法 JSON。"""


def build_narrative_prompt(
    scene: str,
    message: str,
    patient: Dict[str, Any],
    history: List[Dict[str, Any]],
    symptom_profile: Dict[str, Any],
    risk_hint: Dict[str, Any],
    evidence: List[Evidence],
    suggestions: List[str],
) -> str:
    evidence_text = build_context(evidence)
    if len(evidence_text) > 1800:
        evidence_text = evidence_text[:1800]
    return f"""患者信息：{json.dumps(patient, ensure_ascii=False)}
当前问题：{message}
业务场景：{SCENE_NAMES.get(scene, scene)}
最近对话：{json.dumps(history[-4:], ensure_ascii=False)}
本地症状线索：{json.dumps(symptom_profile, ensure_ascii=False)}
本地风险提示：{json.dumps(risk_hint, ensure_ascii=False)}
RAG和联网证据摘要：
{evidence_text}

请结合患者信息、RAG证据和联网资料回答。请按下面格式输出：
推荐科室：
风险等级：
可能原因：
依据：
建议补充追问：
红旗信号：
建议：
"""


def build_compact_medical_prompt(
    scene: str,
    message: str,
    patient: Dict[str, Any],
    history: List[Dict[str, Any]],
    evidence: List[Evidence],
) -> str:
    age = patient.get("age", "未填写")
    gender = patient.get("gender", "未填写")
    patient_text = (
        f"患者{gender}{age}岁，"
        f"既往病史：{patient.get('chronic_diseases') or '未填写'}；"
        f"过敏史：{patient.get('allergy_history') or '未填写'}；"
        f"用药史：{patient.get('medication_history') or '未填写'}。"
    )
    history_text = "；".join([str(item.get("content", ""))[:120] for item in history[-4:] if item.get("content")])
    evidence_topics = "；".join([item.title for item in evidence[:5]]) or "暂无证据"
    task_name = SCENE_NAMES.get(scene, scene)
    if scene == "medication":
        focus = "重点分析用药安全、相互作用、禁忌/慎用人群、是否需要药师或专科医生进一步确认。"
    elif scene == "triage":
        focus = "重点判断推荐挂号科室、风险等级、可能原因、需要补充追问的问题和红旗信号。"
    else:
        focus = "重点结合会话记忆进行连续问诊，说明可能原因、就医建议和推荐挂号科室。"
    return (
        f"{patient_text}主诉/问题：{message}。"
        f"业务场景：{task_name}。最近对话：{history_text or '无'}。"
        f"RAG与联网检索证据主题：{evidence_topics}。"
        f"{focus}"
        "请按如下格式回答：推荐科室、风险等级、可能原因、证据依据、建议补充追问、红旗信号、建议。"
    )


def parse_json_object(text: str) -> Dict[str, Any] | None:
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.I).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    candidates = [cleaned]
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        candidates.append(match.group(0))
    for item in candidates:
        try:
            data = json.loads(item)
            return data if isinstance(data, dict) else None
        except Exception:
            continue
    return None


def parse_narrative_answer(text: str, scene: str) -> Dict[str, Any] | None:
    if not text or not text.strip():
        return None
    department = extract_department(text, scene)
    risk_level = extract_risk(text)
    return {
        "risk_level": risk_level,
        "recommended_department": department,
        "conclusion": first_meaningful_line(text),
        "reasoning": text.strip(),
        "red_flags": extract_bullets_after(text, ["红旗信号", "急诊", "及时就医"]),
        "next_questions": extract_bullets_after(text, ["补充追问", "需要补充", "就诊前准备"]),
        "care_advice": extract_bullets_after(text, ["建议", "处理建议", "注意事项"]),
        "evidence_summary": "已由远程大模型结合患者信息、本地RAG证据和联网DeepResearch资料进行综合整理。",
    }


def extract_department(text: str, scene: str) -> str:
    if scene == "medication":
        return "药学门诊"
    explicit = re.search(r"推荐科室[：:]\s*([^\n，,。；; ]+)", text)
    if explicit:
        candidate = explicit.group(1).strip()
        for department in DEPARTMENTS:
            if department in candidate:
                return department
    for department in DEPARTMENTS:
        if department in text:
            return department
    aliases = [
        ("妇科", "妇产科"),
        ("妇产", "妇产科"),
        ("男科", "男科"),
        ("泌尿", "泌尿外科"),
        ("消化", "消化科"),
        ("骨科", "骨科"),
        ("皮肤", "皮肤科"),
        ("呼吸", "呼吸科"),
        ("神经", "神经内科"),
        ("内分泌", "内分泌科"),
        ("眼科", "眼科"),
    ]
    for key, department in aliases:
        if key in text:
            return department
    return "内科"


def extract_risk(text: str) -> str:
    explicit = re.search(r"风险等级[：:]\s*[-\s]*(低风险|中风险|高风险|低|中等|中度|高)", text)
    if explicit:
        value = explicit.group(1)
        if value in {"中等", "中度", "中"}:
            return "中风险"
        if value == "低":
            return "低风险"
        if value == "高":
            return "高风险"
        return value
    if any(word in text for word in ["中等风险", "中度风险", "中等", "中度"]):
        return "中风险"
    if any(word in text for word in ["急诊", "立即就医", "高风险", "严重", "剧烈", "晕厥", "大量出血"]):
        return "高风险"
    if any(word in text for word in ["建议就诊", "尽快就诊", "中风险", "明显疼痛", "持续"]):
        return "中风险"
    return "低风险"


def first_meaningful_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip(" -\t")
        if line and not line.startswith("推荐科室") and not line.startswith("风险等级"):
            return line[:160]
    return "已由远程大模型结合证据完成分析。"


def extract_bullets_after(text: str, headers: List[str], limit: int = 5) -> List[str]:
    lines = [line.strip() for line in text.splitlines()]
    collected: List[str] = []
    active = False
    for line in lines:
        if any(header in line for header in headers):
            active = True
            cleaned = re.sub(r"^[#\-\s]*", "", line)
            if "：" in cleaned:
                cleaned = cleaned.split("：", 1)[-1].strip()
            elif ":" in cleaned:
                cleaned = cleaned.split(":", 1)[-1].strip()
            if cleaned and cleaned not in headers:
                collected.append(cleaned)
            continue
        if active:
            if re.match(r"^(可能原因|依据|证据|推荐科室|风险等级|结论)[：:]", line):
                active = False
                continue
            cleaned = re.sub(r"^[-*•\d.、\s]+", "", line).strip()
            if cleaned:
                collected.append(cleaned)
        if len(collected) >= limit:
            break
    return collected[:limit]


def normalize_department(value: Any, scene: str) -> str:
    text = str(value or "").strip()
    if text in DEPARTMENTS:
        return text
    if scene == "medication":
        return "药学门诊"
    for department in DEPARTMENTS:
        if department in text:
            return department
    return "内科"


def normalize_risk(value: Any) -> str:
    text = str(value or "").strip()
    if text in {"低风险", "中风险", "高风险"}:
        return text
    if "高" in text:
        return "高风险"
    if "中" in text:
        return "中风险"
    return "低风险"


def render_answer(scene: str, data: Dict[str, Any], department: str, risk_level: str) -> str:
    red_flags = ensure_list(data.get("red_flags"))
    next_questions = ensure_list(data.get("next_questions"))
    care_advice = ensure_list(data.get("care_advice"))
    lines = [
        "结论：",
        str(data.get("conclusion") or "已根据患者信息、RAG证据和联网资料完成综合分析。"),
        "",
        "风险等级：",
        risk_level,
        "",
        "推荐预约挂号科室：",
        department,
        "",
        "依据与原因：",
        str(data.get("reasoning") or data.get("evidence_summary") or "模型结合当前症状、患者背景和证据进行综合判断。"),
    ]
    if next_questions:
        lines += ["", "建议补充追问：", *[f"- {item}" for item in next_questions]]
    if care_advice:
        lines += ["", "建议：", *[f"- {item}" for item in care_advice]]
    if red_flags:
        lines += ["", "需要及时线下就医或急诊的信号：", *[f"- {item}" for item in red_flags]]
    evidence_summary = data.get("evidence_summary")
    if evidence_summary:
        lines += ["", "证据摘要：", str(evidence_summary)]
    return "\n".join(lines)


def ensure_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def fallback_structured(scene: str, message: str, risk_hint: Dict[str, Any], suggestions: List[str]) -> Dict[str, Any]:
    department = "药学门诊" if scene == "medication" else "内科"
    return {
        "risk_level": risk_hint.get("risk_level", "低风险"),
        "recommended_department": department,
        "conclusion": "远程大模型暂时不可用，当前结果为降级健康科普建议。",
        "reasoning": "系统未能完成 AI 主导的证据整合，请补充症状、持续时间、伴随表现和既往病史后重试。",
        "red_flags": ["胸痛", "呼吸困难", "意识异常", "持续高热不退", "便血或咯血", "剧烈疼痛"],
        "next_questions": ["症状持续多久？", "是否逐渐加重？", "是否存在基础病、过敏史或长期用药？"],
        "care_advice": suggestions,
        "evidence_summary": "降级模式下未生成完整证据摘要。",
    }


def build_search_query(scene: str, message: str, patient: Dict[str, Any], history: List[Dict[str, Any]]) -> str:
    history_text = " ".join([str(item.get("content", "")) for item in history[-4:]])
    if scene == "medication":
        return f"用药安全 药物相互作用 禁忌 特殊人群 {message} {patient}"
    if scene == "triage":
        return f"互联网医院 分诊 指南 推荐科室 红旗症状 {message} {patient}"
    return f"线上问诊 健康科普 就医建议 推荐科室 {message} {history_text} {patient}"


def build_context(evidence: List[Evidence]) -> str:
    if not evidence:
        return "暂无可用证据。"
    return "\n\n".join([f"[{idx + 1}] {item.title} | {item.source} | score={item.score}\n{item.content[:700]}" for idx, item in enumerate(evidence[:8])])


def departments() -> List[str]:
    return DEPARTMENTS


REPORTS = [
    {
        "id": "LAB2026050301",
        "type": "检验",
        "title": "血常规",
        "name": "血常规",
        "report_date": "2026-05-02",
        "date": "2026-05-02",
        "status": "部分异常",
        "items": [
            {"name": "白细胞", "value": "11.2", "unit": "10^9/L", "reference": "3.5-9.5", "range": "3.5-9.5", "flag": "偏高"},
            {"name": "中性粒细胞比例", "value": "78", "unit": "%", "reference": "40-75", "range": "40-75", "flag": "偏高"},
            {"name": "血红蛋白", "value": "136", "unit": "g/L", "reference": "130-175", "range": "130-175", "flag": "正常"},
        ],
    },
    {
        "id": "IMG2026050108",
        "type": "检查",
        "title": "胸部 CT",
        "name": "胸部 CT",
        "report_date": "2026-05-01",
        "date": "2026-05-01",
        "status": "已出报告",
        "items": [
            {"name": "影像所见", "value": "双肺纹理稍增多，未见明显实变影", "unit": "", "reference": "", "range": "", "flag": "提示随访"},
            {"name": "报告建议", "value": "结合临床症状，必要时呼吸科复诊", "unit": "", "reference": "", "range": "", "flag": "建议"},
        ],
    },
    {
        "id": "LAB2026042812",
        "type": "检验",
        "title": "肝肾功能",
        "name": "肝肾功能",
        "report_date": "2026-04-28",
        "date": "2026-04-28",
        "status": "正常",
        "items": [
            {"name": "ALT", "value": "24", "unit": "U/L", "reference": "0-40", "range": "0-40", "flag": "正常"},
            {"name": "肌酐", "value": "68", "unit": "umol/L", "reference": "45-84", "range": "45-84", "flag": "正常"},
        ],
    },
]


def report_list() -> List[Dict[str, Any]]:
    return REPORTS


async def interpret_report(report_id: str) -> Dict[str, Any]:
    report = next((item for item in REPORTS if item["id"] == report_id), None)
    if not report:
        return {"id": report_id, "analysis": "未查询到该报告。"}

    abnormal = [item for item in report["items"] if item["flag"] != "正常"]
    department = "呼吸科" if "胸" in report["name"] or "白细胞" in str(report["items"]) else "内科"
    risk_level = "中风险" if abnormal else "低风险"
    llm = LLMClient()
    if llm.enabled:
        prompt = (
            "请用患者友好的中文解读这份检验/检查报告，重点分析异常项可能对应的常见原因、"
            "需要结合哪些症状判断、建议复查或就诊科室。不要确诊，不要制造恐慌。\n"
            f"报告：{report}"
        )
        try:
            text = await llm.chat(
                [{"role": "system", "content": "你是医院报告解读 Agent，只做科普解释和就医建议。"}, {"role": "user", "content": prompt}],
                timeout=12,
            )
        except Exception:
            text = report_fallback(report, abnormal, department)
    else:
        text = report_fallback(report, abnormal, department)
    text = compliance_guard(text)
    return {"id": report_id, "department": department, "risk_level": risk_level, "analysis": text, "interpretation": text}


def report_fallback(report: Dict[str, Any], abnormal: List[Dict[str, Any]], department: str) -> str:
    if not abnormal:
        return f"报告《{report['name']}》当前未见明显异常项。若仍有不适，建议结合症状咨询内科或相关专科。"
    lines = [f"报告《{report['name']}》有 {len(abnormal)} 项需要关注："]
    for item in abnormal:
        if "白细胞" in item["name"] or "中性" in item["name"]:
            reason = "可能与感染、炎症、应激反应等有关，需要结合发热、咳嗽、咽痛、腹泻等症状判断"
        else:
            reason = "需要结合临床症状进一步判断"
        lines.append(f"- {item['name']}：{item['value']}{item.get('unit','')}，标记为{item['flag']}，{reason}。")
    lines.append(f"建议结合症状、体温、用药史和既往病史咨询「{department}」。异常指标不等于确诊，应由医生结合临床判断。")
    return "\n".join(lines)


def schedule_for_department(department: str, booked_counts: Dict[str, int] | None = None) -> Dict[str, Any]:
    from app.core.database import appointment_key

    booked_counts = booked_counts or {}
    titles = ["主任医师", "副主任医师", "主治医师"]
    surnames = ["王", "李", "张", "陈", "刘", "赵", "周", "黄", "林", "吴"]
    rows = []
    today = date.today()
    seed = sum(ord(ch) for ch in department)
    random.seed(seed)
    for day in range(7):
        visit_date = today + timedelta(days=day)
        for period, slots in [("上午", "08:30-11:30"), ("下午", "14:00-17:00")]:
            title = random.choice(titles)
            base_quota = random.randint(8, 32)
            doctor = f"{random.choice(surnames)}医生"
            key = appointment_key(department, doctor, visit_date.isoformat(), period, slots)
            remaining = max(base_quota - booked_counts.get(key, 0), 0)
            rows.append(
                {
                    "schedule_id": key,
                    "department": department,
                    "visit_date": visit_date.isoformat(),
                    "date": visit_date.isoformat(),
                    "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][visit_date.weekday()],
                    "period": period,
                    "time_slot": slots,
                    "doctor": doctor,
                    "doctor_title": title,
                    "title": title,
                    "remaining": remaining,
                    "quota": base_quota,
                    "fee": random.choice([25, 35, 50, 80]),
                }
            )
    return {"department": department, "schedule": rows}
