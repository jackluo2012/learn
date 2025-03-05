### Quantaxis安装
```
git clone https://github.com/yutiansut/quantaxis --depth 1 
cd quantaxis
python -m pip install -r requirements.txt -i https://pypi.doubanio.com/simple
python -m pip install tushare
python -m pip install pytdx
python -m pip install -e . 
```

### 设置mongodb
```
$env:MONGODB = "192.168.1.100" #设置mongodb地址

$env:MONGODB = "mongodb://root:admin@localhost:27017/quantaxis"
```