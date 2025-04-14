import { LiteSVM, TransactionMetadata } from "litesvm";
import {
  Keypair,
  LAMPORTS_PER_SOL,
  PublicKey,
  Transaction,
  SystemProgram,
} from "@solana/web3.js";
import { 
  TOKEN_PROGRAM_ID,
  ASSOCIATED_TOKEN_PROGRAM_ID,
  createMint,
  getAssociatedTokenAddress,
  mintTo,
} from "@solana/spl-token";
import idlJson from "../../target/idl/tokenvesting.json";
import { AnchorProvider, Program } from "@coral-xyz/anchor";
import { BN } from "bn.js";

const IDL = idlJson as any;

describe("Token Vesting Tests", () => {
  // 初始化基础变量
  const programId = new PublicKey(IDL.address);
  const provider = AnchorProvider.local();
  const program = new Program(IDL, programId, provider);

  // 测试相关变量
  let svm: LiteSVM;
  let admin: Keypair;          // 管理员账户
  let mint: PublicKey;         // 代币铸造账户
  let companyName = "TestCompany";
  
  beforeEach(async () => {
    // 为每个测试初始化环境
    svm = new LiteSVM();
    svm.addProgramFromFile(programId, "./vesting.so");
    
    // 创建管理员账户并空投 SOL
    admin = new Keypair();
    svm.airdrop(admin.publicKey, BigInt(10 * LAMPORTS_PER_SOL));
    
    // 创建代币铸造账户
    mint = await createMint(
      svm,
      admin,
      admin.publicKey,
      null,
      9
    );
  });

  it("应该成功创建归属账户", async () => {
    // 获取归属账户 PDA
    const [vestingAccount] = PublicKey.findProgramAddressSync(
      [Buffer.from(companyName)],
      programId
    );

    // 获取国库代币账户 PDA
    const [treasuryAccount] = PublicKey.findProgramAddressSync(
      [Buffer.from("treasury"), Buffer.from(companyName)],
      programId
    );

    try {
      // 创建归属账户交易
      const tx: Transaction = await program.methods
        .createVestingAccount(companyName)
        .accounts({
          signer: admin.publicKey,
          vestingAccount,
          mint,
          treasuryTokenAccount: treasuryAccount,
          tokenProgram: TOKEN_PROGRAM_ID,
          systemProgram: SystemProgram.programId,
        })
        .transaction();

      // 执行交易
      svm.sendTransaction(tx, [admin]);

      // 验证账户创建成功
      const account = await program.account("VestingAccount").fetch(vestingAccount);
      expect(account.owner).toEqual(admin.publicKey);
      expect(account.mint).toEqual(mint);
      expect(account.compayName).toEqual(companyName);
    } catch (error) {
      console.error("创建归属账户失败:", error);
      throw error;
    }
  });

  it("应该成功创建员工账户", async () => {
    // 创建员工账户
    const employee = new Keypair();
    svm.airdrop(employee.publicKey, BigInt(LAMPORTS_PER_SOL));

    // 获取归属账户 PDA
    const [vestingAccount] = PublicKey.findProgramAddressSync(
      [Buffer.from(companyName)],
      programId
    );

    // 获取员工账户 PDA
    const [employeeAccount] = PublicKey.findProgramAddressSync(
      [
        Buffer.from("employee_vesting"),
        employee.publicKey.toBuffer(),
        vestingAccount.toBuffer()
      ],
      programId
    );

    // 设置归属计划参数
    const now = Math.floor(Date.now() / 1000);
    const startTime = now;
    const cliffTime = now + 30 * 24 * 60 * 60; // 30天后
    const endTime = now + 365 * 24 * 60 * 60;  // 1年后
    const totalAmount = new BN(1000000000);     // 1000 tokens

    try {
      // 创建员工账户交易
      const tx = await program.methods
        .createEmployeeAccount(
          new BN(startTime),
          new BN(endTime),
          totalAmount,
          new BN(cliffTime)
        )
        .accounts({
          owner: admin.publicKey,
          beneficiary: employee.publicKey,
          vestingAccount,
          employeeAccount,
          systemProgram: SystemProgram.programId,
        })
        .transaction();

      // 执行交易
      svm.sendTransaction(tx, [admin]);

      // 验证员工账户创建成功
      const account = await program.account.employeeAccount.fetch(employeeAccount);
      expect(account.beneficiary).toEqual(employee.publicKey);
      expect(account.vestingAccount).toEqual(vestingAccount);
      expect(account.totalAmount.toString()).toEqual(totalAmount.toString());
    } catch (error) {
      console.error("创建员工账户失败:", error);
      throw error;
    }
  });

  it("应该成功提取代币", async () => {
    // 创建员工账户相关变量
    const employee = new Keypair();
    const now = Math.floor(Date.now() / 1000);
    const startTime = now - 180 * 24 * 60 * 60; // 6个月前
    const cliffTime = startTime + 30 * 24 * 60 * 60; // 开始后30天
    const endTime = startTime + 365 * 24 * 60 * 60; // 开始后1年
    const totalAmount = new BN(1000000000);

    // 获取各种 PDA 地址
    const [vestingAccount] = PublicKey.findProgramAddressSync(
      [Buffer.from(companyName)],
      programId
    );
    
    const [treasuryAccount] = PublicKey.findProgramAddressSync(
      [Buffer.from("treasury"), Buffer.from(companyName)],
      programId
    );

    const employeeTokenAccount = await getAssociatedTokenAddress(
      mint,
      employee.publicKey
    );

    try {
      // 先创建归属账户
      await program.methods
        .createVestingAccount(companyName)
        .accounts({
          signer: admin.publicKey,
          vestingAccount,
          mint,
          treasuryTokenAccount: treasuryAccount,
          tokenProgram: TOKEN_PROGRAM_ID,
          systemProgram: SystemProgram.programId,
        })
        .rpc();

      // 创建员工账户
      await program.methods
        .createEmployeeAccount(
          new BN(startTime),
          new BN(endTime),
          totalAmount,
          new BN(cliffTime)
        )
        .accounts({
          owner: admin.publicKey,
          beneficiary: employee.publicKey,
          vestingAccount,
          employeeAccount,
          systemProgram: SystemProgram.programId,
        })
        .rpc();

      // 铸造代币到国库账户
      await mintTo(
        svm,
        admin,
        mint,
        treasuryAccount,
        admin,
        totalAmount.toNumber()
      );

      // 执行提取代币交易
      const tx = await program.methods
        .claimTokens(companyName)
        .accounts({
          beneficiary: employee.publicKey,
          employeeAccount,
          vestingAccount,
          mint,
          treasuryTokenAccount: treasuryAccount,
          employeeTokenAccount,
          tokenProgram: TOKEN_PROGRAM_ID,
          associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
          systemProgram: SystemProgram.programId,
        })
        .transaction();

      // 执行交易
      svm.sendTransaction(tx, [employee]);

      // 验证提取结果
      const employeeAccount = await program.account.employeeAccount.fetch(employeeAccount);
      expect(employeeAccount.totalWithdraw.toNumber()).toBeGreaterThan(0);
    } catch (error) {
      console.error("提取代币失败:", error);
      throw error;
    }
  });

  it("应该在悬崖期内无法提取代币", async () => {
    // 创建员工账户
    const employee = new Keypair();
    svm.airdrop(employee.publicKey, BigInt(LAMPORTS_PER_SOL));

    // 设置时间参数
    const now = Math.floor(Date.now() / 1000);
    const startTime = now - 15 * 24 * 60 * 60; // 15天前
    const cliffTime = now + 15 * 24 * 60 * 60; // 还有15天到悬崖期
    const endTime = now + 365 * 24 * 60 * 60;  // 1年后
    const totalAmount = new BN(1000000000);     // 1000 tokens

    // 获取必要的 PDA 地址
    const [vestingAccount] = PublicKey.findProgramAddressSync(
      [Buffer.from(companyName)],
      programId
    );

    const [employeeAccount] = PublicKey.findProgramAddressSync(
      [
        Buffer.from("employee_vesting"),
        employee.publicKey.toBuffer(),
        vestingAccount.toBuffer()
      ],
      programId
    );

    const [treasuryAccount] = PublicKey.findProgramAddressSync(
      [Buffer.from("treasury"), Buffer.from(companyName)],
      programId
    );

    const employeeTokenAccount = await getAssociatedTokenAddress(
      mint,
      employee.publicKey
    );

    try {
      // 先创建归属账户
      await program.methods
        .createVestingAccount(companyName)
        .accounts({
          signer: admin.publicKey,
          vestingAccount,
          mint,
          treasuryTokenAccount: treasuryAccount,
          tokenProgram: TOKEN_PROGRAM_ID,
          systemProgram: SystemProgram.programId,
        })
        .rpc();

      // 创建员工账户
      await program.methods
        .createEmployeeAccount(
          new BN(startTime),
          new BN(endTime),
          totalAmount,
          new BN(cliffTime)
        )
        .accounts({
          owner: admin.publicKey,
          beneficiary: employee.publicKey,
          vestingAccount,
          employeeAccount,
          systemProgram: SystemProgram.programId,
        })
        .rpc();

      // 铸造代币到国库账户
      await mintTo(
        svm,
        admin,
        mint,
        treasuryAccount,
        admin,
        totalAmount.toNumber()
      );

      // 尝试提取代币交易
      const tx = await program.methods
        .claimTokens(companyName)
        .accounts({
          beneficiary: employee.publicKey,
          employeeAccount,
          vestingAccount,
          mint,
          treasuryTokenAccount: treasuryAccount,
          employeeTokenAccount,
          tokenProgram: TOKEN_PROGRAM_ID,
          associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
          systemProgram: SystemProgram.programId,
        })
        .transaction();

      // 执行交易并期望失败
      await expect(
        svm.sendTransaction(tx, [employee])
      ).rejects.toThrow(/CliffTimeNotReached/);

    } catch (error) {
      // 确保错误是悬崖期未到
      if (!error.message.includes("CliffTimeNotReached")) {
        throw error;
      }
    }
  });

  // 添加新的测试用例：测试超出结束时间的情况
  it("应该在超出结束时间时无法提取代币", async () => {
    // 创建员工账户
    const employee = new Keypair();
    svm.airdrop(employee.publicKey, BigInt(LAMPORTS_PER_SOL));

    // 设置时间参数（结束时间在过去）
    const now = Math.floor(Date.now() / 1000);
    const startTime = now - 400 * 24 * 60 * 60; // 400天前
    const cliffTime = startTime + 30 * 24 * 60 * 60; // 开始后30天
    const endTime = now - 30 * 24 * 60 * 60;  // 30天前结束
    const totalAmount = new BN(1000000000);

    // 获取必要的 PDA 地址
    const [vestingAccount] = PublicKey.findProgramAddressSync(
      [Buffer.from(companyName)],
      programId
    );

    const [employeeAccount] = PublicKey.findProgramAddressSync(
      [
        Buffer.from("employee_vesting"),
        employee.publicKey.toBuffer(),
        vestingAccount.toBuffer()
      ],
      programId
    );

    const [treasuryAccount] = PublicKey.findProgramAddressSync(
      [Buffer.from("treasury"), Buffer.from(companyName)],
      programId
    );

    const employeeTokenAccount = await getAssociatedTokenAddress(
      mint,
      employee.publicKey
    );

    try {
      // 先创建归属账户
      await program.methods
        .createVestingAccount(companyName)
        .accounts({
          signer: admin.publicKey,
          vestingAccount,
          mint,
          treasuryTokenAccount: treasuryAccount,
          tokenProgram: TOKEN_PROGRAM_ID,
          systemProgram: SystemProgram.programId,
        })
        .rpc();

      // 创建员工账户
      await program.methods
        .createEmployeeAccount(
          new BN(startTime),
          new BN(endTime),
          totalAmount,
          new BN(cliffTime)
        )
        .accounts({
          owner: admin.publicKey,
          beneficiary: employee.publicKey,
          vestingAccount,
          employeeAccount,
          systemProgram: SystemProgram.programId,
        })
        .rpc();

      // 铸造代币到国库账户
      await mintTo(
        svm,
        admin,
        mint,
        treasuryAccount,
        admin,
        totalAmount.toNumber()
      );

      // 尝试提取代币交易
      const tx = await program.methods
        .claimTokens(companyName)
        .accounts({
          beneficiary: employee.publicKey,
          employeeAccount,
          vestingAccount,
          mint,
          treasuryTokenAccount: treasuryAccount,
          employeeTokenAccount,
          tokenProgram: TOKEN_PROGRAM_ID,
          associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
          systemProgram: SystemProgram.programId,
        })
        .transaction();

      // 执行交易并期望失败
      await expect(
        svm.sendTransaction(tx, [employee])
      ).rejects.toThrow(/EndTimeReached/);

    } catch (error) {
      // 确保错误是结束时间已到
      if (!error.message.includes("EndTimeReached")) {
        throw error;
      }
    }
  });
});