// trait 不可变引用 \ Move

//定义一个结构
struct Obj{}
//定义一个trait
trait Overview{
    fn overview(&self) -> String{
        String::from("overview")
    }
}
//为结构实现trait
impl Overview for Obj{
    fn overview(&self) -> String{
        String::from("obj")
    }
}
// 定义一个函数，参数为trait
// 不可变引用 
fn call_obj(item: &impl Overview){
    println!("Overview {}",item.overview());
}
// Move 所有权转移
fn call_obj_move(item: Box<dyn Overview>){
    println!("Overview {}",item.overview());
}

fn main() {
     //调用不可用引用
     let a = Obj{};
     call_obj(&a);
     println!("Overview {}",a.overview());
     //调用所有权转移
     let b_a = Box::new(Obj{});
     call_obj_move(b_a);
    //  println!("Overview {}",b_a.overview());

    // 创建一个普通的 金额
    // Box 会转移所有权 
    let c = Box::new(Common(100.0));
    let t = Box::new(TenPercentDiscount(100.0));
    let f = Box::new(FixedDiscount(100.0));
    //声明一个集合，集合中每个元素都实现了Sale特质
    // 显示声明集合中每个元素都是Box
    let sales:Vec<Box<dyn Sale>> = vec![c,t,f];
    //计算金额
    let total = total_amount(&sales);
    println!("Total {}",total);
}
// 计算钱数的一个特质
trait Sale{
    fn amount(&self) -> f64;
}
//原始金额
struct Common(f64);
//实现计算金额
impl Sale for Common{
    fn amount(&self) -> f64{
        self.0
    }
}
//打折
struct TenPercentDiscount(f64);
impl Sale for TenPercentDiscount{
    fn amount(&self) -> f64{
        self.0 * 0.9
    }
}
//立减
struct FixedDiscount(f64);
impl Sale for FixedDiscount{
    fn amount(&self) -> f64{
        self.0 - 10.0
    }
}
//计算金额
// 传入一个集合，集合中每个元素都实现了Sale特质
fn total_amount(sales: &Vec<Box<dyn Sale>>) -> f64{
    // 遍历集合，计算金额 ,先打折再立减
    sales.iter().map(|s| s.amount()).sum()
}