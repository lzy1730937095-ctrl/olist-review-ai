"""基准方案：用关键词判断差评是否属于“1 未收到 / 送达延迟”，并与人工标准答案对比。

运行：python src/keyword_baseline.py
"""
import pandas as pd

df = pd.read_csv("data/gold100.csv")

# 两组关键词：v1 为最初版本，v2 在 v1 基础上加入 entreg（配送）
KEYWORDS = {
    "v1": ["rece", "che", "prazo", "atras", "demo", "aguard", "ainda não"],
    "v2": ["rece", "che", "prazo", "atras", "demo", "aguard", "ainda não", "entreg"],
}

for name, keywords in KEYWORDS.items():
    tp = fp = fn = 0
    for comment, gold in zip(df["review_comment_message"], df["gold_labels"]):
        c = comment.lower()
        pred = any(k in c for k in keywords)
        truth = "1" in str(gold).split(",")
        if pred and truth:
            tp += 1
        elif pred and not truth:
            fp += 1
        elif not pred and truth:
            fn += 1
    precision = tp / (tp + fp) * 100
    recall = tp / (tp + fn) * 100
    print(f"关键词 {name}：TP={tp} FP={fp} FN={fn}  精确率 {precision:.1f}%  召回率 {recall:.1f}%")
