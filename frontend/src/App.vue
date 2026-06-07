<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">医路通 AI</div>
      <div class="brand-sub">互联网医院智能分诊、问诊、用药、报告与预约服务平台</div>
      <button
        v-for="item in navItems"
        :key="item.key"
        class="nav-item"
        :class="{ active: activePage === item.key }"
        @click="activePage = item.key"
      >
        <span>{{ item.icon }}</span>
        <strong>{{ item.label }}</strong>
      </button>
    </aside>

    <main class="main">
      <section class="hero">
        <div>
          <h1>{{ pageMeta.title }}</h1>
          <p>{{ pageMeta.subtitle }}</p>
        </div>
        <div class="hero-tags">
          <el-tag type="success">DeepResearch 默认开启</el-tag>
          <el-tag type="primary">三轨编排 Swarm / LangGraph / Dify</el-tag>
          <el-tag type="warning">RAG 证据引用</el-tag>
        </div>
      </section>

      <section class="nurse-assistant">
        <div class="nurse-avatar" aria-hidden="true">
          <div class="nurse-cap">+</div>
          <div class="nurse-face"><span></span><span></span></div>
          <div class="nurse-body"></div>
        </div>
        <div class="nurse-copy">
          <strong>您好，我是医路通智能护士助手</strong>
          <p>我会先检索本地医疗知识库和联网资料，再交由 AI 综合推理，为你整理分诊、问诊和用药建议。</p>
        </div>
        <div class="medical-icons">
          <span>分诊</span>
          <span>问诊</span>
          <span>用药</span>
          <span>挂号</span>
        </div>
      </section>

      <section class="metrics three">
        <button class="metric-card clickable" @click="activePage = 'triage'">
          <i class="metric-icon">+</i>
          <span>服务模块</span>
          <strong>6</strong>
          <small>分诊 / 问诊 / 用药 / 报告 / 挂号</small>
        </button>
        <button class="metric-card clickable" @click="goRecords">
          <i class="metric-icon">≡</i>
          <span>问诊记录</span>
          <strong>{{ metrics.session_count || records.length }}</strong>
          <small>支持近 7 天、30 天、半年查询</small>
        </button>
        <button class="metric-card clickable" @click="activePage = 'reports'">
          <i class="metric-icon">▣</i>
          <span>报告查询</span>
          <strong>{{ reports.length }}</strong>
          <small>检验检查报告 + AI 解读</small>
        </button>
      </section>

      <section v-if="activePage === 'triage'" class="grid">
        <div class="panel">
          <div class="panel-title">
            <h2>智能分诊台</h2>
            <el-button type="primary" :loading="triageLoading" @click="submitTriage">生成分诊建议</el-button>
          </div>

          <div class="form-grid">
            <label>年龄
              <el-input-number v-model="patient.age" :min="0" :max="120" controls-position="right" />
            </label>
            <label>性别
              <el-select v-model="patient.gender">
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
                <el-option label="未说明" value="未说明" />
              </el-select>
            </label>
            <label>既往病史
              <el-input v-model="patient.chronic_diseases" placeholder="如：高血压、糖尿病" />
            </label>
            <label>过敏史
              <el-input v-model="patient.allergy_history" placeholder="如：青霉素过敏" />
            </label>
            <label class="field-wide">用药史
              <el-input v-model="patient.medication_history" placeholder="如：正在服用布洛芬、降压药" />
            </label>
          </div>
          <el-input
            v-model="triageText"
            type="textarea"
            :rows="5"
            placeholder="请描述主诉、持续时间、伴随症状、体温、疼痛部位等，例如：腹泻一天，伴有腹痛，没有发热"
          />

          <ResultPanel
            v-if="triageResult"
            :key="triageResult._key"
            :result="triageResult"
            banner-label="推荐挂号科室"
          />
          <div v-else class="friendly-empty">
            填写患者基础信息和症状描述后，系统会输出风险等级、推荐挂号科室、分诊依据和可追溯证据。
          </div>
        </div>

        <InsightPanel title="分诊证据与 Agent 链路" :result="triageResult" />
      </section>

      <section v-if="activePage === 'consultation'" class="grid">
        <div class="panel">
          <div class="panel-title">
            <h2>线上问诊</h2>
            <el-tag type="success">带会话记忆 · 可切换编排引擎</el-tag>
          </div>

          <OrchestratorSelector v-model="orchestratorMode" />
    <OrchestratorMetrics :metrics="consultMetrics" :mode="orchestratorMode" />

          <div v-if="pendingInterrupt" class="interrupt-banner">
            <strong>高风险症状检测</strong>
            <p>当前 LangGraph 工作流已暂停，请确认已了解需立即就医后再继续。</p>
            <div class="interrupt-actions">
              <el-button type="danger" :loading="consultLoading" @click="confirmInterrupt(true)">
                我已了解，继续查看紧急建议
              </el-button>
              <el-button :loading="consultLoading" @click="confirmInterrupt(false)">取消</el-button>
            </div>
          </div>

          <div class="chat-box" ref="chatBox">
            <div v-for="(msg, index) in messages" :key="index" class="msg" :class="msg.role">
              {{ msg.content }}
            </div>
            <div v-if="consultLoading" class="msg assistant">{{ consultLoadingHint }}</div>
          </div>
          <div class="form-grid compact">
            <label>年龄
              <el-input-number v-model="patient.age" :min="0" :max="120" controls-position="right" />
            </label>
            <label>性别
              <el-select v-model="patient.gender">
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
                <el-option label="未说明" value="未说明" />
              </el-select>
            </label>
            <label>既往病史
              <el-input v-model="patient.chronic_diseases" placeholder="如：高血压、糖尿病" />
            </label>
            <label>过敏史
              <el-input v-model="patient.allergy_history" placeholder="如：青霉素过敏" />
            </label>
            <label class="field-wide">用药史
              <el-input v-model="patient.medication_history" placeholder="如：正在服用布洛芬、降压药" />
            </label>
          </div>
          <div class="composer">
            <el-input
              v-model="consultText"
              type="textarea"
              :rows="3"
              placeholder="继续描述症状或追问建议，例如：腹泻一天应该挂什么科？"
              @keydown.ctrl.enter="submitConsultation"
            />
            <el-button type="primary" :loading="consultLoading" @click="submitConsultation">发送问诊</el-button>
          </div>
        </div>

        <InsightPanel title="问诊证据与 Agent 链路" :result="consultResult" />
      </section>

      <section v-if="activePage === 'medication'" class="grid">
        <div class="panel">
          <div class="panel-title">
            <h2>用药咨询</h2>
            <el-button type="primary" :loading="medicationLoading" @click="submitMedication">生成用药建议</el-button>
          </div>
          <div class="form-grid compact">
            <label>年龄
              <el-input-number v-model="patient.age" :min="0" :max="120" controls-position="right" />
            </label>
            <label>性别
              <el-select v-model="patient.gender">
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
                <el-option label="未说明" value="未说明" />
              </el-select>
            </label>
            <label>既往病史
              <el-input v-model="patient.chronic_diseases" placeholder="如：胃病、肝肾功能异常" />
            </label>
            <label>过敏史
              <el-input v-model="patient.allergy_history" placeholder="如：头孢过敏" />
            </label>
            <label class="field-wide">用药史
              <el-input v-model="patient.medication_history" placeholder="如：正在服用布洛芬、降压药" />
            </label>
          </div>
          <el-input
            v-model="medicationText"
            type="textarea"
            :rows="5"
            placeholder="请输入药品、症状、剂量、合并用药或特殊人群信息，例如：布洛芬和感冒灵能一起吃吗？"
          />
          <ResultPanel
            v-if="medicationResult"
            :key="medicationResult._key"
            :result="medicationResult"
            banner-label="建议咨询科室"
          />
          <div v-else class="friendly-empty">
            用药咨询会结合本地药品安全知识、联网资料与患者上下文，输出药品相互作用、禁忌提醒和就医边界。
          </div>
        </div>

        <InsightPanel title="用药证据与 Agent 链路" :result="medicationResult" />
      </section>

      <section v-if="activePage === 'records'" class="panel">
        <div class="panel-title">
          <h2>问诊记录</h2>
          <el-radio-group v-model="recordDays" @change="loadRecords">
            <el-radio-button :label="7">近 7 天</el-radio-button>
            <el-radio-button :label="30">近 30 天</el-radio-button>
            <el-radio-button :label="180">近半年</el-radio-button>
          </el-radio-group>
        </div>
        <div class="record-cards">
          <article v-for="record in records" :key="record.id" class="record-card" @click="openRecord(record)">
            <div class="record-top">
              <el-tag>{{ sceneLabel(record.scene) }}</el-tag>
              <span>{{ formatTime(record.created_at) }}</span>
            </div>
            <div class="record-chief">{{ record.chief_complaint || '未填写主诉' }}</div>
            <div class="record-meta">
              <span>风险：{{ record.risk_level || '-' }}</span>
              <span>科室：{{ record.department || record.recommended_department || '-' }}</span>
            </div>
            <p>{{ shortText(record.summary) }}</p>
          </article>
        </div>
      </section>

      <section v-if="activePage === 'reports'" class="grid">
        <div class="panel">
          <h2>报告查询</h2>
          <div class="report-list">
            <article
              v-for="report in reports"
              :key="report.id"
              class="report-card"
              :class="{ active: selectedReport?.id === report.id }"
              @click="selectReport(report)"
            >
              <strong>{{ report.title || report.name }}</strong>
              <span>{{ report.type }} · {{ report.report_date || report.date }} · {{ report.status }}</span>
            </article>
          </div>
        </div>
        <div class="panel">
          <div class="panel-title">
            <h2>AI 报告解读</h2>
            <el-button type="primary" :disabled="!selectedReport" :loading="reportLoading" @click="loadReportAnalysis">解读报告</el-button>
          </div>
          <el-table v-if="selectedReport" :data="selectedReport.items" border stripe>
            <el-table-column prop="name" label="指标" />
            <el-table-column prop="value" label="结果" />
            <el-table-column prop="unit" label="单位" width="90" />
            <el-table-column label="参考范围">
              <template #default="{ row }">{{ row.reference || row.range || '-' }}</template>
            </el-table-column>
            <el-table-column prop="flag" label="标记" width="100" />
          </el-table>
          <div v-if="reportAnalysis" class="answer-card">{{ reportAnalysis }}</div>
          <div v-if="!selectedReport" class="empty-state">请选择一份报告，系统会展示指标并调用 AI 分析异常可能原因、复查建议和就医科室。</div>
        </div>
      </section>

      <section v-if="activePage === 'appointment'" class="grid">
        <div class="panel">
          <h2>预约挂号</h2>
          <div v-if="appointmentInfo" class="appointment-success">
            <strong>预约成功</strong>
            <span>{{ appointmentInfo.department }} · {{ appointmentInfo.visit_date || appointmentInfo.date }} {{ appointmentInfo.period }} {{ appointmentInfo.time_slot }}</span>
            <span>{{ appointmentInfo.doctor }} · {{ appointmentInfo.doctor_title || appointmentInfo.title }}</span>
          </div>
          <div class="department-grid">
            <button
              v-for="dept in departments"
              :key="dept"
              :class="{ active: selectedDepartment === dept }"
              @click="chooseDepartment(dept)"
            >
              <span>{{ dept }}</span>
            </button>
          </div>
        </div>
        <div class="panel">
          <div class="panel-title">
            <h2>{{ selectedDepartment || '请选择科室' }} 排班号源</h2>
            <div class="panel-actions">
              <el-tag type="success">未来 7 天</el-tag>
              <el-button size="small" @click="loadAppointments">刷新预约</el-button>
            </div>
          </div>
          <div class="schedule-cards">
            <article v-for="row in schedule" :key="row.schedule_id" class="schedule-card">
              <div class="schedule-date">
                <strong>{{ row.visit_date || row.date }}</strong>
                <span>{{ row.weekday }} · {{ row.period }}</span>
              </div>
              <div class="doctor-line">
                <span class="doctor-avatar">{{ row.doctor?.slice(0, 1) }}</span>
                <div>
                  <strong>{{ row.doctor }}</strong>
                  <small>{{ row.doctor_title || row.title }} · {{ row.time_slot }}</small>
                </div>
              </div>
              <div class="slot-meta">
                <span>剩余 {{ row.remaining ?? row.quota }} / {{ row.quota }}</span>
                <span>挂号费 {{ row.fee }} 元</span>
              </div>
              <el-button
                type="primary"
                :disabled="isBooked(row) || (row.remaining ?? row.quota) <= 0"
                @click="book(row)"
              >
                {{ isBooked(row) ? '已预约' : ((row.remaining ?? row.quota) <= 0 ? '已约满' : '预约此号') }}
              </el-button>
            </article>
          </div>
        </div>
        <div class="panel appointment-panel">
          <div class="panel-title">
            <h2>我的预约</h2>
            <el-tag>{{ activeAppointments.length }} 个待就诊</el-tag>
          </div>
          <div v-if="appointments.length" class="appointment-list">
            <article v-for="item in appointments" :key="item.id" class="appointment-card" :class="{ cancelled: item.status === '已取消' }">
              <div>
                <strong>{{ item.department }} · {{ item.doctor }}</strong>
                <span>{{ item.doctor_title }} · {{ item.visit_date }} {{ item.period }} {{ item.time_slot }}</span>
                <small>预约单号：YL{{ String(item.id).padStart(6, '0') }} · {{ item.status }}</small>
              </div>
              <el-button
                v-if="item.status === '已预约'"
                size="small"
                type="danger"
                plain
                @click="cancelBooked(item)"
              >
                取消预约
              </el-button>
            </article>
          </div>
          <div v-else class="friendly-empty">暂无预约记录。你可以在左侧选择科室，然后预约多个不同日期或时间段的号源。</div>
        </div>
      </section>

      <section v-if="activePage === 'settings'" class="grid">
        <div class="panel">
          <h2>系统设置</h2>
          <div class="mini-grid">
            <div><span>远程模型</span><strong>{{ settings.llm_enabled ? '已启用' : '未启用' }}</strong></div>
            <div><span>API 地址</span><strong>{{ settings.base_url || '未配置' }}</strong></div>
            <div><span>联网检索</span><strong>默认开启</strong></div>
          </div>
          <div class="answer-card">
            API Key 和 Base URL 从 backend/config/config.yaml 读取。当前页面不会展示密钥明文，避免泄露。
          </div>
        </div>
        <div class="panel">
          <h2>数据管理</h2>
          <p class="muted">清空后会删除会话、消息和问诊记录，适合演示前重置数据。</p>
          <el-button type="danger" size="large" @click="clearSystemData">一键清空全部数据</el-button>
        </div>
      </section>

      <div class="footer-watermark">闲鱼：橙味Ayami，禁止二卖</div>

      <el-dialog v-model="recordDialogVisible" title="问诊记录详情" width="760px">
        <div v-if="selectedRecord" class="record-detail">
          <h3>主诉</h3>
          <p>{{ selectedRecord.chief_complaint || '-' }}</p>
          <h3>推荐科室</h3>
          <el-tag size="large" type="success">{{ selectedRecord.department || selectedRecord.recommended_department || '-' }}</el-tag>
          <h3>风险等级</h3>
          <el-tag size="large" type="warning">{{ selectedRecord.risk_level || '-' }}</el-tag>
          <h3>完整摘要</h3>
          <p>{{ selectedRecord.summary || '-' }}</p>
        </div>
      </el-dialog>
    </main>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, nextTick, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import OrchestratorSelector from './components/OrchestratorSelector.vue'
