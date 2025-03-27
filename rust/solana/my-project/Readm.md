## 如何报错

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
```
#### 创建 钱包
```bash
solana-keygen new

# 钱包地址
solana address

### 获取余额

solana balance
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

# 部署
anchor deploy
```
