# -*- coding: utf-8 -*-
# auto_ingest.py
"""
掃描 data/images/ 下所有檔案，自動建立索引：reports/auto_index.csv
- 嘗試從檔名判斷 Day (支援 _d2/_d3/_d5/_d6 或 day2/day3/day5/day6)
- image_id = 檔名不含副檔名；若包含胚胎ID前綴 emb_XXXX 會沿用，否則以檔名作為ID
- 若 data/embryo_parameters.csv 不存在，建立一份骨架檔（欄位齊全、值留空）
"""
from pathlib import Path
import re, csv

IMAGES = Path('data/images')
REPORTS = Path('reports')
REPORTS.mkdir(exist_ok=True)
index_csv = REPORTS/'auto_index.csv'

DAY_PATTERNS = [
    (re.compile(r"[_-]d(\d+)", re.I), 1),
    (re.compile(r"day(\d+)", re.I), 1)
]

rows = []
for p in sorted(IMAGES.glob('*')):
    if not p.is_file():
        continue
    fname = p.name
    stem = p.stem
    day = ''
    for pat, gi in DAY_PATTERNS:
        m = pat.search(fname)
        if m:
            day = m.group(gi)
            break
    image_id = stem  # 可自行改規則：如 stem.split('_')[0]
    rows.append([str(p), image_id, day])

with open(index_csv, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['image_path','image_id','day'])
    w.writerows(rows)
print(f"[INGEST] 生成索引：{index_csv} 共 {len(rows)} 筆")

# 參數骨架
params_csv = Path('data')/'embryo_parameters.csv'
if not params_csv.exists():
    with open(params_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['image_id','age','AMH','medium_brand','injection_only','fertilization','outcome','blast_day'])
    print(f"[INGEST] 建立參數骨架：{params_csv}")