import OrchestratorMetrics from './components/OrchestratorMetrics.vue'
import {
  cancelAppointment,
  clearAllData,
  createAppointment,
  getAppointments,
  getDepartments,
  getMetrics,
  getRecords,
  getReports,
  getSchedule,
  getSettings,
  interpretReport,
  resumeLangGraph,
  runConsultationOrchestrated,
  runMedication,
  runTriage
} from './api/client'

const navItems = [
  { key: 'triage', label: '智能分诊台', icon: '◆' },
  { key: 'consultation', label: '线上问诊', icon: '●' },
  { key: 'medication', label: '用药咨询', icon: '■' },
  { key: 'records', label: '问诊记录', icon: '○' },
  { key: 'reports', label: '报告查询', icon: '▲' },
  { key: 'appointment', label: '预约挂号', icon: '◇' },
  { key: 'settings', label: '系统设置', icon: '⚙' }
]

const pageMap = {
  triage: ['智能分诊台', '输入症状与患者基础信息，输出风险分层、推荐科室和可追溯分诊依据。'],
  consultation: ['线上问诊', '面向连续对话的健康科普问诊，支持短期记忆、RAG 证据和联网增强。'],
  medication: ['用药咨询', '专门的药学 Agent，关注药物相互作用、禁忌提醒、特殊人群与就医边界。'],
  records: ['问诊记录', '查询近 7 天、30 天和半年内的分诊、问诊、用药记录。'],
  reports: ['报告查询', '展示检验检查报告，并使用 AI 解读异常原因、复查建议和推荐科室。'],
  appointment: ['预约挂号', '按科室查看未来 7 天上午/下午医生排班与剩余号源。'],
  settings: ['系统设置', '查看远程模型、联网检索和数据管理配置。']
}

