from __future__ import annotations

import unicodedata
from typing import Dict, List


# ==================== Java 类比说明 ====================
# 这个文件类似于 Spring Boot 中的工具类（Utils）或规则引擎（Rule Engine）
# 作用：提供症状分析、风险评估、生活建议等本地规则
# 等价于：@Component public class MedicalSkills { public static final List<String> HIGH_RISK_KEYWORDS = ...; }
# ================================================

# 高风险关键词列表（类似枚举或常量配置）
# Java: public static final List<String> HIGH_RISK_KEYWORDS = Arrays.asList(...);
HIGH_RISK_KEYWORDS = [
    "胸痛",
    "呼吸困难",
    "意识不清",
    "抽搐",
    "便血",
    "咯血",
    "剧烈头痛",
    "高热不退",
    "昏迷",
    "偏瘫",
    "黑便",
    "呕血",
]

# 中风险关键词列表
# Java: public static final List<String> MEDIUM_RISK_KEYWORDS = Arrays.asList(...);
MEDIUM_RISK_KEYWORDS = [
    "发热",
    "发烧",
    "头痛",
    "腹痛",
    "呕吐",
    "腹泻",
    "腰痛",
    "腰疼",
    "心慌",
    "血压高",
    "血糖高",
    "持续",
    "咳嗽",
]


def _normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "")


def analyze_symptoms(question: str) -> Dict:
    """
    分析症状（类似规则引擎的症状分类器）
    
    Java 等价：
    @Component
    public class SymptomAnalyzer {
        public Map<String, Object> analyzeSymptoms(String question) {
            List<String> symptoms = new ArrayList<>();
            
            // 提取匹配的症状关键词
            for (String keyword : HIGH_RISK_KEYWORDS) {
                if (question.contains(keyword)) {
                    symptoms.add(keyword);
                }
            }
            
            // 判断所属身体系统（类似策略模式）
            String bodySystem = classifyBodySystem(question);
            
            return Map.of("symptoms", symptoms, "body_system", bodySystem);
        }
        
        private String classifyBodySystem(String question) {
            if (question.contains("胸痛") || question.contains("心慌")) {
                return "心血管系统";
            } else if (question.contains("咳嗽") || question.contains("呼吸")) {
                return "呼吸系统";
            }
            // ... 其他系统判断
            return "全科";
        }
    }
    """
    question = _normalize_text(question)
    symptoms = []
    
    # 遍历所有风险关键词，提取匹配的症状
    # Java: for (String word : HIGH_RISK_KEYWORDS) { if (question.contains(word)) symptoms.add(word); }
    for word in HIGH_RISK_KEYWORDS + MEDIUM_RISK_KEYWORDS:
        if word in question:
            symptoms.append(word)

    # 默认归为全科
    # Java: String bodySystem = "全科";
    body_system = "全科"
    
    # 根据关键词判断所属身体系统（类似 if-else 分支逻辑）
    # Java: if (question.contains("胸痛") || question.contains("心慌")) { bodySystem = "心血管系统"; }
    if any(w in question for w in ["胸痛", "心慌", "血压", "心悸"]):
        body_system = "心血管系统"
    elif any(w in question for w in ["咳嗽", "呼吸", "咯血", "黄痰", "胸闷"]):
        body_system = "呼吸系统"
    elif any(w in question for w in ["腹痛", "腹泻", "拉肚子", "呕吐", "恶心", "胃痛", "反酸"]):
        body_system = "消化系统"
    elif any(w in question for w in ["头痛", "头晕", "意识", "抽搐", "昏迷", "眩晕"]):
        body_system = "神经系统"
    elif any(w in question for w in ["腰痛", "腰疼", "关节", "扭伤", "骨折"]):
        body_system = "骨骼肌肉系统"
    elif any(w in question for w in ["尿频", "尿急", "尿痛", "血尿"]):
        body_system = "泌尿系统"
    elif any(w in question for w in ["皮疹", "瘙痒", "湿疹", "荨麻疹"]):
        body_system = "皮肤系统"
    
    return {"symptoms": symptoms, "body_system": body_system}


def assess_risk(question: str) -> Dict:
    """
    评估风险等级（类似规则引擎的风险评估器）
    
    Java 等价：
    @Component
    public class RiskAssessor {
        public Map<String, String> assessRisk(String question) {
            // 高风险判断
            if (HIGH_RISK_KEYWORDS.stream().anyMatch(question::contains)) {
                return Map.of(
                    "risk_level", "高风险",
                    "reason", "问题中包含可能需要紧急处理的高危症状。",
                    "advice", "建议立即线下就医或联系急救服务。"
                );
            }
            
            // 中风险判断
            if (MEDIUM_RISK_KEYWORDS.stream().anyMatch(question::contains)) {
                return Map.of(
                    "risk_level", "中风险",
                    "reason", "问题中包含持续或需要观察的常见症状。",
                    "advice", "建议记录症状变化，必要时到医院就诊。"
                );
            }
            
            // 低风险
            return Map.of(
                "risk_level", "低风险",
                "reason", "暂未识别到明确高危信号。",
                "advice", "可先进行健康观察和生活方式调整，如症状持续或加重应就医。"
            );
        }
    }
    """
    question = _normalize_text(question)
    # 高风险判断（类似 anyMatch 操作）
    # Java: if (HIGH_RISK_KEYWORDS.stream().anyMatch(question::contains)) { ... }
    if any(word in question for word in HIGH_RISK_KEYWORDS):
        return {
            "risk_level": "高风险",
            "reason": "问题中包含可能需要紧急处理的高危症状。",
            "advice": "建议立即线下就医或联系急救服务。",
        }
    
    # 中风险判断
    # Java: if (MEDIUM_RISK_KEYWORDS.stream().anyMatch(question::contains)) { ... }
    if any(word in question for word in MEDIUM_RISK_KEYWORDS):
        return {
            "risk_level": "中风险",
            "reason": "问题中包含持续或需要观察的常见症状。",
            "advice": "建议记录症状变化，必要时到医院就诊。",
        }
    
    # 低风险（默认情况）
    return {
        "risk_level": "低风险",
        "reason": "暂未识别到明确高危信号。",
        "advice": "可先进行健康观察和生活方式调整，如症状持续或加重应就医。",
    }


