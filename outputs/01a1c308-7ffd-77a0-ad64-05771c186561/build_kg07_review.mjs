import fs from 'node:fs/promises';
import path from 'node:path';
import { FileBlob, Workbook, SpreadsheetFile } from 'file:///C:/Program%20Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1112-737-0_26.1112.737.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';

const root = 'D:/CLASS/syh';
const src = path.join(root, 'experiments/kg07_mechanism_interpretation');
const outDir = path.join(root, 'outputs/01a1c308-7ffd-77a0-ad64-05771c186561');
const outFile = path.join(outDir, 'kg07_human_review.xlsx');
const reviewCsv = await fs.readFile(path.join(src, 'kg07_human_review_20_cases.csv'), 'utf8');
const evidenceCsv = await fs.readFile(path.join(src, 'kg07_human_review_evidence.csv'), 'utf8');

// Let artifact-tool parse CSV so quoting/embedded commas and JSON text stay intact.
const reviewImport = await Workbook.fromCSV(reviewCsv, { sheetName: 'Review' });
const evidenceImport = await Workbook.fromCSV(evidenceCsv, { sheetName: 'Evidence' });
const reviewValues = reviewImport.worksheets.getItem('Review').getUsedRange().values;
const evidenceValues = evidenceImport.worksheets.getItem('Evidence').getUsedRange().values;
const reviewHeaders = reviewValues[0].map((v) => String(v).replace(/^\uFEFF/, '').trim());
const evidenceHeaders = evidenceValues[0].map((v) => String(v).replace(/^\uFEFF/, '').trim());

const reviewKeep = [
  'case', 'pert_id', 'drug_name', 'review_code', 'evidence_input_sha256',
  'evidence_package_path', 'claims_json', 'supported_claim_fraction',
  'citation_precision', 'unsupported_assertion_count',
  'relation_direction_error_count', 'uncertainty_accuracy', 'review_notes'
];
const evidenceKeep = [
  'case', 'pert_id', 'drug_name', 'review_code', 'claim_index',
  'claim_section', 'claim_text', 'relation', 'evidence_ids', 'path_ids',
  'citation_found_in_package', 'source_snapshots_json'
];
const project = (rows, headers, keep) => {
  const idx = keep.map((k) => headers.indexOf(k));
  if (idx.some((i) => i < 0)) throw new Error(`Missing required columns: ${keep.filter((_, j) => idx[j] < 0).join(', ')}; parsed header=${JSON.stringify(headers)}`);
  return [keep, ...rows.slice(1).map((r) => idx.map((i) => r[i] ?? null))];
};
const scores = project(reviewValues, reviewHeaders, reviewKeep);
scores[0] = ['病例', '药物ID', '药物', '盲审代码', '证据包SHA256', '证据包路径', '声明数', '支持声明比例', '引用准确率', '无依据断言数', '关系方向错误数', '不确定性判断准确率', '审阅备注'];
for (const row of scores.slice(1)) {
  try { row[6] = JSON.parse(String(row[6] ?? '[]')).length; }
  catch { throw new Error(`Invalid claims_json in blinded review row ${row[0]}/${row[3]}`); }
}
const evidence = project(evidenceValues, evidenceHeaders, evidenceKeep);
const workbook = Workbook.create();

const intro = workbook.worksheets.add('开始这里');
intro.showGridLines = false;
intro.getRange('A1').values = [['KG07 机制解释人工盲审']];
intro.getRange('A1:F1').format = { fill: '#17365D', font: { bold: true, color: '#FFFFFF', size: 16 }, rowHeight: 32, verticalAlignment: 'center' };
const introRows = [
  ['状态', '待人工评分：60 条记录的评分栏均为空。'],
  ['盲审原则', '仅依据工作簿中的匿名代码 A/B/C 评估；全部评分完成前，不打开单独保存的映射密钥。'],
  ['怎么审', '在“评分表”逐行填写 5 个指标和备注；需要核对具体声明时，在“证据快照”按 case + review_code + claim_index 定位。'],
  ['证据核查', '引用 ID 存在不等于引用支持文字。核对原始证据表述、关系方向以及路径来源；把相关性说成因果也计为无依据。'],
  ['比例字段', 'supported_claim_fraction、citation_precision、uncertainty_accuracy 填 0–1 小数；无可评估项填 NA。'],
  ['计数字段', 'unsupported_assertion_count、relation_direction_error_count 填非负整数；没有错误填 0。'],
  ['备注', 'review_notes 记录关键问题，可列 Evidence ID / Path ID。评分留空表示未审阅，不代表 0。'],
  ['回传方式', '保存此工作簿并交回；评分完成后再揭盲汇总。不要把密钥写入此工作簿。'],
  ['研究边界', '这些结果用于机制解释质量评估，不构成药物临床疗效证据。']
];
intro.getRange(`A3:B${introRows.length + 2}`).values = introRows;
intro.getRange('A3:A11').format = { fill: '#D9EAF7', font: { bold: true, color: '#17365D' }, columnWidth: 18, verticalAlignment: 'center' };
intro.getRange('B3:B11').format = { wrapText: true, columnWidth: 100, verticalAlignment: 'center' };
intro.getRange('A3:B11').format.rowHeight = 42;
intro.freezePanes.freezeRows(2);

