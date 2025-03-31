### 创建 solana 项目
```bash
anchor init my-project
## 如果需要rust 做测试
anchor init --test-template rust my-project

### Rust 测试文件生成在 /tests/src/test_initialize.rs。
```


## 如果报错

```bash
error: rustc 1.79.0-dev is not supported by the following package:

                 Note that this is the rustc version that ships with Solana tools and not your system's rustc version. Use `solana-install update` or head over to https://docs.solanalabs.com/cli/install to install a newer version.
  bytemuck_derive@1.9.2 requires rustc 1.84
Either upgrade rustc or select compatible dependency versions with
`cargo update <name>@<current-ver> --precise <compatible-ver>`
where `<compatible-ver>` is the latest version supporting rustc 1.79.0-dev
```

```bash
# 当前的解决方法是降级到 bytemuck_derive 1.8.1 
cargo update -p bytemuck_derive@1.9.2 --precise 1.8.1
```

### solana 配置
```bash
solana config get
# 设置开发网络
solana config set --url devnet
solana config set -um    # For mainnet-beta
solana config set -ud    # For devnet
solana config set -ul    # For localhost
solana config set -ut    # For testnet
```
#### 创建 钱包
```bash
solana-keygen new

# 1. 生成solana钱包地址
solana-keygen new -o ~/.config/solana/id.json

# 钱包地址
solana address

### 获取余额

solana balance
```
### 启动solana 本地网络
```
# 这部很重要
cd ~/
solana-test-validator
```


### anchor cli basics
```bash
# 创建
anchor init  my-project
cd my-project
# 编译
anchor build

# 测试
anchor test

## 跳过本地验证节点
anchor test --skip-local-validator

# 部署
anchor deploy
```
### 以下是常见错误 
- 如何处理 Program ID 不匹配问题
```bash
rm target/deploy/<program_name>.json
anchor test --skip-local-validator

anchor keys sync

```

### 修改代码 后 ，内容增多 ，需要扩展数据空间
```bash
Error: Buffer account data size (180989) is smaller than the minimum size (202101)
```

```bash
solana program extend 27fJa3G1hbuJbAUMxREDU62TemBbVCCxPB49tC3ybfDr 1440
```


