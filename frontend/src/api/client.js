import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8012',
  timeout: 180000
})

export async function sendChat(payload) {
  const { data } = await api.post('/api/chat', payload)
  return data
}

export async function runTriage(payload) {
  const { data } = await api.post('/api/triage', payload)
  return data
}

export async function runConsultation(payload) {
  const { data } = await api.post('/api/consultation', payload)
  return data
}

/** 阶段 2：统一编排路由（Swarm / LangGraph / Dify） */
export async function runConsultationOrchestrated(payload) {
  const mode = payload.orchestrator || 'swarm'
  const endpoints = {
    swarm: '/api/chat',
    langgraph: '/api/chat/langgraph',
    dify: '/api/chat/dify'
  }
  const { data } = await api.post(endpoints[mode] || '/api/chat/route', payload)
  return data
}

export async function resumeLangGraph(sessionId, confirmed = true) {
  const { data } = await api.post('/api/chat/langgraph/resume', {
    session_id: sessionId,
    confirmed
  })
  return data
}

export async function runMedication(payload) {
  const { data } = await api.post('/api/medication', payload)
  return data
}

export async function getRecords(days = 7) {
  const { data } = await api.get('/api/records', { params: { days } })
  return data.records
}

export async function getReports() {
  const { data } = await api.get('/api/reports')
  return data.reports
}

export async function interpretReport(reportId) {
  const { data } = await api.get(`/api/reports/${reportId}/interpret`)
  return data
}

export async function getDepartments() {
  const { data } = await api.get('/api/departments')
  return data.departments
}

export async function getSchedule(department) {
  const { data } = await api.get('/api/appointments/schedule', { params: { department } })
  return data
}

export async function createAppointment(payload) {
  const { data } = await api.post('/api/appointments', payload)
  return data
}

export async function getAppointments() {
  const { data } = await api.get('/api/appointments')
  return data.appointments
}

export async function cancelAppointment(appointmentId) {
  const { data } = await api.delete(`/api/appointments/${appointmentId}`)
  return data
}

export async function getMetrics() {
  const { data } = await api.get('/api/metrics')
  return data
}

export async function getSessions() {
  const { data } = await api.get('/api/sessions')
  return data.sessions
}

export async function getSettings() {
  const { data } = await api.get('/api/settings')
  return data
}

export async function clearAllData() {
  const { data } = await api.delete('/api/sessions')
  return data
}
