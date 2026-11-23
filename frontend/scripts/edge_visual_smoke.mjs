import { spawn } from 'node:child_process'
import { setTimeout as delay } from 'node:timers/promises'
import { mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'

const baseUrl = process.env.DG_FRONTEND_URL ?? 'http://127.0.0.1:5175'
const edge = process.env.EDGE_PATH ?? 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
const profile = path.join(process.env.TEMP ?? process.cwd(), 'diseasegraph-visual-smoke')
const output = path.resolve('screenshots')
const projectId = '3f18f4c1-713d-58c5-8a53-38eca5a5aaf9'
const routes = [
  ['dashboard', '/', 'ER 阳性乳腺癌药物重定位'],
  ['s1', '/s1', '疾病表达特征'],
  ['s2', '/s2', '候选药物综合证据'],
  ['graph', '/graph', '局部证据子图'],
  ['drug-details', '/drugs', '药物详情'],
  ['reliability', '/compare', '可靠性分析'],
  ['final-results', '/final-results', 'ER 阳性乳腺癌 Top 10 候选药物'],
]

await mkdir(output, { recursive: true })
const browser = spawn(edge, [
  '--headless=new', '--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage',
  '--remote-allow-origins=*', '--remote-debugging-port=9222', `--user-data-dir=${profile}`,
  '--window-size=1440,1100', 'about:blank',
], { stdio: 'ignore', windowsHide: true })

let socket
try {
  let target
  for (let i = 0; i < 40; i++) {
    try {
      const response = await fetch('http://127.0.0.1:9222/json')
      target = (await response.json()).find((item) => item.type === 'page')
      if (target) break
    } catch {}
    await delay(250)
  }
  if (!target) throw new Error('Edge DevTools 页面未启动')
  socket = new WebSocket(target.webSocketDebuggerUrl)
  await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject })
  let nextId = 0
  const pending = new Map()
  socket.onmessage = (event) => {
    const message = JSON.parse(event.data)
    if (message.id && pending.has(message.id)) {
      const { resolve, reject } = pending.get(message.id)
      pending.delete(message.id)
      message.error ? reject(new Error(message.error.message)) : resolve(message.result)
    }
  }
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++nextId
    pending.set(id, { resolve, reject })
    socket.send(JSON.stringify({ id, method, params }))
  })
  const evaluate = async (expression, awaitPromise = true) => {
    const result = await send('Runtime.evaluate', { expression, awaitPromise, returnByValue: true })
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.text)
    return result.result.value
  }
  await send('Page.enable')
  await send('Runtime.enable')
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false })

  const results = []
  for (const [name, route, expected] of routes) {
    await send('Page.navigate', { url: `${baseUrl}${route}` })
    await delay(1800)
    await evaluate('window.scrollTo(0, 0)')
    const selected = await evaluate(`(() => { const el=document.querySelector('#active-project'); if(!el) return false; const setter=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set; setter.call(el, '${projectId}'); el.dispatchEvent(new Event('change',{bubbles:true})); return el.value === '${projectId}'; })()`)
    await delay(1200)
    const text = await evaluate('document.body.innerText')
    const hasExpectedHeading = text.includes(expected)
    const layout = name === 'graph' ? await evaluate(`(() => { const grid=document.querySelector('.graph-workspace'); const canvas=document.querySelector('.graph-card canvas'); return { columns:grid ? getComputedStyle(grid).gridTemplateColumns.split(' ').length : 0, canvasReady:!!canvas }; })()`) : undefined
    const screenshot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false })
    await writeFile(path.join(output, `${name}.png`), Buffer.from(screenshot.data, 'base64'))
    results.push({ route, projectSelected: selected, expectedText: expected, hasExpectedHeading, ...(layout ? { graphWorkspace: layout } : {}), screenshot: `${name}.png` })
    if (name === 'graph') {
      await evaluate("document.querySelector('.graph-workspace')?.scrollIntoView({block:'start'})")
      await delay(350)
      const workspaceShot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false })
      await writeFile(path.join(output, 'graph-workspace.png'), Buffer.from(workspaceShot.data, 'base64'))
    }
  }

  await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] })
  const reducedMotion = await evaluate("(() => { const node=document.querySelector('.route-view'); return node ? parseFloat(getComputedStyle(node).animationDuration) <= 0.0001 : false; })()")
  results.push({ accessibilityCheck: 'prefers-reduced-motion', passed: reducedMotion })
  await send('Emulation.setEmulatedMedia', { features: [] })

  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true })
  await send('Page.navigate', { url: `${baseUrl}/` })
  await delay(1000)
  await evaluate(`(() => { const el=document.querySelector('#active-project'); const setter=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set; setter.call(el, '${projectId}'); el.dispatchEvent(new Event('change',{bubbles:true})); document.querySelector('[aria-label="打开导航菜单"]')?.click(); return true; })()`)
  await delay(400)
  const mobileNoOverflow = await evaluate('document.documentElement.scrollWidth <= innerWidth')
  const mobile = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false })
  await writeFile(path.join(output, 'mobile-navigation.png'), Buffer.from(mobile.data, 'base64'))
  results.push({ route: '/', viewport: '390×844', menuOpened: true, noHorizontalOverflow: mobileNoOverflow, screenshot: 'mobile-navigation.png' })
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false })
  await send('Page.navigate', { url: `${baseUrl}/` })
  await delay(1000)
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9, nativeVirtualKeyCode: 9 })
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9, nativeVirtualKeyCode: 9 })
  const keyboardFocus = await evaluate("(() => { const el=document.activeElement; return !!el && el.matches(':focus-visible') && getComputedStyle(el).outlineStyle !== 'none'; })()")
  results.push({ accessibilityCheck: 'keyboard-visible-focus', passed: keyboardFocus })
  console.log(JSON.stringify({ results }, null, 2))
  const graph = results.find((item) => item.route === '/graph')
  if (results.slice(0, routes.length).some((item) => !item.projectSelected || !item.hasExpectedHeading) || graph?.graphWorkspace?.columns !== 3 || graph?.graphWorkspace?.canvasReady !== true || !mobileNoOverflow || !reducedMotion || !keyboardFocus) process.exitCode = 1
} finally {
  socket?.close()
  browser.kill()
}
