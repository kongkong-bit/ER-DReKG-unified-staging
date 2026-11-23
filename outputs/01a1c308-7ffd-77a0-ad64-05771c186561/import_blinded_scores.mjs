import fs from 'node:fs/promises';
import path from 'node:path';
import { FileBlob, SpreadsheetFile, Workbook } from 'file:///C:/Program%20Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1112-737-0_26.1112.737.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';

const root = 'D:/CLASS/syh';
const outDir = path.join(root, 'outputs/01a1c308-7ffd-77a0-ad64-05771c186561');
const sourceCsv = path.join(root, 'experiments/kg07_mechanism_interpretation/kg07_human_review_20_cases.csv');
const workbookPath = path.resolve(process.argv[2] ?? path.join(outDir, 'kg07_human_review.xlsx'));
const apply = process.argv.includes('--apply');
const force = process.argv.includes('--force');
const scoredCsvPath = path.join(root, 'experiments/kg07_mechanism_interpretation/kg07_human_review_20_cases_scored.csv');
const criterionMap = new Map([
  ['支持声明比例', 'supported_claim_fraction'],
  ['引用准确率', 'citation_precision'],
  ['无依据断言数', 'unsupported_assertion_count'],
  ['关系方向错误数', 'relation_direction_error_count'],
  ['不确定性判断准确率', 'uncertainty_accuracy'],
  ['审阅备注', 'review_notes'],
]);
const identityHeaders = ['病例', '药物ID', '药物', '盲审代码'];

function clean(value) {
  if (value === null || value === undefined) return '';
  return String(value).trim();
}

function key(caseId, code) {
  return `${clean(caseId)}\u0000${clean(code)}`;
}

function quoteCsv(value) {
  const text = value === null || value === undefined ? '' : String(value);
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function checkScore(field, value, label) {
  const raw = clean(value);
  if (!raw) return 'blank';
  if (raw.toUpperCase() === 'NA') {
    if (field.endsWith('_count')) throw new Error(`${label}: count fields cannot be NA`);
    return 'ok';
  }
  const n = Number(raw);
  if (!Number.isFinite(n)) throw new Error(`${label}: expected a number${field.endsWith('_count') ? '' : ' or NA'}`);
  if (field.endsWith('_count')) {
    if (!Number.isInteger(n) || n < 0) throw new Error(`${label}: expected a nonnegative integer`);
  } else if (n < 0 || n > 1) {
    throw new Error(`${label}: expected a number from 0 to 1`);
  }
  return 'ok';
}

const xlsxBlob = await FileBlob.load(workbookPath);
const workbook = await SpreadsheetFile.importXlsx(xlsxBlob);
const scoreValues = workbook.worksheets.getItem('评分表').getUsedRange().values;
if (scoreValues.length !== 61) throw new Error(`评分表应为 61 行（含表头），实际为 ${scoreValues.length}`);
const scoreHeaders = scoreValues[0].map(clean);
const headerIndex = new Map(scoreHeaders.map((header, index) => [header, index]));
for (const header of [...identityHeaders, ...criterionMap.keys()]) {
  if (!headerIndex.has(header)) throw new Error(`评分表缺少列：${header}`);
}
const headerText = scoreHeaders.join('|');
if (/method|output_path|blinding_key|reviewer_method/i.test(headerText)) {
  throw new Error('评分表含方法揭盲或原始输出路径字段；拒绝导入');
}

const rawCsv = await fs.readFile(sourceCsv, 'utf8');
const sourceBook = await Workbook.fromCSV(rawCsv, { sheetName: 'Source' });
const sourceValues = sourceBook.worksheets.getItem('Source').getUsedRange().values;
const sourceHeaders = sourceValues[0].map((v) => clean(v).replace(/^\uFEFF/, ''));
const sourceRows = sourceValues.slice(1);
if (sourceRows.length !== 60) throw new Error(`原始盲审 CSV 应为 60 行，实际为 ${sourceRows.length}`);
const sourceIndex = new Map(sourceHeaders.map((header, index) => [header, index]));
for (const field of [...criterionMap.values()]) if (!sourceIndex.has(field)) throw new Error(`原始 CSV 缺少列：${field}`);

const sourceByKey = new Map();
for (const row of sourceRows) {
  const k = key(row[sourceIndex.get('case')], row[sourceIndex.get('review_code')]);
  if (sourceByKey.has(k)) throw new Error(`原始 CSV 有重复病例/盲审代码：${k.replace('\u0000', '/')}`);
  sourceByKey.set(k, row);
}
if (sourceByKey.size !== 60) throw new Error('原始 CSV 身份键不完整');

let blankCount = 0;
const imported = [];
const seen = new Set();
for (const row of scoreValues.slice(1)) {
  const caseId = clean(row[headerIndex.get('病例')]);
  const pertId = clean(row[headerIndex.get('药物ID')]);
  const drugName = clean(row[headerIndex.get('药物')]);
  const code = clean(row[headerIndex.get('盲审代码')]);
  const k = key(caseId, code);
  const sourceRow = sourceByKey.get(k);
  if (!sourceRow || seen.has(k)) throw new Error(`评分工作簿的病例/代码缺失或重复：${caseId}/${code}`);
  seen.add(k);
  if (clean(sourceRow[sourceIndex.get('pert_id')]) !== pertId || clean(sourceRow[sourceIndex.get('drug_name')]) !== drugName) {
    throw new Error(`评分工作簿身份字段与原始 CSV 不一致：${caseId}/${code}`);
  }
  const scores = {};
  for (const [displayName, field] of criterionMap) {
    const value = row[headerIndex.get(displayName)];
    const state = checkScore(field, value, `${caseId}/${code}/${displayName}`);
    if (state === 'blank' && field !== 'review_notes') blankCount++;
    scores[field] = clean(value);
  }
  imported.push({ k, scores });
}
if (seen.size !== 60) throw new Error(`工作簿应覆盖 60 条记录，实际匹配 ${seen.size}`);

const sourceRowsWithScores = sourceRows.map((row) => [...row]);
for (const { k, scores } of imported) {
  const row = sourceByKey.get(k);
  const idx = sourceRows.indexOf(row);
  for (const [field, value] of Object.entries(scores)) row[sourceIndex.get(field)] = value;
  sourceRowsWithScores[idx] = row;
}

if (apply && blankCount > 0) throw new Error(`仍有 ${blankCount} 个必填评分为空；未写文件`);
if (apply && !force) {
  try {
    await fs.access(scoredCsvPath);
    throw new Error(`目标文件已存在：${scoredCsvPath}。检查后添加 --force 才可覆盖`);
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
}

const csvOutput = [sourceHeaders, ...sourceRowsWithScores]
  .map((row) => row.map(quoteCsv).join(','))
  .join('\r\n') + '\r\n';
if (apply) {
  await fs.writeFile(scoredCsvPath, `\uFEFF${csvOutput}`, 'utf8');
}
console.log(JSON.stringify({
  status: blankCount ? 'HUMAN_REVIEW_PENDING' : 'HUMAN_REVIEW_READY_TO_SCORE',
  workbook: workbookPath,
  matchedRows: seen.size,
  blankRequiredScoreCells: blankCount,
  mode: apply ? 'applied_to_separate_scored_csv' : 'dry_run_no_files_written',
  scoredCsv: apply ? scoredCsvPath : null,
}, null, 2));
