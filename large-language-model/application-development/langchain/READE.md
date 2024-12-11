### 不同 Python 项目需要使用不同版本的 Python 解释器，以及独立的 package 依赖。

```
使用 Poetry + Pyenv 管理。
首先安装 Pyenv 和 Poetry。
配置 Poetry：
poetry config virtualenvs.prefer-active-python true
使用 Pyenv 安装多版本解释器：
pyenv install 3.10
pyenv install 3.11
pyenv install --list
在 Poetry 项目中，指定 Python 版本：
poetry env use $(which python3.10)
结束。
```