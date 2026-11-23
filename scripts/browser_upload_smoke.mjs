#!/usr/bin/env node
// Real Chromium-based UI upload smoke test using installed Microsoft Edge + CDP.
// Uses a synthetic CSV and requires an existing test_only project.
import { spawn } from 'node:child_process'
import { createServer } from 'node:net'
import { existsSync } from 'node:fs'
import { mkdtemp, rm, writeFile } from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'

const projectId = process.argv[2]
if (!projectId) throw new Error('usage: node scripts/browser_upload_smoke.mjs <test_only-project-id>')
if (typeof WebSocket === 'undefined') throw new Error('Node.js 21+ is required for the built-in WebSocket client')
const origin = process.env.APP_ORIGIN ?? 'http://127.0.0.1:5173'
const edgePath = process.env.EDGE_PATH ?? [
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
].find((candidate) => {
  try { return existsSync(candidate) } catch { return false }
})
if (!edgePath) throw new Error('Microsoft Edge not found; set EDGE_PATH')

const tempRoot = os.tmpdir()
const profile = await mkdtemp(path.join(tempRoot, 'DiseaseGraphUploadE2E-'))
const fixturePath = path.join(profile, 'synthetic_deg.csv')
const fixtureContent = 'gene_symbol,logFC,adj.P.Val,t\nE2E_SYNTHETIC_GENE,1.2,0.01,3.5\n'
await writeFile(fixturePath, fixtureContent, 'utf8')

const portServer = createServer()
await new Promise((resolve, reject) => portServer.listen(0, '127.0.0.1', resolve).once('error', reject))
const port = portServer.address().port
await new Promise((resolve) => portServer.close(resolve))

let browser
let ws
let childOutput = ''
let session
const result = { project_id: projectId, app_origin: origin, status: 'FAIL' }

async function poll(fn, label, timeoutMs = 15000) {
  const end = Date.now() + timeoutMs
  let last
  while (Date.now() < end) {
    try {
      last = await fn()
      if (last) return last
    } catch (error) { last = error }
    await new Promise((resolve) => setTimeout(resolve, 250))
  }
  throw new Error(`timed out waiting for ${label}: ${String(last)}`)
}

async function cdp(method, params = {}) {
  if (!ws || ws.readyState !== WebSocket.OPEN) throw new Error('CDP socket is not open')
  const id = ++session.seq
  return await new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      session.pending.delete(id)
      reject(new Error(`CDP timeout: ${method}`))
    }, 10000)
    session.pending.set(id, (message) => {
      clearTimeout(timer)
      if (message.error) reject(new Error(`${method}: ${message.error.message}`))
      else resolve(message.result)
    })
    ws.send(JSON.stringify({ id, method, params }))
  })
}

