use std::{fmt::Display, iter::Peekable, str::Chars};
#[derive(Debug,Clone,Copy)]
enum Token {
    Number(i32),
    Plus, // 加法
    Minus, // 减法
    Multiply, // 乘法
    Divide, // 除法
    Power, // 幂
    LeftParen, // 左括号
    RightParen, // 右括号
    
}
const ASSOC_RIGHT:i32 = 1; // 右结合
const ASSOC_LEFT:i32 = -1; // 左结合
impl Display for Token  {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "{}",
            match self {
                Token::Number(n) => n.to_string(),
                Token::Plus => "+".to_string(),
                Token::Minus => "-".to_string(),
                Token::Multiply => "*".to_string(),
                Token::Divide => "/".to_string(),
                Token::Power => "^".to_string(),
                Token::LeftParen => "(".to_string(),
                Token::RightParen => ")".to_string(),
            }
        )
    }
}

impl Token  {
    // 判断是否是数字
    fn is_numerice(&self) -> bool {
        match self {
            Token::Number(_) => true,
            _ => false,
        }
    }
    // 判断是否是操作符
    fn is_operator(&self) -> bool {
        match self {
            Token::Plus | Token::Minus | Token::Multiply | Token::Divide | Token::Power => true,
            _ => false,
        }
    }
    // 判断优先级别
    fn precedence(&self) -> u8 {
        match self {
            Token::Plus | Token::Minus => 1,
            Token::Multiply | Token::Divide => 2,
            Token::Power => 3,
            _ => 0,
        }
    }
    // 获取运算符的结合性
    fn assoc(&self) -> i32 {
        match self {
            Token::Power => ASSOC_RIGHT,           
            _ => ASSOC_LEFT,
        }
    }
    fn compute(&self, left: i32, right: i32) -> Option<i32> {
        match self {
            Token::Plus => Some(left + right),
            Token::Minus => Some(left - right),
            Token::Multiply => Some(left * right),
            Token::Divide => Some(left / right),
            Token::Power => Some(left.pow(right as u32)),
            _ => None,
        }
    }

}


// 将一个算术表达式解析成连续的 Token
// 并通过 Iterator 返回，也可以通过 Peekable 接口获取
struct Tokenizer<'info> {
    tokens: Peekable<Chars<'info>>,
}

impl <'info> Tokenizer<'info>  {
    fn new(expr: &'info str) -> Self {
        Self {
            tokens: expr.chars().peekable(),
        }
    }
    // 跳过空白字符
    fn consume_whitespace(&mut self) {
        while let Some(c) = self.tokens.peek() {
            if c.is_whitespace() {
                self.tokens.next();
            }else {
                break;
            }
        }
    } 
    // 扫描数字
    fn scan_number(&mut self) -> Option<Token> {
        let mut num = String::new();
        while let Some(c) = self.tokens.peek() {
            if c.is_numeric() {
                num.push(*c);
                self.tokens.next();
            }else {
                break;
            }
        }
        match num.parse::<i32>() {
            Ok(n) => Some(Token::Number(n)),
            Err(_) => None,
        }
    } 
    // 扫描操作符
    fn scan_opeator(&mut self) -> Option<Token> {
        match self.tokens.next() {
            Some('+') => Some(Token::Plus),
            Some('-') => Some(Token::Minus),
            Some('*') => Some(Token::Multiply),
            Some('/') => Some(Token::Divide),
            Some('^') => Some(Token::Power),
            Some('(') => Some(Token::LeftParen),
            Some(')') => Some(Token::RightParen),
            _ => None,
        }
    }
}


impl <'info> Iterator for Tokenizer<'info>  {
    type Item = Token;
    fn next(&mut self) -> Option<Self::Item> {
        
        self.consume_whitespace();
        match self.tokens.peek() {
            Some(c) if c.is_numeric() =>self.scan_number(),
            Some(_) => self.scan_opeator(),
            None => None,
        }
    }
}

fn main() {
    println!("Hello, world!");
}
