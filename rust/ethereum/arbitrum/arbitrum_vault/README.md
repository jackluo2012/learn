### 创建 项目
```shell
cargo stylus new arbitrum_vault
```
### 使用foundry 的 anvil 开启以太坊节点
```shell
anvil 
```
### 构建程序
```shell 
cargo stylus check -e https://sepolia-rollup.arbitrum.io/rpc
cargo stylus deploy \
	--endpoint=https://sepolia-rollup.arbitrum.io/rpc \
  --private-key=$PKEY \
  --max-fee-per-gas-gwei=30
```
### 部署成功
```shell

deployed code at address: 0x48fdffe10c6f096dfac5e62be05e0a627205e1dc
deployment tx hash: 0xf5f09e15870cd3d0a77c24db3cdb8a1986c5dbb19de48966b17dbad30a90b04e     
contract activated and ready onchain with tx hash: 0xac133251ad3aaf231c5b7b04c85423f1927133e0f1a4838782a529b654c631c7

NOTE: We recommend running cargo stylus cache bid 48fdffe10c6f096dfac5e62be05e0a627205e1dc 0 to cache your activated contract in ArbOS.
Cached contracts benefit from cheaper calls. To read more about the Stylus contract cache, see
https://docs.arbitrum.io/stylus/how-tos/caching-contracts
```
```shell
cast send --rpc-url https://sepolia-rollup.arbitrum.io/rpc --private-key $PKEY 0x48fdffe10c6f096dfac5e62be05e0a627205e1dc "mint(uint256)" 88888888
```
```shell output
cast send --rpc-url https://sepolia-rollup.arbitrum.io/rpc --private-key $PKEY 0x48fdffe10c6f096dfac5e62be05e0a627205e1dc "mint(uint256)" 88888888

blockHash            0xa10470ff8e86eb35141ae2ea8fc74dbb5f2b8f18ed78eece0b3b25a420c50572
blockNumber          155620717
contractAddress
cumulativeGasUsed    1628160
effectiveGasPrice    3244470000
from                 0xE96cFDc8F44C12270aCaDA7F9140c8A99Bd185dB
gasUsed              85516
logs                 [{"address":"0x48fdffe10c6f096dfac5e62be05e0a627205e1dc","topics":["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef","0x0000000000000000000000000000000000000000000000000000000000000000","0x000000000000000000000000e96cfdc8f44c12270acada7f9140c8a99bd185db"],"data":"0x00000000000000000000000000000000000000000000000000000000054c5638","blockHash":"0xa10470ff8e86eb35141ae2ea8fc74dbb5f2b8f18ed78eece0b3b25a420c50572","blockNumber":"0x946956d","transactionHash":"0xe4197b23be93b5f782c2f4a2d653497e366ee491d7ae4d8496f681c6e903737a","transactionIndex":"0x13","logIndex":"0x5","removed":false}]
logsBloom            0x00000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000040000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000020000000000000000000800000000000000000000000010000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002000800000000000000000000000000000000000000000040000020000000000000000000000000000000000000000000000000000000008000000000
root
status               1 (success)
transactionHash      0xe4197b23be93b5f782c2f4a2d653497e366ee491d7ae4d8496f681c6e903737a
transactionIndex     19
type                 2
blobGasPrice
blobGasUsed
to                   0x48fdFfe10c6F096dfaC5E62Be05E0a627205E1Dc
gasUsedForL1         0
l1BlockNumber        8382449
timeboosted          false
```

### 部署合约的地址
```shell

deployed code at address: 0x4cbe87ce6faf8786c24aa612dbd17395034c2c24
deployment tx hash: 0x63099eb1620eff8ef9560315fae3dfd8d1d0a15f21c8f5e869fa9e608fcf8b17
Error: stylus deploy failed
```

### 激活合约
```shell
cargo stylus activate --endpoint=https://sepolia-rollup.arbitrum.io/rpc   --private-key=$PKEY --address 0x4cbe87ce6faf8786c24aa612dbd17395034c2c24
```

### 设置存存款地址
```shell
cast send --rpc-url https://sepolia-rollup.arbitrum.io/rpc --private-key $PKEY 0x4cbe87ce6faf8786c24aa612dbd17395034c2c24 "setAsset(address)" 0x48fdFfe10c6F096dfaC5E62Be05E0a627205E1Dc
```

