# 医路通 AI 企业级医疗助手

一个前后端分离的医疗 Agent 应用项目，集成多 Agent 协作、Skills 工具调用、RAG 医学知识库、DeepResearch 联网增强、SQLite 会话记忆、医疗安全合规和 Vue3 可视化工作台。

## 技术栈

- Backend: FastAPI, SQLite, OpenAI-compatible API, RAG, Skills, DeepResearch
- Frontend: Vue3, Vite, Element Plus, ECharts, Axios
- Knowledge: Markdown 本地知识库
- Memory: SQLite 会话与消息记录

## 快速启动

```bash
cd 医疗助手企业版/backend
pip install -r requirements.txt
python main.py
```

```bash
cd 医疗助手企业版/frontend
npm install
npm run dev
```

访问：

```text
http://127.0.0.1:5178
```

后端接口：

```text
http://127.0.0.1:8012/api/health
```

## 配置

复制或修改：

```text
backend/config/config.yaml
```

默认不开启真实 LLM，系统会使用本地规则 + RAG 兜底回答。填写 API Key 并设置：

```yaml
features:
  enable_llm: true
```

即可启用真实大模型。
