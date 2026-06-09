# Dify 企业感工作流搭建指南

> 目标：在 Dify 画布上搭出 **12+ 节点、有并行/分支/审计** 的编排图，对齐 LangGraph 链路，面试时「一眼不像 Demo」。
>
> 说明：这是**展示型编排增强**——节点名称和拓扑对齐企业实践，核心医疗逻辑仍在本地 Skills（可测试、可审计）。
>
> 开源主线：Dify 是可选增强。没有 Dify API Key 或公网隧道时，请使用本地 LangGraph 工作流完成主要演示。

## 参考工作流

- 应用名称：`medical-consultation`
- Studio 地址：https://cloud.dify.ai/app/d2051109-a79b-468a-8b98-73eeed4d745e/workflow
- 画布截图：见 `docs/assets/dify-workflow.png`

## 一、你现在 vs 目标

| 现在（Demo 感） | 目标（企业感） |
|----------------|----------------|
| 4 个 HTTP 串行 | 12+ 节点，有并行与多级分支 |
| 节点名「HTTP 请求」 | 统一命名：`01_` `02_` + 职能 |
| 无患者上下文 | 开始节点注入 `patient_context` |
| 无 RAG 证据链 | 并行召回知识库 |
| 一个 LLM 了事 | 意图识别 → 循证推理 → 合规审计 分层 |
| 无错误处理 | HTTP 失败走降级分支 |

## 二、目标拓扑（照着画）

```text
[开始] user_query + patient_context
    │
    ▼
[02_意图识别_LLM]  输出 scene / keywords / need_rag
    │
    ├──────────────────┐
    ▼                  ▼
[03a_症状分析_HTTP]  [03b_知识检索_HTTP]   ← 并行
    │                  │
    └────────┬─────────┘
             ▼
      [04_变量聚合]  合并 symptoms + evidence
             │
             ▼
      [05_风险评估_HTTP]
             │
             ▼
      [06_条件路由]
       ├─ 高风险 ──→ [07a_急诊话术_LLM] ──→ [09_合规审计_HTTP] ──→ [回复]
       ├─ 中风险 ──→ [07b_循证推理_LLM] ──→ [09_合规审计_HTTP] ──→ [回复]
       └─ 低风险 ──→ [07b_循证推理_LLM] ──→ [08_生活建议_HTTP] ──→ [09_合规审计_HTTP] ──→ [回复]

[06_条件路由] 的 ELSE 失败 ──→ [10_降级话术_LLM] ──→ [回复]
```

## 三、逐步操作（Dify 控制台）

### 0. 准备工作

1. 启动后端：`cd backend && python main.py`
2. 启动隧道：`cloudflared tunnel --url http://127.0.0.1:8012`
3. 记下隧道 URL，下文用 `{TUNNEL}` 代替

### 1. 开始节点 — 定义输入变量

在「开始」节点添加输入字段：

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `user_query` | string | 用户主诉（映射系统 query） |
| `patient_age` | number | 可选 |
| `patient_gender` | string | 可选 |

### 2. `02_意图识别_LLM`

- **模型**：qwen2.5-plus（或你现有的）
- **Prompt 要点**：

```text
你是医疗问诊路由 Agent。根据用户输入判断：
1. scene: consultation / triage / medication
2. keywords: 症状关键词数组
3. need_rag: true/false

用户输入：{{#start.user_query#}}
只输出 JSON：{"scene":"...","keywords":[],"need_rag":true}
```

### 3. 并行层（关键：让画布「撑起来」）

添加 **并行分支** 节点，两路同时执行：

**03a_症状分析_Skill**

- 方法：POST
- URL：`{TUNNEL}/tools/symptom_analysis`
- Body：

```json
{"input": "{{#start.user_query#}}"}
```

**03b_知识检索_RAG**

- 方法：POST
- URL：`{TUNNEL}/tools/knowledge_retrieval`
- Body：

```json
{"input": "{{#start.user_query#}}", "top_k": 5}
```

### 4. `04_变量聚合`

用 **变量赋值** 或 **模板** 节点，把两路结果合成：

```json
{
  "symptoms": "{{#03a.body.result#}}",
  "evidence": "{{#03b.body.result.evidence#}}"
}
```

（变量引用名按你画布实际节点 ID 调整。）

### 5. `05_风险评估_Skill`