const activePage = ref('triage')
const pageMeta = computed(() => {
  const [title, subtitle] = pageMap[activePage.value] || pageMap.triage
  return { title, subtitle }
})

const patient = ref({
  age: 26,
  gender: '男',
  chronic_diseases: '',
  allergy_history: '',
  medication_history: ''
})

const metrics = ref({})
const settings = ref({})
const records = ref([])
const reports = ref([])
const departments = ref([])
const schedule = ref([])
const appointments = ref([])
const selectedDepartment = ref('')
const selectedReport = ref(null)
const reportAnalysis = ref('')
const recordDays = ref(7)
const selectedRecord = ref(null)
const recordDialogVisible = ref(false)
const appointmentInfo = ref(null)
const activeAppointments = computed(() => appointments.value.filter(item => item.status === '已预约'))

const triageText = ref('')
const triageResult = ref(null)
const triageLoading = ref(false)

const consultText = ref('')
const consultResult = ref(null)
const consultLoading = ref(false)
const consultMetrics = ref({})
const orchestratorMode = ref('swarm')
const consultSessionId = ref(null)
const pendingInterrupt = ref(false)
const chatBox = ref(null)
const messages = ref([
  {
    role: 'assistant',
    content: '您好，我是医路通 AI。请描述症状、持续时间、年龄和既往病史，我会结合本地知识库、联网证据和安全规则给出健康科普建议。'
  }
])

