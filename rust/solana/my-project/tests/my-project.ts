import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { MyProject } from "../target/types/my_project";
import { Keypair } from "@solana/web3.js";

describe("my-project", () => {
  // Configure the client to use the local cluster.
  anchor.setProvider(anchor.AnchorProvider.env());

  const program = anchor.workspace.myProject as Program<MyProject>;

  it("Is initialized!", async () => {
    
    const provider = anchor.getProvider();

    // 创建新账户
    const newAccount = Keypair.generate();
    const lamports =await provider.connection.getMinimumBalanceForRentExemption(8+1024);

    // 请求空投
    const tx =await provider.connection.requestAirdrop(newAccount.publicKey, lamports);
    await provider.connection.confirmTransaction(tx);

    // 调用程序并初始化账户
    const txSignature =await program.methods
      .initialize()
      .accounts({
      myAccount: newAccount.publicKey,
      user: provider.publicKey,
      })
      .signers([newAccount])
      .rpc();

    console.log("Transaction Signature:", txSignature);

//     const tx = await program.methods.initialize().rpc();
//     console.log("Your transaction signature", tx);
  });
});
