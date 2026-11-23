# 浏览器项目数据上传端到端验收

日期：2026-11-14

## 验收范围

在独立无头 Edge profile 中打开实际 Vite 页面，选择现有 `test_only` 软件测试项目，经过页面上传弹窗选择 `precomputed_deg` 类型、设置文件输入、提交并校验结果。使用单行合成 DEG，不包含真实患者资料。

## 结果

- 项目：`c493efde-981a-511c-9409-0fac7021b096`（`test_only`）。
- 页面正确显示文件输入可访问名称“选择项目数据文件”；数据类型选择、已选文件状态及成功提示均通过真实 React 页面验证。
- Vite 代理上传生成 Dataset `0327a50b-fd0a-44fa-beee-70ae9980986c`，类型 `precomputed_deg`，状态 `validation_pending`。
- 数据库存储文件存在，文件 SHA-256 与 API/数据库记录一致：`f50483c6c4491bdf9a98179ea7f3030a814b7ad2b16c6bd75f50561bf296895b`。
- 后端实际解析为 CSV、1 行、4 列；因这是 DEG 表，不要求样本分组注释。
- AnalysisRun 数量上传前后均为 4，证明上传未自动运行分析。
- 浏览器页面 UI、上传 API、项目隔离和待验证门禁：**PASS**。

## Windows 原生文件选择器补充验收

- 在独立 Edge 访客窗口中使用 Windows“打开”对话框选择合成表达矩阵 `native_picker_expression.csv`，未触碰个人 Edge 窗口。
- 上传目标仍为项目 `c493efde-981a-511c-9409-0fac7021b096`（`test_only`），数据集 ID 为 `e4ca951b-3ad8-4cee-bf10-b34d6702323c`。
- 文件大小 64 字节；存储文件 SHA-256 为 `988bd2f625f11f63860f51189f107337cc8d4df8469107cbc4dcd0a310aca9ce`，与 API 记录一致。
- 类型为 `expression_matrix`，状态 `validation_pending`，校验为 1 行、3 列、2 个样本，并正确要求样本分组注释。
- 项目 AnalysisRun 数量仍为 4；上传没有启动分析。原生选择、页面登记、数据校验及不自动运行分析：**PASS**。
- 本次文件完全是软件验证用合成数据，不代表任何生物学结果。

## 限制

前一项 DEG 上传通过 Edge DevTools Protocol 的 `DOM.setFileInputFiles` 验证；本次补充另外实际打开并操作了 Windows 原生选择器。两项均使用合成文件和 `test_only` 项目。

## 可复跑

本机 Node 24 和 Microsoft Edge：

```powershell
node scripts\browser_upload_smoke.mjs c493efde-981a-511c-9409-0fac7021b096
```

脚本拒绝正式项目，并在同一测试项目已存在 `synthetic_deg.csv` 时停止，避免重复上传。复跑需使用新的 `test_only` 项目。

机器可读验收记录：`browser_upload_smoke_20261114.json`。