const medicationText = ref('')
const medicationResult = ref(null)
const medicationLoading = ref(false)
const reportLoading = ref(false)

const consultLoadingHint = computed(() => {
  const map = {
    swarm: 'Swarm 多 Agent 正在结合 RAG 与联网证据推理…',
    langgraph: 'LangGraph 状态机执行中…',
    dify: 'Dify 云端工作流执行中（约 1–2 分钟，请稍候）…'
  }
  return map[orchestratorMode.value] || map.swarm
})

const ResultPanel = defineComponent({
  props: {
    result: { type: Object, required: true },
    bannerLabel: { type: String, default: '推荐科室' }
  },
  setup(props) {
    return () => h('div', { class: 'result-wrap' }, [
      h('div', { class: 'department-banner' }, [
        h('span', props.bannerLabel),
        h('strong', props.result.recommended_department || '内科')
      ]),
      h('div', { class: 'mini-grid' }, [
        h('div', [h('span', '风险等级'), h('strong', props.result.risk_level || '待评估')]),
        h('div', [h('span', '证据数量'), h('strong', evidenceCount(props.result))]),
        h('div', [h('span', 'Agent 步骤'), h('strong', traceCount(props.result))])
      ]),
      h('div', { class: 'answer-card' }, props.result.answer)
    ])
  }
})

