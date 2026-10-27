"""评估 AI 分类结果：逐类别计算精确率、召回率，并列出与标准答案不一致的样本。

运行：python src/evaluate.py results/ai_results_deepseek_prompt_v2.csv
"""
import sys

import pandas as pd

CATEGORIES = {
    1: "未收到/送达延迟", 2: "少发/漏发", 3: "发错货", 4: "与描述不符",
    5: "商品缺陷", 6: "运输破损/包装", 7: "客服/售后", 8: "其他",
}


def to_set(labels):
    labels = str(labels)
    return set() if labels == "ERROR" else {int(x) for x in labels.split(",")}


path = sys.argv[1] if len(sys.argv) > 1 else "results/ai_results_deepseek_prompt_v2.csv"
df = pd.read_csv(path)
gold = [to_set(x) for x in df["gold_labels"]]
pred = [to_set(x) for x in df["ai_labels"]]

exact = sum(g == p for g, p in zip(gold, pred))
print(f"完全一致：{exact}/{len(df)}    解析失败：{(df['ai_labels'] == 'ERROR').sum()}\n")

print(f"{'类别':<14}{'TP':>4}{'FP':>4}{'FN':>4}{'精确率':>9}{'召回率':>9}")
total_tp = total_fp = total_fn = 0
for k, name in CATEGORIES.items():
    tp = sum(k in g and k in p for g, p in zip(gold, pred))
    fp = sum(k not in g and k in p for g, p in zip(gold, pred))
    fn = sum(k in g and k not in p for g, p in zip(gold, pred))
    total_tp, total_fp, total_fn = total_tp + tp, total_fp + fp, total_fn + fn
    precision = f"{tp / (tp + fp) * 100:.1f}%" if tp + fp else "-"
    recall = f"{tp / (tp + fn) * 100:.1f}%" if tp + fn else "-"
    print(f"{k} {name:<12}{tp:>4}{fp:>4}{fn:>4}{precision:>9}{recall:>9}")
print(f"{'合计':<14}{total_tp:>4}{total_fp:>4}{total_fn:>4}"
      f"{total_tp / (total_tp + total_fp) * 100:>8.1f}%{total_tp / (total_tp + total_fn) * 100:>8.1f}%")

print("\n不一致的样本：")
for i, (g, p) in enumerate(zip(gold, pred)):
    if g != p:
        row = df.iloc[i]
        print(f"#{row['idx']}  答案 {row['gold_labels']} → AI {row['ai_labels']}  |  {row['ai_reason']}")
