import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { QuickTacToe } from "../target/types/quick_tac_toe";
// import idl from "../target/idl/quick_tac_toe";
import * as assert from "assert";
import {
  Connection,
  Keypair,
  LAMPORTS_PER_SOL,
  Transaction,
  sendAndConfirmTransaction,
} from "@solana/web3.js";

const connection = new Connection("http://127.0.0.1:8899", "confirmed");

// const pg = new Program(idl as QuickTacToe, anchor.AnchorProvider(connection))
const wallet = anchor.Wallet.local();
const pg = anchor.workspace.quickTacToe as Program<QuickTacToe>;

import {getAssociatedTokenAddressSync} from "@solana/spl-token";
import{MPL_TOKEN_METADATA_PROGRAM_ID} from "@metaplex-foundation/mpl-token-metadata";
import { web3 } from "@coral-xyz/anchor";

type Square = { row: number; column: number };
type Status = {active: {}} |{won:{}} | {tie:{}}|{notStarted:{}};
type Board = ({x:{}}| {o:{}}| null )[][];
interface PlayArgs {
  square: Square;
  player: web3.Keypair;
  playerRecord: web3.PublicKey;
  otherPlayerRecord: web3.PublicKey;
  game: web3.PublicKey;
  expectedTurn:number,
  expectedState: Status,
  expectedBoard: Board,
  winner?: web3.PublicKey,

}

// 数字创建缓冲区
function numberBuffer(value: bigint): Uint8Array {
  const bytes = new Uint8Array(8);
  for (let i = 0; i < 8; i++) {
    bytes[i] = Number(value & BigInt(0xff));
    value = value >> BigInt(8);
  }
  return bytes;
}
// 游戏中调用它来移动方块
async function play({
  square,
  player,
  playerRecord,
  otherPlayerRecord,
  game,
  expectedTurn,
  expectedState,
  expectedBoard,
  winner,
}: PlayArgs): Promise<void> {
  try {
    const tx = await pg.methods
      .play(square)
      .accounts({
        player: player.publicKey,
        playerRecord,
        otherPlayerRecord,
        game,
      }).preInstructions([
        web3.ComputeBudgetProgram.setComputeUnitLimit({ units: 400_000 }),
      ])
      .signers([player])
      .transaction();
    const txHash = await web3.sendAndConfirmTransaction(anchor.getProvider().connection, tx, [player]);

    const gameData = await pg.account.game.fetch(game);
    assert.strictEqual(
      gameData.turn,
      expectedTurn,
      `Turn should be ${expectedTurn}`
    );

    assert.deepEqual(gameData.state, expectedState, "State does not match");
    assert.deepEqual(gameData.board, expectedBoard, "Board does not match");
    if (winner) {
      assert.strictEqual(
        gameData.winner.toBase58(),
        player.publicKey.toBase58(),
        "Expect Player O to be in Player O position"
      );
    }
  } catch (err) {
    console.log(err);
  }
}
const computeBudgetIxs = [
  web3.ComputeBudgetProgram.setComputeUnitLimit({ units: 1_400_000 }), // 最高设置可达 1,400,000（视集群支持而定）
  web3.ComputeBudgetProgram.setComputeUnitPrice({ microLamports: 1 })   // 提升优先级，可选
];
describe("Quick-Tac-Toe", () => {
  // 定义铸币和程序状态 PDA
  const [mint] = web3.PublicKey.findProgramAddressSync(
    [Buffer.from("play_token_mint")],
    pg.programId
  );
  const [programState] = web3.PublicKey.findProgramAddressSync(
    [Buffer.from("program_state")],
    pg.programId
  );

  // Define Player, Keypairs, PDAs, and ATAs
  const playerXKp = new web3.Keypair();
  const playerOKp = new web3.Keypair();

  const [playerXPda] = web3.PublicKey.findProgramAddressSync(
    [Buffer.from("player"), playerXKp.publicKey.toBuffer()],
    pg.programId
  );
  const [playerOPda] = web3.PublicKey.findProgramAddressSync(
    [Buffer.from("player"), playerOKp.publicKey.toBuffer()],
    pg.programId
  );

  const playerXAta = getAssociatedTokenAddressSync(mint, playerXKp.publicKey);
  const playerOAta = getAssociatedTokenAddressSync(mint, playerOKp.publicKey);

  const GAME_ID = 1;

  const [game] = web3.PublicKey.findProgramAddressSync(
    [Buffer.from("new_game"), numberBuffer(BigInt(GAME_ID))],
    pg.programId
  );

  before(async () => {
    // Request and confirm airdrops
    // const [drop1, drop2] = await Promise.all([
    //   pg.connection.requestAirdrop(playerXKp.publicKey, web3.LAMPORTS_PER_SOL),
    //   pg.connection.requestAirdrop(playerOKp.publicKey, web3.LAMPORTS_PER_SOL),
    // ]);
  });

  it("1. Initialize mint", async () => {
    const tx = await pg.methods
      .init()
      .accounts({
        mint,
        programState,
        payer: wallet.publicKey,
      })
      //  增加多个 compute budget 设置
      .preInstructions(computeBudgetIxs)
      .signers([])
      .transaction();

    const txHash = await web3.sendAndConfirmTransaction(connection, tx, [wallet.payer], {skipPreflight: true});
    console.log(txHash);
  });

  it("2. Create players", async () => {
    // Add code here
  });

  it("3. Create game", async () => {
    // Add code here
  });

  it("4. Cannot join own game", async () => {
    // Add code here
  });

  it("5. Player O joins game", async () => {
    // Add code here
  });

  it("6. Player X wins game", async () => {
    // Add code here
  });

  it("7. Claims reward", async () => {
    // Add code here
  });
});