const InsightPanel = defineComponent({
  props: {
    title: { type: String, required: true },
    result: { type: Object, default: null }
  },
  setup(props) {
    return () => h('div', { class: 'panel' }, [
      h('h2', props.title),
      props.result
        ? h('div', [
            h('h3', 'AI 思考过程'),
            ...(props.result.thinking_steps || props.result.agent_trace || []).map((step) => {
              const item = typeof step === 'string' ? { agent: 'Thinking', detail: step } : step
              return h('div', { class: 'trace-item' }, [
                h('strong', item.agent || item.name || 'Agent'),
                h('small', item.action || item.role || ''),
                h('span', item.observation || item.detail || item.content || '')
              ])
            }),
            h('h3', '证据引用'),
            h('div', { class: 'evidence' }, (props.result.evidence || []).map((item, index) =>
              h('div', { class: 'evidence-item' }, [
                h('strong', `#${index + 1} ${item.title || item.source || '证据'}`),
                h('small', `${item.source || ''} · ${item.score ?? ''}`),
                h('p', item.content || item.snippet || '')
              ])
            ))
          ])
        : h('div', { class: 'empty-state' }, '提交后会展示 Agent 路由、RAG 检索、联网增强、安全审查和引用证据。')
    ])
  }
})

function buildPayload(text, scene) {
  return {
    message: text,
    scene,
    patient_context: { ...patient.value },
    enable_deep_search: true
  }
}

