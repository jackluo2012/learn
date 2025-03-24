### 第三节
### 获取迭代器的三种方法iter()、iter mut()和Into_iter()

#### 1. iter()方法
### iter()方法返回一个不可变引用的迭代器，用于只读访问集合的元素
### 该方法适用于你希望在不修改集合的情况下迭代元素的场景
```rust
let v1 = vec![1, 2, 3];
let v1_iter = v1.iter();
for val in v1_iter {
    println!("Got: {}", val);
}
```
#### 2. iter mut()方法
### iter mut()方法
### iter_mut()方法返回一个可变引用的迭代器，用于允许修改集合中的元素
### 该方法适用于你希望在迭代过程中修改集合元素的场景
```rust
let mut v1 = vec![1, 2, 3];
```
#### 3. Into_iter()方法
### Into_iter()方法
### Into_iter()方法将集合转换为迭代器，并消耗集合的所有权
### 该方法适用于你希望在迭代过程中消耗集合的场景
```rust
let v1 = vec![1, 2, 3];
let v1_iter = v1.into_iter();
for val in v1_iter {
    println!("Got: {}", val);
}
```