```output
cast send --rpc-url https://sepolia-rollup.arbitrum.io/rpc --private-key $PKEY 0x4cbe87ce6faf8786c24aa612dbd17395034c2c24 "setAsset(address)" 0x4cbe87ce6faf8786c24aa612dbd17395034c2c24

blockHash            0x2db9e841302c8783a4dd75248f666663ea0630e52c8541cae2443ee652b3f04b
blockNumber          155934205
contractAddress
cumulativeGasUsed    891456
effectiveGasPrice    100000000
from                 0xE96cFDc8F44C12270aCaDA7F9140c8A99Bd185dB
gasUsed              65629
logs                 []
logsBloom            0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
root
status               1 (success)
transactionHash      0x5cb7ed17d5f1aefff583a5069ec0251e288dcf3c0cb9adbcd7c42b7189243b34
transactionIndex     19
type                 2
blobGasPrice
blobGasUsed
to                   0x4CBE87CE6faF8786C24aa612DBd17395034C2c24
gasUsedForL1         0
l1BlockNumber        8388998
timeboosted          false
```

新部署的合约地址：0xe67216fe214832e36e8b32d5632b855c68bdd9fb
代币合约的地址：0x48fdffe10c6f096dfac5e62be05e0a627205e1dc

```shell
cast send --rpc-url https://sepolia-rollup.arbitrum.io/rpc --private-key $PKEY 0xe67216fe214832e36e8b32d5632b855c68bdd9fb "setAsset(address)" 0x48fdffe10c6f096dfac5e62be05e0a627205e1dc
```



### 存款
```shell
cast send --rpc-url https://sepolia-rollup.arbitrum.io/rpc \
  --private-key $PKEY \
  0x4cbe87ce6faf8786c24aa612dbd17395034c2c24 \
  "approve(address,uint256)" 0x4cbe87ce6faf8786c24aa612dbd17395034c2c24 88888888



cast send --rpc-url https://sepolia-rollup.arbitrum.io/rpc --private-key $PKEY 0xe67216fe214832e36e8b32d5632b855c68bdd9fb "deposit(uint256)" 88888888
```

### 新合约地址
```bash
deployed code at address: 0x9d4ea7f4a8732c305873afc8c2175c67b6e38a00
deployment tx hash: 0x66c4025f436cdb49de39d43e4c58cd7b7976003adf7a0811938fa651de2d88de
contract activated and ready onchain with tx hash: 0xbcba06d52e22781ed30fc32ea3c19f44b84f52281ccd5652999750cb435f73b8
```





![Image](./header.png)

# Stylus Hello World

