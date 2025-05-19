### 安装依赖

```shell
forge install transmissions11/solmate Openzeppelin/openzeppelin-contracts
```

```shell
forge build
```

#### 运行测试
```shell
anvil
```
### 
```shell
export RPC_URL=http://127.0.0.1:8545/
export PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
```

###  NFT 合约的部署
```shell
forge create NFT --broadcast --rpc-url=$RPC_URL --private-key=$PRIVATE_KEY --constructor-args NFT NFT
```
```bash ERC20 合约的部署
[⠢] Compiling...
No files changed, compilation skipped
Deployer: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
Deployed to: 0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512
Transaction hash: 0x98203d06bd219e886cd0aebcf006e4de4eb2695bc967ffaddb080e5d8fbc9286
```


### 发送交易和获取链上数据
```bash
cast send --rpc-url=$RPC_URL <contractAddress>  "mintTo(address)" <mintAddress> --private-key=$PRIVATE_KEY

cast send --rpc-url=$RPC_URL 0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512  "mintTo(address)" 0x70997970C51812dc3A010C7d01b50e0d17dc79C8 --private-key=$PRIVATE_KEY
```
```bash out put
blockHash            0x2c70b697dfa43d2cc82cb98aebe80a46febd60255809f0061177ed7df58ef9e6
blockNumber          3
contractAddress
cumulativeGasUsed    93751
effectiveGasPrice    793317307
from                 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
gasUsed              93751
logs                 [{"address":"0xe7f1725e7734ce288f8367e1bb143e90bb3f0512","topics":["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef","0x0000000000000000000000000000000000000000000000000000000000000000","0x00000000000000000000000070997970c51812dc3a010c7d01b50e0d17dc79c8","0x0000000000000000000000000000000000000000000000000000000000000001"],"data":"0x","blockHash":"0x2c70b697dfa43d2cc82cb98aebe80a46febd60255809f0061177ed7df58ef9e6","blockNumber":"0x3","blockTimestamp":"0x682afb4e","transactionHash":"0x394607808e7db66612ab0f8e0b0a08c142d30e6e8e2c180308ae03bf74d10f70","transactionIndex":"0x0","logIndex":"0x0","removed":false}]
logsBloom            0x00000000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000040000000000000000000000000008000000000000000000040000000000000000000000000800020000000000000000000800000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002000000000000000000001000000000000000000000000000000060000000000000000000000000000000000001000000000000800000000000000000
root
status               1 (success)
transactionHash      0x394607808e7db66612ab0f8e0b0a08c142d30e6e8e2c180308ae03bf74d10f70
transactionIndex     0
type                 2
blobGasPrice         1
blobGasUsed
to                   0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512
```

### 检查铸造出来的 NFT 持有者是不是我们指定的地址

```bash
cast call --rpc-url=$RPC_URL --private-key=$PRIVATE_KEY <contractAddress> "ownerOf(uint256)" 1

cast call --rpc-url=$RPC_URL --private-key=$PRIVATE_KEY 0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512 "ownerOf(uint256)" 1
```
```bash out put
0x00000000000000000000000070997970c51812dc3a010c7d01b50e0d17dc79c8
```