const scoreSheet = workbook.worksheets.add('评分表');
scoreSheet.showGridLines = false;
scoreSheet.getRangeByIndexes(0, 0, scores.length, scores[0].length).values = scores;
scoreSheet.freezePanes.freezeRows(1);
scoreSheet.getRange('A1:M1').format = { fill: '#17365D', font: { bold: true, color: '#FFFFFF' }, wrapText: true, rowHeight: 36, verticalAlignment: 'center' };
scoreSheet.getRange(`A2:M${scores.length}`).format = { verticalAlignment: 'top', wrapText: true };
scoreSheet.getRange(`H2:L${scores.length}`).format.fill = '#FFF2CC';
scoreSheet.getRange(`M2:M${scores.length}`).format.fill = '#FFF2CC';
for (const [col, width] of Object.entries({ A: 8, B: 18, C: 22, D: 13, E: 27, F: 58, G: 13, H: 20, I: 18, J: 22, K: 23, L: 20, M: 55 })) {
  scoreSheet.getRange(`${col}:${col}`).format.columnWidth = width;
}
scoreSheet.getRange(`A2:L${scores.length}`).format.rowHeight = 28;
scoreSheet.getRange(`M2:M${scores.length}`).format.rowHeight = 42;
for (const col of ['H', 'I', 'L']) {
  scoreSheet.getRange(`${col}2:${col}${scores.length}`).dataValidation = {
    rule: { type: 'custom', formula1: `=OR(AND(ISNUMBER(${col}2),${col}2>=0,${col}2<=1),UPPER(${col}2)="NA")` }
  };
}
for (const col of ['J', 'K']) {
  scoreSheet.getRange(`${col}2:${col}${scores.length}`).dataValidation = {
    rule: { type: 'whole', operator: 'between', formula1: 0, formula2: 1000 }
  };
}

const evidenceSheet = workbook.worksheets.add('证据快照');
evidenceSheet.showGridLines = false;
evidenceSheet.getRangeByIndexes(0, 0, evidence.length, evidence[0].length).values = evidence;
evidenceSheet.freezePanes.freezeRows(1);
evidenceSheet.getRange('A1:L1').format = { fill: '#17365D', font: { bold: true, color: '#FFFFFF' }, wrapText: true, rowHeight: 36, verticalAlignment: 'center' };
evidenceSheet.getRange(`A2:L${evidence.length}`).format = { wrapText: true, verticalAlignment: 'top' };
for (const [col, width] of Object.entries({ A: 8, B: 18, C: 22, D: 13, E: 12, F: 22, G: 80, H: 18, I: 44, J: 34, K: 24, L: 70 })) {
  evidenceSheet.getRange(`${col}:${col}`).format.columnWidth = width;
}
evidenceSheet.getRange(`G2:G${evidence.length}`).format.rowHeight = 54;
evidenceSheet.getRange(`L2:L${evidence.length}`).format.rowHeight = 50;

workbook.recalculate();
await fs.mkdir(outDir, { recursive: true });
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outFile);
const savedBlob = await FileBlob.load(outFile);
const savedWorkbook = await SpreadsheetFile.importXlsx(savedBlob);
for (const [sheetName, range] of [['开始这里', 'A1:B11'], ['评分表', 'A1:M6'], ['证据快照', 'A1:L8']]) {
  const preview = await savedWorkbook.render({ sheetName, range, scale: 0.65, format: 'png' });
  await fs.writeFile(path.join(outDir, `preview_${sheetName}.png`), new Uint8Array(await preview.arrayBuffer()));
}
const check = await savedWorkbook.inspect({ kind: 'workbook,sheet', maxChars: 3000 });
console.log(JSON.stringify({ outFile, scoreRows: scores.length - 1, evidenceRows: evidence.length - 1, scoreHeaders: scores[0], evidenceHeaders: evidence[0], check: check.ndjson }, null, 2));
