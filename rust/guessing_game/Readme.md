#  安装 maturn 
```bash
pipx install maturin
```

###  创建项目
```bash
maturin new -b pyo3 guessing_game
```

###  安装并配置 maturin（在虚拟环境中）
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip maturin
```

###  开发项目
```bash
maturin develop
```
```output
(.venv) ➜  guessing_game git:(main) ✗ maturin develop
🔗 Found pyo3 bindings
🐍 Found CPython 3.12 at /home/jackluo/data/learn/rust/guessing_game/.venv/bin/python
   Compiling pyo3-build-config v0.27.1
   Compiling pyo3-macros-backend v0.27.1
   Compiling pyo3-ffi v0.27.1
   Compiling pyo3 v0.27.1
   Compiling pyo3-macros v0.27.1
   Compiling guessing_game v0.1.0 (/home/jackluo/data/learn/rust/guessing_game)
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 5.53s
📦 Built wheel for CPython 3.12 to /tmp/.tmpTzGfjj/guessing_game-0.1.0-cp312-cp312-linux_x86_64.whl
✏️ Setting installed package as editable
🛠 Installed guessing_game-0.1.0
```
###  你的 guessing_game 模块现在应该已经在你当前的虚拟环境中开放了。去玩几局吧
```bash
(.venv) ➜  guessing_game git:(main) ✗ python
Python 3.12.3 (main, Aug 14 2025, 17:47:21) [GCC 13.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
Ctrl click to launch VS Code Native REPL
>>> import guessing_game
>>> guessing_game.guess_the_number()
Guess the number!
Please input your guess.
3
You guessed: 3
Too small!
Please input your guess.
4
You guessed: 4
Too small!
Please input your guess.
5
You guessed: 5
Too small!
Please input your guess.
80
You guessed: 80
Too small!
Please input your guess.
99
You guessed: 99
Too big!
Please input your guess.
87  
You guessed: 87
Too small!
Please input your guess.
89
You guessed: 89
Too small!
Please input your guess.
98
You guessed: 98
Too big!
Please input your guess.
93
You guessed: 93
Too small!
Please input your guess.
96
You guessed: 96
Too small!
Please input your guess.
97
You guessed: 97
You win!
>>> 
```