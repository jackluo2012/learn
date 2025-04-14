### 我们需要一个mint token
```bash
spl-token create-token --url devnet --decimals 9 --mint-authority AEav14XC2m11X5F6iBRrmK7cu8L2GhD9A2QGzGUDfLYD
```
```
result :
AJhPKU6DGqKEeG6Ug5wBJFJhXtXvURybFppzbwPNowxP
```


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

### web

This is a React app that uses the Anchor generated client to interact with the Solana program.

#### Commands

Start the web app

```shell
pnpm dev
```

Build the web app

```shell
pnpm build
```
