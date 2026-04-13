#
### 创建虚拟环境
```shell
python3 -m venv venv

### 激活虚拟环境
source venv/bin/activate

### 安装依赖
pip freeze > requirements.txt
pip install -r requirements.txt

### 运行
python app.py
```
### 替换成最新的 token 值 ，防止账号欠费
```
# 干跑（只打印方案）
python scripts/update_llm_by_quota.py quota.json

# 原地替换（备份原文件）
python scripts/update_llm_by_quota.py quota.json --inplace

# 输出到新文件
python scripts/update_llm_by_quota.py quota.json -o config/llm_config_new.yaml
```