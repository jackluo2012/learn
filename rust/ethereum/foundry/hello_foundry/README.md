## Foundry

```shell
source .env


// 区块链 RPC 节点地址
SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/mv
// 钱包私钥 私钥前的 0x 开头
PRIVATE_KEY=0xa373526
// 区块链浏览器的 API KEY TOKEN
ETHERSCAN_API_KEY=MRMRHYZ8R8UC
```

https://book.getfoundry.sh/

## Usage
https://sepolia.etherscan.io/address/0xb9298dde9152005fcd90dc9c6f7d294bdc403568

### Build

```shell
$ forge build
```

### Test

```shell
$ forge test
```

### Format

```shell
$ forge fmt
```

### Gas Snapshots

```shell
$ forge snapshot
```

### Anvil

```shell
$ anvil
```

### Deploy

```shell
$ forge script script/Counter.s.sol:CounterScript --rpc-url <your_rpc_url> --private-key <your_private_key>
```

### Cast

```shell
$ cast <subcommand>
```

### Help

```shell
$ forge --help
$ anvil --help
$ cast --help
```
