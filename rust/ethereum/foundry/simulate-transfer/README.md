### 分叉以太坊区块链
```shell
anvil --fork-url YOUR_ENDPOINT_URL --fork-block-number 19000000

anvil --fork-url https://eth-mainnet.g.alchemy.com/v2/-t6rLvfkU794BdiDw6MPHSFgFag_ilxQ --fork-block-number 19000000
```

```shell output
Wallet
==================
Mnemonic:          test test test test test test test test test test test junk
Derivation path:   m/44'/60'/0'/0/


Fork
==================
Endpoint:       https://eth-mainnet.g.alchemy.com/v2/-t6rLvfkU794BdiDw6MPHSFgFag_ilxQ
Block number:   19000000
Block hash:     0xcf384012b91b081230cdf17a3f7dd370d8e67056058af6b272b3d54aa2714fac
Chain ID:       1
```

### 进行测试
```shell
forge test --rpc-url http://127.0.0.1:8545/ --match-path test/Counter.t.sol -vv
```
测试结果如下：
```shell output
[⠒] Compiling...
[⠘] Compiling 21 files with Solc 0.8.20
[⠒] Solc 0.8.20 finished in 691.86ms
Compiler run successful!

Ran 1 test for test/Counter.t.sol:PEPETransferTest
[PASS] testPEPETransfer() (gas: 37676)
Logs:
  PEPE balance of recipient before:  84320755095486852230203257
  PEPE balance of recipient after:  84320755095486852240203257

Suite result: ok. 1 passed; 0 failed; 0 skipped; finished in 3.62s (2.03s CPU time)

Ran 1 test suite in 3.63s (3.62s CPU time): 1 tests passed, 0 failed, 0 skipped (1 total tests)
```