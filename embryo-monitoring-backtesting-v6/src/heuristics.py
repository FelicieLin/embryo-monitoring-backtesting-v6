# -*- coding: utf-8 -*-
# heuristics.py
"""簡易影像啟發法：估計細胞數（僅研究用、不可作臨床用途）
步驟：灰階→自動門檻→二值化→連通元件計數→輸出 2/4/8/>8 類別。
"""
from PIL import Image
import numpy as np

def otsu_threshold(gray: np.ndarray) -> int:
    # gray: 0..255
    hist, _ = np.histogram(gray, bins=256, range=(0,255))
    total = gray.size
    sum_total = np.dot(np.arange(256), hist)
    sum_b, w_b, w_f, max_var, th = 0.0, 0.0, 0.0, 0.0, 0
    for t in range(256):
        w_b += hist[t]
        if w_b == 0: continue
        w_f = total - w_b
        if w_f == 0: break
        sum_b += t * hist[t]
        m_b = sum_b / w_b
        m_f = (sum_total - sum_b) / w_f
        var_between = w_b * w_f * (m_b - m_f) ** 2
        if var_between > max_var:
            max_var = var_between; th = t
    return th

def count_components(bin_img: np.ndarray, min_size=30) -> int:
    # bin_img: 0/1
    h, w = bin_img.shape
    visited = np.zeros_like(bin_img, dtype=bool)
    dirs = [(1,0),(-1,0),(0,1),(0,-1)]
    def bfs(si,sj):
        stack = [(si,sj)]; visited[si,sj]=True; size=0
        while stack:
            i,j = stack.pop()
            size += 1
            for di,dj in dirs:
                ni,nj = i+di,j+dj
                if 0<=ni<h and 0<=nj<w and not visited[ni,nj] and bin_img[ni,nj]==1:
                    visited[ni,nj]=True; stack.append((ni,nj))
        return size
    count=0
    for i in range(h):
        for j in range(w):
            if bin_img[i,j]==1 and not visited[i,j]:
                size=bfs(i,j)
                if size>=min_size:
                    count+=1
    return count

def estimate_cell_label(image_path: str) -> str:
    img = Image.open(image_path).convert('L')
    gray = np.array(img)
    th = otsu_threshold(gray)
    bin_img = (gray >= th).astype(np.uint8)
    cnt = count_components(bin_img, min_size=50)
    # 粗略對應
    if cnt <= 3: return '2cells'
    if cnt <= 6: return '4cells'
    if cnt <= 10: return '8cells'
    return '>8cells'
