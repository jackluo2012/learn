import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
// import { AnchorBac } from "../target/types/anchor_bac";
import { BullsAndCows } from "../target/types/bulls_and_cows";

describe("anchor_bac", () => {
  // Configure the client to use the local cluster.
  anchor.setProvider(anchor.AnchorProvider.env());

  const program = anchor.workspace.bulls_and_cows as Program<BullsAndCows>;
  const seeds = Buffer.from("guessing pda");
  const guessingPdaPubkey = anchor.web3.PublicKey.findProgramAddressSync(
    [seeds],
    program.programId
  )[0];
  // it("Is initialized!", async () => {
  //   // Add your test here.
  //   const tx = await program.methods.guess(2).rpc();
  //   console.log("Your transaction signature", tx);
  // });
  it("Is guess!", async () => {
    // Add your test here.
    const tx1 = await program.methods.guess(1)
    .accounts({
      guessingAccount: guessingPdaPubkey,
      payer: anchor.getProvider().publicKey,
      systemProgram: anchor.web3.SystemProgram.programId,
    })
    .rpc();
    console.log("Your transaction signature", tx1);
    
  });
});
