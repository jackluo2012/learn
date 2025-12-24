# maturin develop

```bash
# 编译
maturin develop
```
```python
import guessing_game
guessing_game.guess_the_number()
```
### 演示代码
```python
>>> import guessing_game
>>> guessing_game.guess_the_number()
Guess the number!
Please input your guess.
50
You guessed: 50
Too small!
Please input your guess.
80
You guessed: 80
Too big!
Please input your guess.
60
You guessed: 60
Too big!
Please input your guess.
56
You guessed: 56
Too small!
Please input your guess.
58
You guessed: 58
Too small!
Please input your guess.
59
You guessed: 59
You win!
>>>
```