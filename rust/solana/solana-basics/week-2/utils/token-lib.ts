
import { Connection, Keypair, PublicKey, SystemProgram, TransactionInstruction } from "@solana/web3.js";
import {
    getMinimumBalanceForRentExemptMint,
    getAssociatedTokenAddressSync,
    MINT_SIZE, TOKEN_PROGRAM_ID,
    createInitializeMintInstruction,
    createMintToInstruction,
    createAssociatedTokenAccountIdempotentInstruction,
} from "@solana/spl-token";
// 输入金额和小数位数，并以小数形式返回金额。例如，如果金额为 1，
// 小数位为两位，则函数返回 100。如果金额为 1，小数位为三位，则函数返回 1,000
const amountToDecimalAmount = (amount: number, decimals: number) => {
    return amount * (10 ** decimals);
}

interface createNewTokenParams {
    authority: PublicKey,
    connection: Connection,
    numDecimals?: number,
    numTokens?: number
}

interface createNewTokenReturn {
    instructions: TransactionInstruction[],
    signers: Keypair[]
}


export async function createNewToken({
    authority,
    connection,
    numDecimals = 0,
    numTokens = 0
}: createNewTokenParams): Promise<createNewTokenReturn> {
    const instructions: TransactionInstruction[] = [];
    // Instruction 1 - 创建一个新的帐号
    const requiredBalance = await getMinimumBalanceForRentExemptMint(connection);
    const mintKeypair = Keypair.generate();
    const ix1 = SystemProgram.createAccount({
        fromPubkey: authority,
        newAccountPubkey: mintKeypair.publicKey,
        space: MINT_SIZE,
        lamports: requiredBalance,
        programId: TOKEN_PROGRAM_ID,
    });

    // Instruction 2 - 初始化mint帐号
    const ix2 = createInitializeMintInstruction(
        mintKeypair.publicKey,
        numDecimals,
        authority,
        authority
    );
    instructions.push(ix1, ix2)

    // 我们检查是否需要铸造代币。如果不需要，我们将返回指令和签名者（记住，我们需要使用铸造者的密钥对对交易进行签名，以将其初始化为新账户）
    if (numTokens === 0) return { instructions, signers: [mintKeypair] };

    // Instruction 3 - 为铸币创建一个关联的代币账户
    const tokenATA = getAssociatedTokenAddressSync(mintKeypair.publicKey, authority);
    const ix3 = createAssociatedTokenAccountIdempotentInstruction(
        authority,
        tokenATA,
        authority,
        mintKeypair.publicKey
    );

    // Instruction 4 - 向新账户铸造代币
    const ix4 = createMintToInstruction(
        mintKeypair.publicKey,
        tokenATA,
        authority,
        amountToDecimalAmount(numTokens, numDecimals)
    );
    instructions.push(ix3, ix4)

    return { instructions: instructions, signers: [mintKeypair] };
}