

---

# v6 一鍵流程（只給影像＋參數也可跑）

## 1) 準備
- 把你的影像放到 `data/images/`（檔名建議含 day 標記，如 `emb_0001_d3.jpg` 或 `...day3...`）
- 編輯/匯入 `data/embryo_parameters.csv`（若不存在，`auto_ingest.py` 會建立骨架）

## 2) 一鍵執行
- **零標註模式（不訓練，啟發式估計細胞數）**：
```bash
python src/pipeline_v6.py --mode zero-shot
```
- **監督模式（若已建好 train/val CSV 就訓練並推論；否則退回啟發式）**：
```bash
python src/pipeline_v6.py --mode supervised
```

## 3) 輸出位置
- 成長線（論文版面、300DPI）：`reports/figures_paper/*.png`
- 分層/交互作用統計：`reports/analytics/*.png` + `*.csv`
- 啟發式或推論結果：`reports/cell_count_pred.csv`（Day2/3），`reports/blast_pred.csv`（Day5/6）

> 注意：啟發式估計僅供研究流程驗證，**不可用於臨床**。如需更可靠結果，請提供標註並使用 supervised 模式訓練模型。
