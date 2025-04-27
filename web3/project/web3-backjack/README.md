This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-wagmi`](https://github.com/wevm/wagmi/tree/main/packages/create-wagmi).


### 创建
```shell
pnpm create wagmi
pnpm i
pnpm dev
```


### 使用 mongodb 存储数据


####
- 创建一个铵钮，用点击后，
- 发送一个验证的请求，通过它的钱包的信息进行签名
- 然后把它的信息签名和信息都发送给后端，后端对他的签名进行验证,他是不是这个钱包的主人，如果是，返回一个正确的信息
- 如果没有完成验证的话，就不会加载


### 什么是电子签名，怎么验证电子签名
- 每个钱包都是由两部份组成的
- 一是是一个公钥，一个是私钥
- 用私钥加密的信息，用公钥进行解密