- URL：`{TUNNEL}/tools/risk_assessment`
- Body：`{"input": "{{#start.user_query#}}"}`

### 6. `06_条件路由`（三级，比只有一个 IF 更像企业）

| 分支 | 条件 | 下一节点 |
|------|------|----------|
| IF-1 | `risk_assessment` 结果含 `高风险` | `07a_急诊话术_LLM` |
| ELIF | 含 `中风险` | `07b_循证推理_LLM` |
| ELSE | 其他 | `07b_循证推理_LLM` → 再接生活建议 |

### 7. `07b_循证推理_LLM`（核心，别省）

```text
你是互联网医院循证问诊 Agent。

患者：{{patient_gender}} {{patient_age}}岁
主诉：{{user_query}}
症状分析：{{symptoms}}
RAG证据：{{evidence}}

要求：
- 结合证据回答，引用证据编号
- 不能确诊、不能开处方
- 输出 JSON：risk_level, department, conclusion, reasoning, care_advice
```

### 8. `08_生活建议_Skill`（仅低风险支路）

- URL：`{TUNNEL}/tools/lifestyle_recommendations`
- Body：

```json
{
  "input": "{{#start.user_query#}}",
  "patient_info": {"age": "{{#start.patient_age#}}", "gender": "{{#start.patient_gender#}}"}
}
```

### 9. `09_合规审计_Skill`（每条出口必经 — 企业审计感）

- URL：`{TUNNEL}/tools/compliance_guard`
- Body：`{"input": "{{#07b.text#}}"}` 或上一步 LLM 输出

### 10. `10_降级话术_LLM`（HTTP 失败分支）

任一 HTTP 节点开启「失败时继续」，并增加条件：

- 若 `status != success` → 走降级 LLM，输出「本地 Skills 暂不可用，建议线下就医…」

### 11. 结束 — 结构化输出

在「直接回复」或「结束」节点输出：

```json
{
  "answer": "{{#09.body.result.cleaned_text#}}",
  "risk_level": "{{#07b.risk_level#}}",
  "department": "{{#07b.department#}}",
  "orchestrator": "dify",
  "skills_called": ["symptom_analysis","knowledge_retrieval","risk_assessment","compliance_guard"]
}
```

## 四、节点命名规范（装企业感的关键）

把「HTTP 请求」改成：

| 原名称 | 建议名称 |
|--------|----------|
| HTTP 请求 | `03a_症状分析_Skill` |
| HTTP 请求 2 | `05_风险评估_Skill` |
| HTTP 请求 3 | `09_合规审计_Skill` |
| LLM | `02_意图识别_Agent` |
| LLM 2 | `07b_循证推理_Agent` |
| 条件分支 | `06_风险路由_策略` |

**数字前缀**让评审一眼看出流水线阶段。

## 五、截图清单（放 GitHub `docs/dify-demo/`）

1. `workflow-full.png` — 全景 12 节点
2. `parallel-rag.png` — 并行症状+RAG 特写
3. `risk-routing.png` — 三级条件分支
4. `compliance-audit.png` — 合规节点在出口前
5. `preview-success.mp4` — Preview 跑通 15 秒

## 六、面试话术（配合这张图）

> 我把 Dify 定位为**可配置的编排层**，医疗规则留在本地 Skills HTTP 服务。工作流里有意图路由、并行 RAG 召回、风险策略分支和合规审计节点，和 LangGraph 状态机同构。Dify 给运营改 Prompt/分支，LangGraph 是代码级生产兜底。

## 七、和 LangGraph 对齐表（显得有架构思考）

| LangGraph 节点 | Dify 对应 |
|----------------|-----------|
| ContextAgent / symptom | `03a_症状分析` |
| RAGAgent | `03b_知识检索` |
| RiskRouteStrategy | `06_条件路由` |
| ReasoningAgent | `07b_循证推理` |
| FormatterAgent | 结构化输出 |
| SafetyAgent / compliance | `09_合规审计` |

## 八、耗时预期

| 操作 | 时间 |
|------|------|
| 按本文搭完画布 | 1–2 小时 |
| 更新隧道 + 发布 | 10 分钟 |
| 截图录屏放 GitHub | 20 分钟 |

搭完后画布节点数 **12+**，有并行、三级路由、合规审计、降级分支——面试演示足够「像企业编排」，而不必再堆更多无意义节点。
