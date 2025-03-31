import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { MyProject } from "../target/types/my_project";
import { Keypair, SystemProgram, PublicKey, LAMPORTS_PER_SOL } from "@solana/web3.js";

describe("my-project", () => {
  // Configure the client to use the local cluster.
  anchor.setProvider(anchor.AnchorProvider.env());

  const program = anchor.workspace.myProject as Program<MyProject>;

  it("Is initialized!", async () => {
    try {
      const provider = anchor.getProvider();

      // 创建新账户
      const newAccount = Keypair.generate();
      const lamports = await provider.connection.getMinimumBalanceForRentExemption(8 + 1024);

      // 请求空投
      const tx = await provider.connection.requestAirdrop(newAccount.publicKey, lamports);
      await provider.connection.confirmTransaction(tx);

      // 调用程序并初始化账户
      const txSignature = await program.methods
        .initialize()
        .accounts({
          myAccount: newAccount.publicKey,
          user: provider.wallet.publicKey,
        })
        .signers([newAccount])
        .rpc();

      console.log("Transaction Signature:", txSignature);
    } catch (err) {
      console.error("Error during initialization:", err);
    }
  });

  it("Create and fund account owned by our program", async () => {
    try {
      const provider = anchor.getProvider();
      const payer = provider.wallet;

      // 创建新账户 programOwnedAccount
      const programOwnedAccount = Keypair.generate();

      // 分配 lamports（1 SOL）
      const lamports = 1 * LAMPORTS_PER_SOL;

      // 创建账户并设置 owner 为程序
      const createAccountIx = SystemProgram.createAccount({
        fromPubkey: payer.publicKey, // 我的钱包地址
        newAccountPubkey: programOwnedAccount.publicKey, // 新账户地址
        space: 0, // 新账户的存储空间 (0 表示不存储额外数据)
        lamports, // 存入新账户的初始余额 (1 SOL)
        programId: program.programId, // 设置 owner 为自定义程序的 ID
      });

      // 构建交易
      const tx = new anchor.web3.Transaction().add(createAccountIx);

      // 签名并发送交易
      const txSignature = await provider.sendAndConfirm(tx, [programOwnedAccount]);
      console.log("Created program-owned account. Transaction Signature:", txSignature);

      // 转账逻辑：从 programOwnedAccount 转出 SOL 到接收者的钱包
      const recipient = Keypair.generate(); // 接收者的钱包地址
      const transferIx = SystemProgram.transfer({
        fromPubkey: programOwnedAccount.publicKey, // 转出账户
        toPubkey: recipient.publicKey, // 接收者账户
        lamports: 0.5 * LAMPORTS_PER_SOL, // 转出 0.5 SOL
      });

      // 构建转账交易
      const transferTx = new anchor.web3.Transaction().add(transferIx);

      // 签名并发送转账交易
      const transferTxSignature = await provider.sendAndConfirm(transferTx, [programOwnedAccount]);
      console.log("Transferred 0.5 SOL. Transaction Signature:", transferTxSignature);

      // 验证接收者余额
      const recipientBalance = await provider.connection.getBalance(recipient.publicKey);
      console.log("Recipient Balance:", recipientBalance / LAMPORTS_PER_SOL, "SOL");
    } catch (err) {
      console.error("Error during account creation and funding:", err);
    }
  });

  it("Transfer SOL using CPI", async () => {
    try {
      const provider = anchor.getProvider();

      // 创建一个由程序管理的账户
      const programOwnedAccount = Keypair.generate();
      const lamports = await provider.connection.getMinimumBalanceForRentExemption(0);

      // 创建账户并设置 owner 为程序
      const createAccountIx = SystemProgram.createAccount({
        fromPubkey: provider.wallet.publicKey, // 我的钱包地址
        newAccountPubkey: programOwnedAccount.publicKey, // 新账户地址
        space: 0, // 不需要额外存储空间
        lamports, // 存入账户的初始余额
        programId: program.programId, // 设置 owner 为自定义程序的 ID
      });

      // 构建交易
      const tx = new anchor.web3.Transaction().add(createAccountIx);

      // 签名并发送交易
      await provider.sendAndConfirm(tx, [programOwnedAccount]);
      console.log("Created program-owned account.");

      // 创建接收者账户
      const recipient = Keypair.generate();

      // 调用程序的 transferSolWithCpi 方法
      const txSignature = await program.methods
        .transferSolWithCpi(new anchor.BN(0.5 * LAMPORTS_PER_SOL)) // 转账金额
        .accounts({
          payer: programOwnedAccount.publicKey, // 使用程序管理的账户作为 payer
          recipient: recipient.publicKey, // 接收者账户
          systemProgram: SystemProgram.programId, // 系统程序
        })
        .signers([programOwnedAccount]) // 签名 programOwnedAccount
        .rpc();

      console.log("CPI Transfer Transaction Signature:", txSignature);

      // 验证接收者余额
      const recipientBalance = await provider.connection.getBalance(recipient.publicKey);
      console.log("Recipient Balance after CPI Transfer:", recipientBalance / LAMPORTS_PER_SOL, "SOL");
    } catch (err) {
      console.error("Error during CPI transfer:", err);
    }
  });
});
