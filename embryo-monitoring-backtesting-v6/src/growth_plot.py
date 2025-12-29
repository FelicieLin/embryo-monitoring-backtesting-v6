# -*- coding: utf-8 -*-
# growth_plot.py (paper style)
import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False


PALETTE = {
    'line': '#1f4287',      # 深藍
    'marker': '#21e6c1',    # 青綠
    'blast': '#ff6b6b',     # 珊瑚紅（TE/ICM 標註）
    'text_box_edge': '#ff6b6b'
}

CELL_MAP = {'2cells':2,'4cells':4,'8cells':8,'>8cells':10,'2':2,'4':4,'8':8,'10':10}

REPORTS = Path('reports')
REPORTS.mkdir(exist_ok=True)
(REPORTS/'growth_lines').mkdir(exist_ok=True)
(REPORTS/'figures_paper').mkdir(exist_ok=True)

cell_csv = REPORTS/'cell_count_pred.csv'
blast_csv = REPORTS/'blast_pred.csv'
params_csv = Path('data')/'embryo_parameters.csv'

if not cell_csv.exists():
    print(f"[WARN] 缺少 {cell_csv}，請先輸出細胞數預測。")
    raise SystemExit(0)

cell_df = pd.read_csv(cell_csv)
blast_df = pd.read_csv(blast_csv) if blast_csv.exists() else pd.DataFrame(columns=['image_id','day','pred_te','pred_icm'])
params_df = pd.read_csv(params_csv) if params_csv.exists() else pd.DataFrame()

cell_df['cell_count'] = cell_df.get('pred_label', cell_df.get('cell_count')).map(CELL_MAP)
cell_df['day'] = pd.to_numeric(cell_df['day'], errors='coerce')

# 整體總覽（論文版面）
plt.figure(figsize=(8,6))
for eid, sub in cell_df.sort_values(['image_id','day']).groupby('image_id'):
    plt.plot(sub['day'], sub['cell_count'], color=PALETTE['line'], linewidth=2.5, alpha=0.6)
plt.title('胚胎細胞數成長線總覽', fontsize=14, fontweight='bold')
plt.xlabel('培養天數', fontsize=12); plt.ylabel('細胞數', fontsize=12)
plt.tight_layout(); plt.savefig(REPORTS/'figures_paper'/'growth_overview.png', dpi=300)
plt.close()

# 個別胚胎（論文版面）
for eid, sub in cell_df.groupby('image_id'):
    sub = sub.sort_values('day')
    fig, ax = plt.subplots(figsize=(6.5,4.8))
    ax.plot(sub['day'], sub['cell_count'], color=PALETTE['line'], marker='o', markersize=4,
            markerfacecolor=PALETTE['marker'], markeredgecolor=PALETTE['line'], linewidth=2)
    # TE/ICM 標註
    if not blast_df.empty:
        bsub = blast_df[blast_df['image_id']==eid].copy()
        bsub['day'] = pd.to_numeric(bsub['day'], errors='coerce')
        for _, r in bsub.iterrows():
            ax.scatter(r['day'], sub['cell_count'].max() if len(sub)>0 else 0,
                       s=80, color=PALETTE['blast'], marker='s', zorder=3)
            ax.annotate(f"TE:{r.get('pred_te','?')}\nICM:{r.get('pred_icm','?')}",
                        xy=(r['day'], sub['cell_count'].max()), xytext=(5, -5), textcoords='offset points',
                        bbox=dict(boxstyle='round', fc='white', ec=PALETTE['text_box_edge'], lw=1.5), fontsize=9)
    # 標題含參數摘要
    ttl = eid
    row = params_df[params_df['image_id']==eid]
    if not row.empty:
        rr = row.iloc[0]
        ttl = f"{eid} | age:{rr.get('age','?')} AMH:{rr.get('AMH','?')} {rr.get('fertilization','?')} {rr.get('medium_brand','?')} outcome:{rr.get('outcome','?')}"
    ax.set_title(ttl, fontsize=12, fontweight='bold')
    ax.set_xlabel('培養天數'); ax.set_ylabel('細胞數')
    fig.tight_layout(); fig.savefig(REPORTS/'figures_paper'/f'{eid}_growth.png', dpi=300)
    plt.close(fig)
print('Paper-style figures saved to reports/figures_paper/')
