# -*- coding: utf-8 -*-
# pipeline_v6.py
"""
用法（只需影像 + 參數）：
    python src/pipeline_v6.py --mode zero-shot
或（已有/願意訓練模型）：
    python src/pipeline_v6.py --mode supervised
說明：
- zero-shot：不訓練，使用 heuristics 估計 Day2/3 細胞數；TE/ICM 若無推論檔則略過。
- supervised：若 data/*_train.csv 存在則訓練；若 models/* 權重存在則推論；否則退回 heuristics。
"""
import argparse
from pathlib import Path
import pandas as pd

REPORTS = Path('reports')
DATA = Path('data')
SRC = Path('src')


def ensure_auto_index():
    from auto_ingest import IMAGES, REPORTS, index_csv
    # 直接呼叫會再次建立索引與參數骨架
    pass


def build_cell_predictions_zero_shot():
    # 由 auto_index + heuristics 估計 Day2/3 細胞數
    from heuristics import estimate_cell_label
    idx = pd.read_csv(REPORTS/'auto_index.csv')
    rows = []
    for _, r in idx.iterrows():
        label = estimate_cell_label(r['image_path'])
        rows.append({
            'image_id': r['image_id'],
            'day': r['day'],
            'image_path': r['image_path'],
            'pred_label': label
        })
    out = REPORTS/'cell_count_pred.csv'
    pd.DataFrame(rows).to_csv(out, index=False, encoding='utf-8')
    print(f"[ZERO-SHOT] 產出細胞數預測：{out}")


def run_supervised_if_possible():
    # 優先訓練與推論，若缺資料則退回 heuristics
    trained_any = False
    # 細胞數
    cell_train = DATA/'cell_count_train.csv'
    cell_val   = DATA/'cell_count_val.csv'
    if cell_train.exists() and cell_val.exists():
        from cell_count_train import train, inference
        train(str(cell_train), str(cell_val),
              class_names=["2cells","4cells","8cells",">8cells"],
              out_dir='models/cell_count', epochs=3, bs=16, lr=1e-3)
        inference('models/cell_count/best.pt', str(cell_val), str(REPORTS/'cell_count_pred.csv'))
        trained_any = True
    else:
        print('[SUPERVISED] 缺少 cell_count_train/val.csv，略過訓練，將使用 heuristics。')
        build_cell_predictions_zero_shot()
    # TE/ICM
    blast_train = DATA/'blast_train.csv'
    blast_val   = DATA/'blast_val.csv'
    if blast_train.exists() and blast_val.exists():
        from blast_grading_train import train, inference_multitask
        train(str(blast_train), str(blast_val), out_dir='models/blast', epochs=3, bs=16, lr=1e-3)
        inference_multitask('models/blast/best_multitask.pt', str(blast_val), str(REPORTS/'blast_pred.csv'))
        trained_any = True
    else:
        print('[SUPERVISED] 缺少 blast_train/val.csv，略過 TE/ICM 推論。')
    return trained_any


def run_growth_and_analytics():
    # 繪製成長線（論文版面）與交互作用統計
    import subprocess, sys
    subprocess.run([sys.executable, str(SRC/'growth_plot.py')], check=False)
    subprocess.run([sys.executable, str(SRC/'analytics.py')], check=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['zero-shot','supervised'], default='zero-shot')
    args = ap.parse_args()

    # 先產生索引與參數骨架
    import subprocess, sys
    subprocess.run([sys.executable, str(SRC/'auto_ingest.py')], check=False)

    if args.mode == 'zero-shot':
        build_cell_predictions_zero_shot()
    else:
        run_supervised_if_possible()

    run_growth_and_analytics()
    print('[PIPELINE] 完成：請查看 reports/figures_paper 與 reports/analytics')

if __name__ == '__main__':
    main()