Project starter template for writing Arbitrum Stylus programs in Rust using the [stylus-sdk](https://github.com/OffchainLabs/stylus-sdk-rs). It includes a Rust implementation of a basic counter Ethereum smart contract:

```js
// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

contract Counter {
    uint256 public number;

    function setNumber(uint256 newNumber) public {
        number = newNumber;
    }

    function increment() public {
        number++;
    }
}
```

To set up more minimal example that still uses the Stylus SDK, use `cargo stylus new --minimal <YOUR_PROJECT_NAME>` under [OffchainLabs/cargo-stylus](https://github.com/OffchainLabs/cargo-stylus).

## Quick Start 

Install [Rust](https://www.rust-lang.org/tools/install), and then install the Stylus CLI tool with Cargo

```bash
cargo install --force cargo-stylus cargo-stylus-check
```

Add the `wasm32-unknown-unknown` build target to your Rust compiler:

```
rustup target add wasm32-unknown-unknown
```

You should now have it available as a Cargo subcommand:

```bash
cargo stylus --help
```

Then, clone the template:

```
git clone https://github.com/OffchainLabs/stylus-hello-world && cd stylus-hello-world
```

### Testnet Information

All testnet information, including faucets and RPC endpoints can be found [here](https://docs.arbitrum.io/stylus/reference/testnet-information).

### ABI Export

You can export the Solidity ABI for your program by using the `cargo stylus` tool as follows:

```bash
cargo stylus export-abi
```

which outputs:

```js
/**
 * This file was automatically generated by Stylus and represents a Rust program.
 * For more information, please see [The Stylus SDK](https://github.com/OffchainLabs/stylus-sdk-rs).
 */

interface Counter {
    function setNumber(uint256 new_number) external;

    function increment() external;
}
```

Exporting ABIs uses a feature that is enabled by default in your Cargo.toml:

```toml
[features]
export-abi = ["stylus-sdk/export-abi"]
```

## Deploying

You can use the `cargo stylus` command to also deploy your program to the Stylus testnet. We can use the tool to first check
our program compiles to valid WASM for Stylus and will succeed a deployment onchain without transacting. By default, this will use the Stylus testnet public RPC endpoint. See here for [Stylus testnet information](https://docs.arbitrum.io/stylus/reference/testnet-information)

```bash
cargo stylus check
```

If successful, you should see:

```bash
Finished release [optimized] target(s) in 1.88s
Reading WASM file at stylus-hello-world/target/wasm32-unknown-unknown/release/stylus-hello-world.wasm
Compressed WASM size: 8.9 KB
Program succeeded Stylus onchain activation checks with Stylus version: 1
```

Next, we can estimate the gas costs to deploy and activate our program before we send our transaction. Check out the [cargo-stylus](https://github.com/OffchainLabs/cargo-stylus) README to see the different wallet options for this step:

```bash
cargo stylus deploy \
  --private-key-path=<PRIVKEY_FILE_PATH> \
  --estimate-gas
```

You will then see the estimated gas cost for deploying before transacting:

```bash
Deploying program to address e43a32b54e48c7ec0d3d9ed2d628783c23d65020
Estimated gas for deployment: 1874876
```

The above only estimates gas for the deployment tx by default. To estimate gas for activation, first deploy your program using `--mode=deploy-only`, and then run `cargo stylus deploy` with the `--estimate-gas` flag, `--mode=activate-only`, and specify `--activate-program-address`.


Here's how to deploy:

```bash
cargo stylus deploy \
  --private-key-path=<PRIVKEY_FILE_PATH>
```

The CLI will send 2 transactions to deploy and activate your program onchain.

```bash
Compressed WASM size: 8.9 KB
Deploying program to address 0x457b1ba688e9854bdbed2f473f7510c476a3da09
Estimated gas: 1973450
Submitting tx...
Confirmed tx 0x42db…7311, gas used 1973450
Activating program at address 0x457b1ba688e9854bdbed2f473f7510c476a3da09
Estimated gas: 14044638
Submitting tx...
Confirmed tx 0x0bdb…3307, gas used 14044638
```

Once both steps are successful, you can interact with your program as you would with any Ethereum smart contract.

## Calling Your Program

This template includes an example of how to call and transact with your program in Rust using [ethers-rs](https://github.com/gakonst/ethers-rs) under the `examples/counter.rs`. However, your programs are also Ethereum ABI equivalent if using the Stylus SDK. **They can be called and transacted with using any other Ethereum tooling.**

By using the program address from your deployment step above, and your wallet, you can attempt to call the counter program and increase its value in storage:

```rs
abigen!(
    Counter,
    r#"[
        function number() external view returns (uint256)
        function setNumber(uint256 number) external
        function increment() external
    ]"#
);
let counter = Counter::new(address, client);
let num = counter.number().call().await;
println!("Counter number value = {:?}", num);

let _ = counter.increment().send().await?.await?;
println!("Successfully incremented counter via a tx");

let num = counter.number().call().await;
println!("New counter number value = {:?}", num);
```

Before running, set the following env vars or place them in a `.env` file (see: [.env.example](./.env.example)) in this project:

```
RPC_URL=https://sepolia-rollup.arbitrum.io/rpc
STYLUS_CONTRACT_ADDRESS=<the onchain address of your deployed program>
PRIV_KEY_PATH=<the file path for your priv key to transact with>
```

Next, run:

```
cargo run --example counter --target=<YOUR_ARCHITECTURE>
```

Where you can find `YOUR_ARCHITECTURE` by running `rustc -vV | grep host`. For M1 Apple computers, for example, this is `aarch64-apple-darwin` and for most Linux x86 it is `x86_64-unknown-linux-gnu`

## Build Options

By default, the cargo stylus tool will build your project for WASM using sensible optimizations, but you can control how this gets compiled by seeing the full README for [cargo stylus](https://github.com/OffchainLabs/cargo-stylus). If you wish to optimize the size of your compiled WASM, see the different options available [here](https://github.com/OffchainLabs/cargo-stylus/blob/main/OPTIMIZING_BINARIES.md).

## Peeking Under the Hood

The [stylus-sdk](https://github.com/OffchainLabs/stylus-sdk-rs) contains many features for writing Stylus programs in Rust. It also provides helpful macros to make the experience for Solidity developers easier. These macros expand your code into pure Rust code that can then be compiled to WASM. If you want to see what the `stylus-hello-world` boilerplate expands into, you can use `cargo expand` to see the pure Rust code that will be deployed onchain.

First, run `cargo install cargo-expand` if you don't have the subcommand already, then:

```
cargo expand --all-features --release --target=<YOUR_ARCHITECTURE>
```

Where you can find `YOUR_ARCHITECTURE` by running `rustc -vV | grep host`. For M1 Apple computers, for example, this is `aarch64-apple-darwin`.

## License

This project is fully open source, including an Apache-2.0 or MIT license at your choosing under your own copyright.