function withKey(result) {
  return { ...(result || {}), _key: Date.now() }
}

async function submitTriage() {
  if (!triageText.value.trim()) {
    ElMessage.warning('请先填写症状描述')
    return
  }
  triageLoading.value = true
  triageResult.value = null
  try {
    const result = await runTriage(buildPayload(triageText.value, 'triage'))
    triageResult.value = withKey(result)
    await refreshAfterAction()
  } catch (error) {
    ElMessage.error(error?.message || '分诊请求失败')
  } finally {
    triageLoading.value = false
  }
}

async function submitConsultation() {
  if (!consultText.value.trim()) {
    ElMessage.warning('请输入问诊内容')
    return
  }
  if (pendingInterrupt.value) {
    ElMessage.warning('请先确认或取消高风险提醒')
    return
  }
  const userText = consultText.value
  messages.value.push({ role: 'user', content: userText })
  consultText.value = ''
  consultLoading.value = true
  await scrollChat()
  try {
    const result = await runConsultationOrchestrated({
      ...buildPayload(userText, 'consultation'),
      orchestrator: orchestratorMode.value,
      session_id: consultSessionId.value || undefined
    })
    consultSessionId.value = result.session_id
    consultResult.value = withKey(result)
    consultMetrics.value = {
      ...(result.metrics || {}),
      orchestrator: result.metrics?.orchestrator || orchestratorMode.value
    }

    if (result.metrics?.interrupted) {
      pendingInterrupt.value = true
      messages.value.push({
        role: 'assistant',
        content: result.answer || '检测到高风险症状，请确认已了解需立即就医。'
      })
    } else {
      messages.value.push({
        role: 'assistant',
        content: result.answer || '已完成分析，请结合医生意见判断。'
      })
    }
    await refreshAfterAction()
  } catch (error) {
    messages.value.push({ role: 'assistant', content: `请求失败：${error?.message || '问诊请求失败'}` })
    consultMetrics.value = {}
  } finally {
    consultLoading.value = false
    await scrollChat()
  }
}

async function confirmInterrupt(confirmed) {
  if (!consultSessionId.value) return
  consultLoading.value = true
  try {
    const result = await resumeLangGraph(consultSessionId.value, confirmed)
    consultResult.value = withKey(result)
    consultMetrics.value = {
      ...(result.metrics || {}),
      orchestrator: result.metrics?.orchestrator || orchestratorMode.value
    }
    pendingInterrupt.value = Boolean(result.metrics?.interrupted)
    if (result.answer) {
      messages.value.push({ role: 'assistant', content: result.answer })
    }
  } catch (error) {
    ElMessage.error(error?.message || '确认失败')
  } finally {
    consultLoading.value = false
    pendingInterrupt.value = false
    await scrollChat()
  }
}

async function submitMedication() {
  if (!medicationText.value.trim()) {
    ElMessage.warning('请输入用药问题')
    return
  }
  medicationLoading.value = true
  medicationResult.value = null
  try {
    const result = await runMedication(buildPayload(medicationText.value, 'medication'))
    medicationResult.value = withKey(result)
    await refreshAfterAction()
  } catch (error) {
    ElMessage.error(error?.message || '用药咨询失败')
  } finally {
    medicationLoading.value = false
  }
}

async function refreshAfterAction() {
  await Promise.all([loadRecords(), loadMetrics(), loadAppointments()])
}

async function scrollChat() {
  await nextTick()
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
}

async function loadRecords() {
  records.value = await getRecords(recordDays.value)
}

async function loadMetrics() {
  metrics.value = await getMetrics()
}

