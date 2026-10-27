"""用 DeepSeek 对 100 条差评做多标签分类。

在 Google Colab 中运行：
  1. 上传 data/gold100.csv 和 src/prompt_v2.txt
  2. 在左侧 Secrets（钥匙图标）中添加 DEEPSEEK_API_KEY，并打开笔记本访问权限
本地运行：先设置环境变量 DEEPSEEK_API_KEY，再执行 python src/classify_deepseek.py

API 密钥不要写进代码，也不要提交到 GitHub。
"""
import json
import os
import re

import pandas as pd
from openai import OpenAI

try:  # Colab
    from google.colab import userdata
    API_KEY = userdata.get("DEEPSEEK_API_KEY")
    GOLD_PATH, PROMPT_PATH, OUT_PATH = "gold100.csv", "prompt_v2.txt", "ai_results.csv"
except ImportError:  # 本地
    API_KEY = os.environ["DEEPSEEK_API_KEY"]
    GOLD_PATH = "data/gold100.csv"
    PROMPT_PATH = "src/prompt_v2.txt"
    OUT_PATH = "results/ai_results_deepseek_prompt_v2.csv"

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")
PROMPT = open(PROMPT_PATH, encoding="utf-8").read()


def classify(review):
    """把一条评论填进 prompt，返回模型的原始回答。"""
    message = PROMPT.replace("{review}", review)
    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=[{"role": "user", "content": message}],
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def parse(text):
    """从回答中取出 labels（转成 "1,7" 这样的文字）和 reason；格式不对返回 ERROR。"""
    try:
        data = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
        return ",".join(str(x) for x in data["labels"]), data.get("reason", "")
    except Exception:
        return "ERROR", text


df = pd.read_csv(GOLD_PATH)
ai_labels, ai_reasons = [], []

for i, review in enumerate(df["review_comment_message"]):
    try:
        labels, reason = parse(classify(review))
    except Exception as e:  # 网络等错误：记录后继续
        labels, reason = "ERROR", str(e)
    ai_labels.append(labels)
    ai_reasons.append(reason)
    print(f"{i + 1}/{len(df)}  AI：{labels}  答案：{df['gold_labels'][i]}")

df["ai_labels"] = ai_labels
df["ai_reason"] = ai_reasons
df.to_csv(OUT_PATH, index=False)
print("完成，出错条数：", ai_labels.count("ERROR"))
