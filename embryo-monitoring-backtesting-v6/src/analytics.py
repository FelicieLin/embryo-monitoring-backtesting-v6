# -*- coding: utf-8 -*-
# analytics.py (interaction effects)
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 設定中文字型 (解決 Windows 下 Matplotlib 中文亂碼問題)
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False


REPORTS = Path('reports')
OUT = REPORTS/'analytics'
OUT.mkdir(parents=True, exist_ok=True)

cell_csv = REPORTS/'cell_count_pred.csv'
blast_csv = REPORTS/'blast_pred.csv'
params_csv = Path('data')/'embryo_parameters.csv'

cell_df = pd.read_csv(cell_csv) if cell_csv.exists() else pd.DataFrame()
blast_df = pd.read_csv(blast_csv) if blast_csv.exists() else pd.DataFrame(columns=['image_id','day','pred_te','pred_icm'])
params_df = pd.read_csv(params_csv)

# 成功標記轉布林
params_df['success'] = params_df['outcome'].str.lower().isin(['success','implant']).astype(int)

# Day3 細胞數（若有）
CELL_MAP = {'2cells':2,'4cells':4,'8cells':8,'>8cells':10}
if not cell_df.empty and 'pred_label' in cell_df.columns:
    cell_df['cell_count'] = cell_df['pred_label'].map(CELL_MAP).fillna(pd.to_numeric(cell_df.get('cell_count', np.nan), errors='coerce'))
day3 = cell_df[cell_df.get('day','').astype(str).eq('3')][['image_id','cell_count']].rename(columns={'cell_count':'day3_cells'}) if not cell_df.empty else pd.DataFrame(columns=['image_id','day3_cells'])

base = params_df.merge(day3, on='image_id', how='left')
if not blast_df.empty:
    blast_sel = blast_df[['image_id','pred_te','pred_icm']].drop_duplicates('image_id')
    base = base.merge(blast_sel, on='image_id', how='left')

# 年齡與 AMH 分層
bins_age = [0,30,35,40,120]
labels_age = ['<30','30-34','35-39','>=40']
base['age_bin'] = pd.cut(pd.to_numeric(base['age'], errors='coerce'), bins=bins_age, labels=labels_age, right=False)

bins_amh = [-np.inf,1,3,np.inf]
labels_amh = ['AMH<1','1<=AMH<3','AMH>=3']
base['AMH_bin'] = pd.cut(pd.to_numeric(base['AMH'], errors='coerce'), bins=bins_amh, labels=labels_amh)

# 互動：Age × AMH 成功率熱圖
pivot_age_amh = base.pivot_table(index='age_bin', columns='AMH_bin', values='success', aggfunc='mean',observed=False)
pivot_age_amh.to_csv(OUT/'success_age_amh.csv')
plt.figure(figsize=(6,4))
plt.imshow(pivot_age_amh.values, cmap='Blues', vmin=0, vmax=1)
plt.title('成功率（年齡 × AMH）'); plt.xlabel('AMH 分層'); plt.ylabel('年齡分層')
plt.xticks(range(len(pivot_age_amh.columns)), pivot_age_amh.columns)
plt.yticks(range(len(pivot_age_amh.index)), pivot_age_amh.index)
for i in range(len(pivot_age_amh.index)):
    for j in range(len(pivot_age_amh.columns)):
        val = pivot_age_amh.values[i,j]
        plt.text(j, i, f"{val:.2f}" if pd.notna(val) else '-', ha='center', va='center')
plt.colorbar(label='成功率'); plt.tight_layout(); plt.savefig(OUT/'success_rate_heatmap_age_amh.png', dpi=300); plt.close()

# 互動：培養液 × 受精方式 成功率熱圖
pivot_med_fert = base.pivot_table(index='medium_brand', columns='fertilization', values='success', aggfunc='mean')
pivot_med_fert.to_csv(OUT/'success_medium_fertilization.csv')
plt.figure(figsize=(7,4))
plt.imshow(pivot_med_fert.values, cmap='Greens', vmin=0, vmax=1)
plt.title('成功率（培養液 × 受精方式）'); plt.xlabel('受精方式'); plt.ylabel('培養液品牌')
plt.xticks(range(len(pivot_med_fert.columns)), pivot_med_fert.columns, rotation=30)
plt.yticks(range(len(pivot_med_fert.index)), pivot_med_fert.index)
for i in range(len(pivot_med_fert.index)):
    for j in range(len(pivot_med_fert.columns)):
        val = pivot_med_fert.values[i,j]
        plt.text(j, i, f"{val:.2f}" if pd.notna(val) else '-', ha='center', va='center')
plt.colorbar(label='成功率'); plt.tight_layout(); plt.savefig(OUT/'success_rate_heatmap_medium_fertilization.png', dpi=300); plt.close()

# TE/ICM 分布互動：Age × AMH
if 'pred_te' in base.columns:
    te_dist = base.groupby(['age_bin','AMH_bin','pred_te']).size().unstack(fill_value=0)
    te_dist.to_csv(OUT/'te_dist_age_amh.csv')
    te_dist_ratio = te_dist.div(te_dist.sum(axis=1), axis=0)
    plt.figure(figsize=(8,5))
    # 顯示 TE 分布比率在 Age×AMH 交互下（堆疊條形）
    te_dist_ratio.plot(kind='bar', stacked=True, colormap='Blues')
    plt.title('TE 等級比例（年齡 × AMH）'); plt.xlabel('年齡×AMH 分層'); plt.ylabel('比例')
    plt.tight_layout(); plt.savefig(OUT/'te_ratio_age_amh.png', dpi=300); plt.close()

if 'pred_icm' in base.columns:
    icm_dist = base.groupby(['age_bin','AMH_bin','pred_icm']).size().unstack(fill_value=0)
    icm_dist.to_csv(OUT/'icm_dist_age_amh.csv')
    icm_dist_ratio = icm_dist.div(icm_dist.sum(axis=1), axis=0)
    plt.figure(figsize=(8,5))
    icm_dist_ratio.plot(kind='bar', stacked=True, colormap='Oranges')
    plt.title('ICM 等級比例（年齡 × AMH）'); plt.xlabel('年齡×AMH 分層'); plt.ylabel('比例')
    plt.tight_layout(); plt.savefig(OUT/'icm_ratio_age_amh.png', dpi=300); plt.close()

# 備註：若需統計檢定（卡方等），可另以 SciPy 進行；此處僅輸出熱圖與分布。
print('Interaction analytics saved to reports/analytics/*.csv & *.png')