async function loadReports() {
  reports.value = await getReports()
  if (!selectedReport.value && reports.value.length) selectedReport.value = reports.value[0]
}

async function loadDepartments() {
  departments.value = await getDepartments()
  selectedDepartment.value = departments.value[0] || ''
  if (selectedDepartment.value) await chooseDepartment(selectedDepartment.value)
}

async function loadSettings() {
  settings.value = await getSettings()
}

async function chooseDepartment(department) {
  selectedDepartment.value = department
  const data = await getSchedule(department)
  schedule.value = data.schedule || []
}

async function loadAppointments() {
  appointments.value = await getAppointments()
  if (selectedDepartment.value) {
    const data = await getSchedule(selectedDepartment.value)
    schedule.value = data.schedule || []
  }
}

function scheduleKey(row) {
  return row.schedule_id || `${selectedDepartment.value}|${row.doctor}|${row.visit_date || row.date}|${row.period}|${row.time_slot}`
}

function appointmentKey(item) {
  return `${item.department}|${item.doctor}|${item.visit_date}|${item.period}|${item.time_slot}`
}

function isBooked(row) {
  const key = scheduleKey(row)
  return activeAppointments.value.some(item => appointmentKey(item) === key)
}

async function book(row) {
  if (isBooked(row)) {
    ElMessage.info('这个医生的当前时间段已经预约过了，可以选择其他时间段继续预约')
    return
  }
  const payload = { department: selectedDepartment.value, ...row }
  const data = await createAppointment(payload)
  appointmentInfo.value = { ...payload, appointment_id: data.appointment_id }
  appointments.value = data.appointments || await getAppointments()
  await chooseDepartment(selectedDepartment.value)
  ElMessage.success(`预约成功：${selectedDepartment.value} ${row.visit_date || row.date} ${row.period}`)
}

async function cancelBooked(item) {
  await ElMessageBox.confirm(`确认取消 ${item.department} ${item.visit_date} ${item.period} 的预约吗？`, '取消预约', {
    type: 'warning',
    confirmButtonText: '确认取消',
    cancelButtonText: '保留预约'
  })
  const data = await cancelAppointment(item.id)
  appointments.value = data.appointments || await getAppointments()
  await chooseDepartment(selectedDepartment.value)
  ElMessage.success('预约已取消')
}

function selectReport(report) {
  selectedReport.value = report
  reportAnalysis.value = ''
}

async function loadReportAnalysis() {
  if (!selectedReport.value) return
  reportLoading.value = true
  try {
    const data = await interpretReport(selectedReport.value.id)
    reportAnalysis.value = data.analysis || data.interpretation || data.answer || '暂无解读'
  } finally {
    reportLoading.value = false
  }
}

function openRecord(record) {
  selectedRecord.value = record
  recordDialogVisible.value = true
}

function goRecords() {
  activePage.value = 'records'
  loadRecords()
}

async function clearSystemData() {
  await ElMessageBox.confirm('确认清空所有会话、消息和问诊记录吗？此操作不可恢复。', '一键清空', {
    type: 'warning',
    confirmButtonText: '确认清空',
    cancelButtonText: '取消'
  })
  await clearAllData()
  triageResult.value = null
  consultResult.value = null
  consultMetrics.value = {}
  consultSessionId.value = null
  pendingInterrupt.value = false
  medicationResult.value = null
  appointmentInfo.value = null
  appointments.value = []
  records.value = []
  messages.value = [messages.value[0]]
  await refreshAfterAction()
  ElMessage.success('数据已清空')
}

function evidenceCount(result) {
  return (result?.evidence || []).length
}

function traceCount(result) {
  return (result?.agent_trace || result?.thinking_steps || []).length
}

function shortText(text = '') {
  return text.length > 72 ? `${text.slice(0, 72)}...` : text
}

function sceneLabel(scene) {
  const map = { triage: '分诊', consultation: '问诊', medication: '用药' }
  return map[scene] || scene || '记录'
}

function formatTime(value) {
  if (!value) return '-'
  return String(value).replace('T', ' ').slice(0, 16)
}

onMounted(async () => {
  await Promise.all([loadMetrics(), loadRecords(), loadReports(), loadDepartments(), loadSettings(), loadAppointments()])
})
</script>