def lifestyle_recommendations(question: str) -> List[str]:
    """
    生成生活建议（类似基于规则的建议生成器）
    
    Java 等价：
    @Component
    public class LifestyleAdvisor {
        public List<String> getRecommendations(String question) {
            List<String> suggestions = new ArrayList<>();
            suggestions.add("保持规律作息，避免熬夜和过度劳累。");
            suggestions.add("补充水分，饮食清淡，避免自行叠加用药。");
            
            // 根据症状添加特定建议（类似策略模式）
            if (question.contains("腹泻") || question.contains("拉肚子")) {
                suggestions.add("注意补液，观察是否有发热、便血...");
                suggestions.add("近期避免油腻、辛辣、生冷食物...");
            }
            
            if (question.contains("腰痛") || question.contains("腰疼")) {
                suggestions.add("避免久坐久站和搬重物...");
                suggestions.add("若外伤后疼痛、疼痛放射到下肢...");
            }
            
            // ... 其他症状判断
            
            return suggestions.subList(0, Math.min(5, suggestions.size()));
        }
    }
    """
    # 基础建议（通用）
    suggestions = [
        "保持规律作息，避免熬夜和过度劳累。",
        "补充水分，饮食清淡，避免自行叠加用药。",
    ]
    
    # 根据症状添加特定建议（类似 if-else 分支逻辑）
    # Java: if (question.contains("腹泻")) { suggestions.add(...); }
    if "腹泻" in question or "拉肚子" in question:
        suggestions += [
            "注意补液，观察是否有发热、便血、明显脱水或持续腹痛。",
            "近期避免油腻、辛辣、生冷食物，必要时咨询消化科。",
        ]
    if "腰痛" in question or "腰疼" in question:
        suggestions += [
            "避免久坐久站和搬重物，观察是否伴有下肢麻木、无力或大小便异常。",
            "若外伤后疼痛、疼痛放射到下肢或持续加重，建议骨科/外科就诊。",
        ]
    if "血压" in question or "高血压" in question:
        suggestions += [
            "减少盐摄入，规律监测血压。",
            "如已长期用药，不建议自行停药或调整剂量。",
        ]
    if "血糖" in question or "糖尿病" in question:
        suggestions += [
            "控制精制碳水摄入，记录空腹和餐后血糖。",
            "出现低血糖表现时应及时处理并咨询医生。",
        ]
    if "发热" in question or "高热" in question:
        suggestions += [
            "记录体温变化，关注精神状态和尿量。",
            "儿童、老人或基础病患者发热应更谨慎。",
        ]
    if "咳嗽" in question:
        suggestions += [
            "观察是否伴随胸闷、气短、咯血或持续高热。",
            "外出佩戴口罩，减少对他人传播风险。",
        ]
    
    # 最多返回5条建议（类似 subList(0, 5)）
    # Java: return suggestions.subList(0, Math.min(5, suggestions.size()));
    return suggestions[:5]


def compliance_guard(answer: str) -> str:
    """
    合规检查（类似 AOP 拦截器或过滤器）
    
    Java 等价：
    @Component
    public class ComplianceGuard {
        private static final Map<String, String> REPLACEMENTS = Map.of(
            "确诊为", "需要由医生评估是否为",
            "一定是", "可能为",
            "必须服用", "是否用药需要医生评估",
            "剂量是", "具体剂量需要遵医嘱"
        );
        
        public String guard(String answer) {
            // 替换不合规表达
            for (Map.Entry<String, String> entry : REPLACEMENTS.entrySet()) {
                answer = answer.replace(entry.getKey(), entry.getValue());
            }
            
            // 添加免责声明
            String disclaimer = "以上内容仅用于健康科普和就医参考...";
            if (!answer.contains(disclaimer)) {
                answer = answer.trim() + "\n\n" + disclaimer;
            }
            
            return answer;
        }
    }
    """
    # 定义需要替换的不合规表达（类似常量 Map）
    # Java: private static final Map<String, String> REPLACEMENTS = Map.of(...);
    replacements = {
        "确诊为": "需要由医生评估是否为",
        "一定是": "可能为",
        "必须服用": "是否用药需要医生评估",
        "剂量是": "具体剂量需要遵医嘱",
    }
    
    # 执行替换（类似 forEach 循环）
    # Java: for (Map.Entry<String, String> entry : replacements.entrySet()) { ... }
    for src, dst in replacements.items():
        answer = answer.replace(src, dst)

    # 添加免责声明（类似 AOP After Advice）
    # Java: if (!answer.contains(disclaimer)) { answer += "\n\n" + disclaimer; }
    disclaimer = "以上内容仅用于健康科普和就医参考，不能替代医生诊断、处方或治疗。"
    if disclaimer not in answer:
        answer = answer.rstrip() + "\n\n" + disclaimer
    
    return answer
