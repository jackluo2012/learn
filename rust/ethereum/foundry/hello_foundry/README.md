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


```shell
# 部署并验证合约
forge script script/MyToken.s.sol:MyTokenScript --rpc-url $SEPOLIA_RPC_URL --broadcast --verify -vvvv

#部署结果
[部署后的地址](https://sepolia.etherscan.io/address/0xb9298dde9152005fcd90dc9c6f7d294bdc403568)



jackluo@jackluo-window:/mnt/d/works/learn/rust/ethereum/foundry/hello_foundry$ forge script script/MyToken.s.sol:MyTokenScript --rpc-url $SEPOLIA_RPC_URL --broadcast --verify -vvvv
[⠢] Compiling...
No files changed, compilation skipped
Traces:
  [1059055] MyTokenScript::run()
    ├─ [0] VM::envUint("PRIVATE_KEY") [staticcall]
    │   └─ ← [Return] <env var value>
    ├─ [0] VM::startBroadcast(<pk>)
    │   └─ ← [Return]
    ├─ [1020188] → new MyToken@0xb9298dDe9152005fcd90dc9C6f7d294bDC403568
    │   ├─ emit Transfer(from: 0x0000000000000000000000000000000000000000, to: 0xE96cFDc8F44C12270aCaDA7F9140c8A99Bd185dB, value: 1000000000000000000 [1e18])
    │   └─ ← [Return] 4516 bytes of code
    ├─ [0] VM::stopBroadcast()
    │   └─ ← [Return]
    └─ ← [Stop]


Script ran successfully.

## Setting up 1 EVM.
==========================
Simulated On-chain Traces:

  [1020188] → new MyToken@0xb9298dDe9152005fcd90dc9C6f7d294bDC403568
    ├─ emit Transfer(from: 0x0000000000000000000000000000000000000000, to: 0xE96cFDc8F44C12270aCaDA7F9140c8A99Bd185dB, value: 1000000000000000000 [1e18])
    └─ ← [Return] 4516 bytes of code


==========================

Chain 11155111

Estimated gas price: 0.002093674 gwei

Estimated total gas used for script: 1521104

Estimated amount required: 0.000003184695896096 ETH

==========================

##### sepolia
✅  [Success] Hash: 0x28559283108f4c99efc2ed5d70cdcf93227ddd3518275bedb7ff717b8896dadc
Contract Address: 0xb9298dDe9152005fcd90dc9C6f7d294bDC403568
Block: 8350498
Paid: 0.00000187179686736 ETH (1170080 gas * 0.001599717 gwei)

✅ Sequence #1 on sepolia | Total Paid: 0.00000187179686736 ETH (1170080 gas * avg 0.001599717 gwei)                                                                                                                                                                                                                  
                                                                                                                                                                                                                                                                                                                      
                                                                                                                                                                                                                                                                                                                      
==========================

ONCHAIN EXECUTION COMPLETE & SUCCESSFUL.
##
Start verification for (1) contracts
Start verifying contract `0xb9298dDe9152005fcd90dc9C6f7d294bDC403568` deployed on sepolia
EVM version: cancun
Compiler version: 0.8.29
Constructor args: 000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000120000000000000000000000000000000000000000000000000de0b6b3a764000000000000000000000000000000000000000000000000000000000000000000074d79546f6b656e0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000024d54000000000000000000000000000000000000000000000000000000000000

Submitting verification for [src/MyToken.sol:MyToken] 0xb9298dDe9152005fcd90dc9C6f7d294bDC403568.
Warning: Could not detect the deployment.; waiting 5 seconds before trying again (4 tries remaining)

Submitting verification for [src/MyToken.sol:MyToken] 0xb9298dDe9152005fcd90dc9C6f7d294bDC403568.
Warning: Could not detect the deployment.; waiting 5 seconds before trying again (3 tries remaining)

Submitting verification for [src/MyToken.sol:MyToken] 0xb9298dDe9152005fcd90dc9C6f7d294bDC403568.
Warning: Could not detect the deployment.; waiting 5 seconds before trying again (2 tries remaining)

Submitting verification for [src/MyToken.sol:MyToken] 0xb9298dDe9152005fcd90dc9C6f7d294bDC403568.
Warning: Could not detect the deployment.; waiting 5 seconds before trying again (1 tries remaining)

Submitting verification for [src/MyToken.sol:MyToken] 0xb9298dDe9152005fcd90dc9C6f7d294bDC403568.
Warning: Could not detect the deployment.; waiting 5 seconds before trying again (0 tries remaining)

Submitting verification for [src/MyToken.sol:MyToken] 0xb9298dDe9152005fcd90dc9C6f7d294bDC403568.
Submitted contract for verification:
        Response: `OK`
        GUID: `qfnd8hqerlx6hftdnkiu9wj56vvgxx26gbaucqytzemkyytf6i`
        URL: https://sepolia.etherscan.io/address/0xb9298dde9152005fcd90dc9c6f7d294bdc403568
Contract verification status:
Response: `OK`
Details: `Pass - Verified`
Contract successfully verified
All (1) contracts were verified!

Transactions saved to: /mnt/d/works/learn/rust/ethereum/foundry/hello_foundry/broadcast/MyToken.s.sol/11155111/run-latest.json

Sensitive values saved to: /mnt/d/works/learn/rust/ethereum/foundry/hello_foundry/cache/MyToken.s.sol/11155111/run-latest.json


```





https://book.getfoundry.sh/

## Usage


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
