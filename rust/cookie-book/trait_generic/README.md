# Trait Object 与 泛型
## 泛型 与 impl 不同的写法
- fn call(item1:&impl Trait,item2:&impl Trait);
- 可以是不同类型
- fn call_generic<T:Trait>(item1:&T,item2:&T);
- 必须是相同类型
### Multiple Trait Bounds
- fn call(impl Trait1+AnotherTrait);
- fn call_generic<T:Trait1+AnotherTrait>(item1:&T);

