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