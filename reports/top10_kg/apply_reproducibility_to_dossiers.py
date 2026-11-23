"""Add historical robustness rows to each frozen-candidate dossier."""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports" / "top10_kg"
DATA = REPORTS / "top10_reproducibility_evidence.csv"
DOSSIERS = REPORTS / "drugs"


def main() -> None:
    with DATA.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        path = DOSSIERS / f"{int(row['rank']):02d}_{row['drug_name']}.md"
        if not path.is_file():
            raise FileNotFoundError(path)
        text = path.read_text(encoding="utf-8-sig")
        text = re.sub(r"\n## Exp006–Exp011 历史复核.*\Z", "", text, flags=re.S)
        section = f"""
## Exp006–Exp011 历史复核

- Exp006：24 h 合格剂量 {row['exp006_dose_count'] or '未记录'} 个，历史 WTCS 负向比例 {row['exp006_negative_dose_fraction'] or '未记录'}；剂量稳定性 `{row['exp006_dose_stability'] or '无候选记录'}`，QC 敏感等级 `{row['exp006_stability_grade'] or '未记录'}`。
- Exp007：A / B100 / B150 / B200 / B300 / matched125 名次：{row['exp007_rank_A_original'] or 'NA'} / {row['exp007_rank_B100'] or 'NA'} / {row['exp007_rank_B150'] or 'NA'} / {row['exp007_rank_B200'] or 'NA'} / {row['exp007_rank_B300'] or 'NA'} / {row['exp007_rank_B_matched125'] or 'NA'}。
- Exp008：历史 B200 置换经验 P / BH-FDR：{row['exp008_empirical_pvalue_B200_historical'] or 'NA'} / {row['exp008_BH_FDR_B200_historical'] or 'NA'}；{row['exp008_scope']}
- Exp009 质量阈值复核：{row['exp009_status']}。Exp010 独立 S1：{row['exp010_status']}{f", rank={row['exp010_external_S1_rank']}, WTCS={row['exp010_external_S1_WTCS']}" if row['exp010_status'] == 'available' else ''}。
- Exp011 PRISM：{row['exp011_status']}{f", ER+ mean={row['exp011_ERpos_mean_sensitivity']}, ER− mean={row['exp011_ERneg_mean_sensitivity']}, ER+−ER−={row['exp011_ERpos_minus_ERneg']}" if row['exp011_status'] == 'available' else ''}。
- 限制：这些是已完成的历史分析，不是按本轮冻结签名重算；未匹配或缺少记录不等于阴性结果。PRISM 细胞存活敏感性与 LINCS WTCS 是不同终点。
"""
        path.write_text(text.rstrip() + "\n" + section.lstrip(), encoding="utf-8")


if __name__ == "__main__":
    main()
