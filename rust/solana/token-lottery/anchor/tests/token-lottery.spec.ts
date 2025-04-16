import * as anchor from '@coral-xyz/anchor'
import { Program } from '@coral-xyz/anchor'
import { Keypair } from '@solana/web3.js'
import { TokenLottery } from '../target/types/token_lottery'
import { TOKEN_PROGRAM_ID } from '@solana/spl-token';


describe('token-lottery', () => {
  // Configure the client to use the local cluster.
  const provider = anchor.AnchorProvider.env()
  anchor.setProvider(provider)
  const payer = provider.wallet as anchor.Wallet
  
  const program = anchor.workspace.token_lottery as Program<TokenLottery>

  const tokenlotteryKeypair = Keypair.generate()

  async function buyTicket() {
    const buyTicketIx = await program.methods
    .buyTicket().accounts({
      tokenProgram: TOKEN_PROGRAM_ID,
    }).instruction();

    const computeIx = anchor.web3.ComputeBudgetProgram.setComputeUnitLimit({
      units: 1000000,
    });

    const priorityIx = anchor.web3.ComputeBudgetProgram.setComputeUnitPrice({
      microLamports: 1,
    });

    const blockhashWithContext = await provider.connection.getLatestBlockhash();
    const tx = new anchor.web3.Transaction({
      feePayer: provider.wallet.publicKey,
      blockhash:blockhashWithContext.blockhash,
      lastValidBlockHeight: blockhashWithContext.lastValidBlockHeight,
    }).add(buyTicketIx)
    .add(computeIx);

    const signature  =await anchor.web3.sendAndConfirmTransaction(
      provider.connection,
      tx, 
      [payer.payer],
      {skipPreflight: true}
    );
    console.log('signature', signature);
  }

  it('Should init config', async () => {
    const configIx = await program.methods.initializeConfig(
      new anchor.BN(0),
      new anchor.BN(1844625290),
      new anchor.BN(10000)
    ).instruction();
    
    const blockhashWithContext = await provider.connection.getLatestBlockhash();
    const tx = new anchor.web3.Transaction({
      feePayer: provider.wallet.publicKey,
      blockhash: blockhashWithContext.blockhash,
      lastValidBlockHeight: blockhashWithContext.lastValidBlockHeight,
    })
    .add(configIx);
    
    // 发送交易
    const signature = await anchor.web3.sendAndConfirmTransaction(
      provider.connection,
      tx, 
      [payer.payer],
      {skipPreflight: true}
    );
     
    console.log('signature', signature);


    const initLotteryIx = await program.methods
    .initializeLottery().accounts({
      tokenProgram: TOKEN_PROGRAM_ID,
    }).instruction();

    const initLotteryTx = new anchor.web3.Transaction({
      feePayer: provider.wallet.publicKey,
      blockhash: blockhashWithContext.blockhash,
      lastValidBlockHeight: blockhashWithContext.lastValidBlockHeight,
    })
    .add(initLotteryIx);

    const initLotterySignature = await anchor.web3.sendAndConfirmTransaction(
      provider.connection,
      initLotteryTx, 
      [payer.payer],
      {skipPreflight: true}
    );
    console.log('initLotterySignature ', initLotterySignature);

    await buyTicket();

  })
});// end of describe
