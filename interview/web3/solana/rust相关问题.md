### 为什么 Solana 选择 Rust 作为智能合约开发语言？​
#### 高性能​：Rust 编译后的代码接近机器码效率，适合 Solana 的高吞吐量需求（每秒处理数万笔交易）
。
- ​内存安全​：通过所有权系统避免内存泄漏和数据竞争，减少智能合约漏洞（如重入攻击）
。
- ​生态兼容​：Solana 运行时依赖 LLVM 优化，Rust 能无缝集成；同时支持 WASM(WebAssembly)，便于跨链扩展

#### Solana 智能合约的入口文件为什么是 lib.rs 而不是 main.rs
- 编译目标​：Solana 程序需编译为 .so 动态库，供链上节点加载执行，而 main.rs 生成二进制可执行文件无法直接部署
- 配置要求​：在 Cargo.toml 中需设置 crate-type = ["cdylib", "lib"]，cdylib 生成动态库，lib 支持本地测试依赖

#### Solana 程序中常用的宏有哪些？各自作用是什么？
- declare_id! 声明程序的唯一 Program ID
- #[program] 标记模块为程序逻辑入口
- msg! 用于链上日志输出
- #[derive(Accounts)] 自动化账户验证，减少手动检查账户权限的代码量