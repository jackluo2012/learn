# sentiment_analysis.py

# 1. 环境准备
# 导入所需的库
import torch
from transformers import BertTokenizer, BertForSequenceClassification, AdamW
from datasets import load_dataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import jieba
import pandas as pd

# 2. 加载中文 BERT 预训练模型
model_name = 'bert-base-chinese'
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertForSequenceClassification.from_pretrained(model_name, num_labels=2)  # 2 表示二分类 (积极/消极)

# 3. 加载开源数据集 ChnSenticorp
# 假设 ChnSenticorp 数据集已经下载并解压到本地
# 请将 'path/to/chnsenticorp' 替换为实际的路径
try:
    dataset = load_dataset("csv", data_files={"train": "ChnSentiCorp_htl_all.csv"})
    # dataset = load_dataset("csv", data_files={"train": "path/to/chnsenticorp/train.csv", "test": "path/to/chnsenticorp/test.csv"}) # 如果有train和test文件
except FileNotFoundError:
    print("ChnSenticorp 数据集文件未找到，请确保文件路径正确。")
    exit()

# 数据清洗和预处理
def preprocess_function(examples):
    # 使用jieba分词
    tokenized_text = [" ".join(jieba.cut(text)) for text in examples["text"]]
    return tokenizer(tokenized_text, padding="max_length", truncation=True, max_length=128)

tokenized_datasets = dataset.map(preprocess_function, batched=True)

# 4. 数据预处理
# 将数据集转换为 PyTorch 张量
tokenized_datasets.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])

# 5. 训练模型
# 定义训练参数
batch_size = 32
learning_rate = 2e-5
epochs = 3

# 创建数据加载器
train_dataloader = torch.utils.data.DataLoader(tokenized_datasets["train"], shuffle=True, batch_size=batch_size)
# 检查是否有测试集，如果没有，则使用训练集的一部分作为测试集
if "test" in tokenized_datasets:
    eval_dataloader = torch.utils.data.DataLoader(tokenized_datasets["test"], batch_size=batch_size)
else:
    train_dataset, eval_dataset = torch.utils.data.random_split(tokenized_datasets["train"], [0.8, 0.2])
    eval_dataloader = torch.utils.data.DataLoader(eval_dataset, batch_size=batch_size)
    train_dataloader = torch.utils.data.DataLoader(train_dataset, shuffle=True, batch_size=batch_size)

# 优化器
optimizer = AdamW(model.parameters(), lr=learning_rate)

# 训练循环
device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
model.to(device)

for epoch in range(epochs):
    model.train()
    for batch in train_dataloader:
        batch = {k: v.to(device) for k, v in batch.items()}
        outputs = model(**batch)
        loss = outputs.loss
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
    print(f"Epoch {epoch+1}/{epochs} 训练完成")

# 6. 评估模型性能
model.eval()
all_predictions = []
all_labels = []
with torch.no_grad():
    for batch in eval_dataloader:
        batch = {k: v.to(device) for k, v in batch.items()}
        outputs = model(**batch)
        logits = outputs.logits
        predictions = torch.argmax(logits, dim=-1)
        all_predictions.extend(predictions.cpu().tolist())
        all_labels.extend(batch["label"].cpu().tolist())

accuracy = accuracy_score(all_labels, all_predictions)
print(f"准确率: {accuracy}")
print(classification_report(all_labels, all_predictions))

# 7. 导出模型
# 保存模型
model.save_pretrained("./sentiment_model")
tokenizer.save_pretrained("./sentiment_model")

print("模型已保存到 ./sentiment_model 目录")