async function evaluate(expression) {
  const response = await cdp('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })
  if (response.exceptionDetails) throw new Error(response.exceptionDetails.text ?? 'page evaluation failed')
  return response.result?.value
}

try {
  const projectResponse = await fetch(`${origin}/api/v1/projects/${projectId}`)
  if (!projectResponse.ok) throw new Error(`project API returned ${projectResponse.status}`)
  const project = await projectResponse.json()
  if (project.status !== 'test_only') throw new Error(`refusing non-test project: ${project.status}`)
  result.project_slug = project.slug

  const beforeDatasets = await (await fetch(`${origin}/api/v1/projects/${projectId}/datasets`)).json()
  const beforeRuns = await (await fetch(`${origin}/api/v1/projects/${projectId}/runs`)).json()
  if (beforeDatasets.items.some((row) => row.filename === 'synthetic_deg.csv')) {
    throw new Error('synthetic_deg.csv already exists for this test project; use a fresh test_only project to avoid duplicate uploads')
  }
  result.datasets_before = beforeDatasets.items.length
  result.runs_before = beforeRuns.length

  browser = spawn(edgePath, [
    '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
    `--remote-debugging-port=${port}`, '--remote-allow-origins=*', `--user-data-dir=${profile}`, `${origin}/`,
  ], { windowsHide: true, stdio: ['ignore', 'ignore', 'pipe'] })
  browser.stderr.on('data', (chunk) => { childOutput = (childOutput + chunk.toString()).slice(-4000) })

  await poll(async () => {
    const response = await fetch(`http://127.0.0.1:${port}/json/version`)
    if (!response.ok) return false
    return response.json()
  }, 'Edge DevTools endpoint')
  const targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json()
  const page = targets.find((target) => target.type === 'page' && target.url.startsWith(origin))
  if (!page) throw new Error('DiseaseGraph page was not opened')
  ws = new WebSocket(page.webSocketDebuggerUrl)
  session = { seq: 0, pending: new Map() }
  ws.addEventListener('message', (event) => {
    const message = JSON.parse(event.data)
    if (message.id && session.pending.has(message.id)) {
      session.pending.get(message.id)(message)
      session.pending.delete(message.id)
    }
  })
  await new Promise((resolve, reject) => {
    ws.addEventListener('open', resolve, { once: true })
    ws.addEventListener('error', reject, { once: true })
  })
  await cdp('Runtime.enable')
  await poll(async () => evaluate("document.querySelector('#active-project')?.options?.length > 0"), 'project selector')

  const selected = await evaluate(`(() => {
    const select = document.querySelector('#active-project');
    const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set;
    setter.call(select, ${JSON.stringify(projectId)});
    select.dispatchEvent(new Event('change', { bubbles: true }));
    return select.value;
  })()`)
  if (selected !== projectId) throw new Error('failed to select test project')
  await poll(async () => evaluate(`document.body.innerText.includes(${JSON.stringify(project.name)}) && document.body.innerText.includes('test_only')`), 'test project dashboard')

  const opened = await evaluate(`(() => {
    const button = [...document.querySelectorAll('button')].find((item) => item.innerText.trim() === '上传数据');
    if (!button) return false;
    button.click(); return true;
  })()`)
  if (!opened) throw new Error('upload dialog button not found')
  await poll(async () => evaluate("!!document.querySelector('#dataset-file') && [...document.querySelectorAll('.ant-modal')].some(x=>x.getClientRects().length)"), 'upload dialog')

  const typeOpened = await evaluate(`(() => {
    const root = document.querySelector('#dataset-type')?.closest('.ant-select') ?? [...document.querySelectorAll('.ant-select')].find(x=>x.innerText.includes('表达矩阵'));
    if (!root) return false;
    const selector=root.querySelector('.ant-select-content') ?? root.querySelector('.ant-select-input');
    if (!selector) return false;
    selector.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,button:0,view:window}));
    return true;
  })()`)
  if (!typeOpened) throw new Error('dataset type selector not found')
  await poll(async () => evaluate("[...document.querySelectorAll('.ant-select-item-option-content')].some(x=>x.innerText.trim()==='已计算差异表达结果')"), 'precomputed DEG option')
  const optionSelected = await evaluate(`(() => {
    const option = [...document.querySelectorAll('.ant-select-item-option-content')].find(x=>x.innerText.trim()==='已计算差异表达结果');
    option?.click(); return !!option;
  })()`)
  if (!optionSelected) throw new Error('precomputed DEG option could not be selected')

  const { root } = await cdp('DOM.getDocument', { depth: -1, pierce: true })
  const input = await cdp('DOM.querySelector', { nodeId: root.nodeId, selector: '#dataset-file' })
  if (!input.nodeId) throw new Error('file input not found in DOM')
  await cdp('DOM.setFileInputFiles', { nodeId: input.nodeId, files: [fixturePath] })
  await evaluate(`(() => { const input=document.querySelector('#dataset-file'); input.dispatchEvent(new Event('input',{bubbles:true})); input.dispatchEvent(new Event('change',{bubbles:true})); })()`)
  await poll(async () => evaluate("document.querySelector('.upload-selection')?.innerText.includes('synthetic_deg.csv')"), 'selected file label')
  result.file_input_label = await evaluate("document.querySelector('#dataset-file')?.getAttribute('aria-label')")
  result.dataset_type = await evaluate("[...document.querySelectorAll('.ant-select')].find(x=>x.innerText.includes('已计算差异表达结果'))?.innerText.trim()")

  const submit = await evaluate(`(() => {
    const modal=[...document.querySelectorAll('.ant-modal')].find(x=>x.getClientRects().length);
    const button=[...(modal?.querySelectorAll('button')??[])].find(x=>x.innerText.trim()==='上传并校验');
    if (!button || button.disabled) return false;
    button.click(); return true;
  })()`)
  if (!submit) throw new Error('upload submit button unavailable')
  const after = await poll(async () => {
    const response = await fetch(`${origin}/api/v1/projects/${projectId}/datasets`)
    if (!response.ok) return false
    const data = await response.json()
    if (data.items.length <= beforeDatasets.items.length) return false
    const item = data.items.find((row) => row.filename === 'synthetic_deg.csv')
    return item ? { data, item } : false
  }, 'uploaded dataset registration', 20000)
  const afterRuns = await (await fetch(`${origin}/api/v1/projects/${projectId}/runs`)).json()
  if (after.item.state !== 'validation_pending') throw new Error(`unexpected dataset state: ${after.item.state}`)
  if (after.item.validation?.dataset_type !== 'precomputed_deg') throw new Error('dataset type was not persisted as precomputed_deg')
  if (afterRuns.length !== beforeRuns.length) throw new Error('upload unexpectedly created an AnalysisRun')
  const successMessage = await poll(async () => evaluate("document.body.innerText.includes('文件已登记，状态 validation_pending')"), 'success toast')
  result.dataset_id = after.item.dataset_id
  result.dataset_state = after.item.state
  result.dataset_type_persisted = after.item.validation.dataset_type
  result.sha256 = after.item.sha256
  result.analysis_runs_after = afterRuns.length
  result.analysis_started = false
  result.ui_success_message = Boolean(successMessage)
  result.status = 'PASS'
} catch (error) {
  result.error = String(error?.stack ?? error)
  if (ws?.readyState === WebSocket.OPEN) {
    try {
      result.page_diagnostics = await evaluate(`JSON.stringify({body:document.body.innerText.slice(-1600),selects:[...document.querySelectorAll('.ant-select')].map(x=>({id:x.id,text:x.innerText.trim(),expanded:x.querySelector('[aria-expanded]')?.getAttribute('aria-expanded'),html:x.outerHTML.slice(0,1200)})),options:[...document.querySelectorAll('[role=option],.ant-select-item-option-content')].map(x=>x.innerText.trim()).slice(0,30)})`)
    } catch {}
  }
  if (childOutput) result.edge_stderr_tail = childOutput
  process.exitCode = 1
} finally {
  if (ws?.readyState === WebSocket.OPEN) {
    try { await cdp('Browser.close') } catch {}
    ws.close()
  }
  if (browser && browser.exitCode === null) {
    await Promise.race([
      new Promise((resolve) => browser.once('exit', resolve)),
      new Promise((resolve) => setTimeout(resolve, 5000)),
    ])
    if (browser.exitCode === null) browser.kill()
  }
  const resolvedProfile = path.resolve(profile)
  if (path.dirname(resolvedProfile) !== path.resolve(tempRoot) || !path.basename(resolvedProfile).startsWith('DiseaseGraphUploadE2E-')) {
    throw new Error('refusing to remove unexpected browser profile path')
  }
  await rm(resolvedProfile, { recursive: true, force: true })
  console.log(JSON.stringify(result, null, 2))
}
