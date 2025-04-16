#### 这是一个代币彩票 的项目
- 创建了一个代币彩票
- 你购买的作品集中的代币
- 才能进行抽奖
- 这些代币产生了费用 进入了一个 Lottery Pot 的帐户，
- 该彩票底池帐户后来被使用
- 在我们的领取获胜者时领取奖金
- 为了弄清楚谁是赢家，我们使用了 Switchboard 随机功能 ，
- 我们使用了一些链上的随机性
- 真正的项目是用链下数据 
- 但我们使用了commit reveal 函数，这样就很容易验证
- 我们用它来创建随机 性，选择我们的获胜者
- 我们以无信任的方式创建它
- 并将奖金给该获胜者


#### 如何没有，请将 主网的程序 
[使用主网帐户和程序](https://solana.com/zh/developers/cookbook/development/using-mainnet-accounts-programs)
```
metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s

```


#### Install Dependencies

```shell
pnpm install
```

#### Start the web app

```
pnpm dev
```

## Apps

### anchor

This is a Solana program written in Rust using the Anchor framework.

#### Commands

You can use any normal anchor commands. Either move to the `anchor` directory and run the `anchor` command or prefix the
command with `pnpm`, eg: `pnpm anchor`.

#### Sync the program id:

Running this command will create a new keypair in the `anchor/target/deploy` directory and save the address to the
Anchor config file and update the `declare_id!` macro in the `./src/lib.rs` file of the program.

You will manually need to update the constant in `anchor/lib/counter-exports.ts` to match the new program id.

```shell
pnpm anchor keys sync
```

#### Build the program:

```shell
pnpm anchor-build
```

#### Start the test validator with the program deployed:

```shell
pnpm anchor-localnet
```

#### Run the tests

```shell
pnpm anchor-test
```

#### Deploy to Devnet

```shell
pnpm anchor deploy --provider.cluster devnet
```

