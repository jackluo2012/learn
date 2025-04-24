import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { Stablecoin } from "../target/types/stablecoin";
import { PythSolanaReceiver } from "@pythnetwork/pyth-solana-receiver";

describe("stablecoin", () => {
  
  const provider = anchor.AnchorProvider.env();
  
  // Configure the client to use the local cluster.
  
  const connection = provider.connection;
  const wallet = provider.wallet as anchor.Wallet; 
  anchor.setProvider(provider);
  const program = anchor.workspace.stablecoin as Program<Stablecoin>;
  //使用pyth Solana 接收器
  const pythSolanaReceiver = new PythSolanaReceiver({connection, wallet});

  const SOL_PRICE_FEED_ID = "0xef0d8b6fda2ceba41da15d4095d1da392a0d2f8ed0c6c7bc0f4cfac8c280b56d";

  const solUsdPriceFeedAccount = pythSolanaReceiver.getPriceFeedAccountAddress(0,SOL_PRICE_FEED_ID);
  // 获取 抵押账户的pda
 const [collateralAccount] = anchor.web3.PublicKey.findProgramAddressSync(
  [Buffer.from("collateral"), wallet.publicKey.toBuffer()],
  program.programId,
 );
  it("Is initialized!", async () => {
    // 初始化我们的配置
    const tx = await program.methods.initializeConfig().accounts({}).rpc({skipPreflight: true,commitment:"confirmed"});
    
    console.log("Your transaction signature", tx);
  });
  // 我们存入sol 铸造usdc.
  it("Deposit Collateral AND mint usdc", async () => {
    // 我们存入 1 SOL
    const amountCollateral = 1_000_000_000;//new anchor.BN(1 * anchor.web3.LAMPORTS_PER_SOL);
    const amountToMint = 1_000_000;
    // 创建 指令
    const tx = await program.methods.depositCollateralAndMintTokens(
      new anchor.BN(amountCollateral),
      new anchor.BN(amountToMint),
    ).accounts({priceUpdate:solUsdPriceFeedAccount}).rpc({skipPreflight: true,commitment:"confirmed"});
    console.log("Your transaction signature", tx);
  });
  // 赎回抵押器，并销销毁 USDC
  it("Redeem Collateral AND burn usdc", async () => {
    // 我们存入 1 SOL
    const amountCollateral = 500_000_000;//new anchor.BN(1 * anchor.web3.LAMPORTS_PER_SOL);
    const amountToMint = 500_000_000;
    // 创建 指令
    const tx = await program.methods.redeemCollateralAndBurnTokens(
      new anchor.BN(amountCollateral),
      new anchor.BN(amountToMint),
    ).accounts({priceUpdate:solUsdPriceFeedAccount}).rpc({skipPreflight: true,commitment:"confirmed"});
    console.log("Your transaction signature", tx);
  });
  //更新配置,改变最低的健康因素
  it("Update Config", async () => {
    // 我们存入 1 SOL
    const tx = await program.methods.updateConfig(
      new anchor.BN(100),
    ).accounts({}).rpc({skipPreflight: true,commitment:"confirmed"});
    console.log("Your transaction signature", tx);
  });
  // 进行清算
  it("Liquidate", async () => {
    const amounttoBurn = 500_000_000;

    const tx = await program.methods.liquidate(
      new anchor.BN(amounttoBurn),
    ).accounts({
      collateralAccount,
      priceUpdate:solUsdPriceFeedAccount,
    }).rpc({skipPreflight: true,commitment:"confirmed"});
    console.log("Your transaction signature", tx);
  });
  // 更新配置到 正常
  it("Update Config", async () => {
    // 我们存入 1 SOL
    const tx = await program.methods.updateConfig(
      new anchor.BN(1),
    ).accounts({}).rpc({skipPreflight: true,commitment:"confirmed"});
    console.log("Your transaction signature", tx);
  });

});
