require('dotenv').config();
import { Connection, Keypair, PublicKey, sendAndConfirmTransaction, SystemProgram, Transaction } from "@solana/web3.js";
import { 
    getOrCreateAssociatedTokenAccount, 
    getMinimumBalanceForRentExemptMint, 
    getAssociatedTokenAddressSync, 
    MINT_SIZE, TOKEN_PROGRAM_ID, 
    createInitializeMintInstruction, 
    createMintToInstruction, 
    createAssociatedTokenAccountIdempotentInstruction, 
    transfer,
    burnChecked 
} from "@solana/spl-token";

const secret = [12,142];
const tokenAuthority = Keypair.fromSecretKey(new Uint8Array(secret));
const receiver = Keypair.generate();



const quickNodeEndpoint = process.env.QUICKNODE_ENDPOINT || "";
const connection = new Connection(quickNodeEndpoint);
connection.getVersion().then(version => {
    console.log('Connection to cluster established:', quickNodeEndpoint);
    console.log('Version:', version);
}).catch(error => console.error(error));

// 创建新令牌
async function createNewToken(authority: Keypair, connection: Connection, numDecimals: number) {
    // Instruction 1 - 为我们的新代币铸造创建一个帐户
    // 创建新帐户所需的最低余额
    // 需要多少 Lamport 来为新帐户充值
    const requiredBalance = await getMinimumBalanceForRentExemptMint(connection);
    // 命令来创建虚荣铸币地址 ID
    const mintKeypair = Keypair.generate();
    // 创建一个新帐户
    const ix1 = SystemProgram.createAccount({
        fromPubkey: authority.publicKey,//为新账户提供资金的账户的公钥
        newAccountPubkey: mintKeypair.publicKey,//新帐户的公钥
        space: MINT_SIZE,//为新帐户分配的内存字节数
        lamports: requiredBalance,//要转移到新账户的 lamports 数量
        programId: TOKEN_PROGRAM_ID,// SPL 代币程序的程序 ID
    });

    // Instruction 2 - 将新帐户初始化为 mint
    const ix2 = createInitializeMintInstruction(
        mintKeypair.publicKey,
        numDecimals,
        authority.publicKey,
        authority.publicKey
    );

    // Create and send transaction
    const createNewTokenTransaction = new Transaction().add(ix1, ix2);
    const initSignature = await sendAndConfirmTransaction(connection, createNewTokenTransaction, [tokenAuthority, mintKeypair]);
    return { initSignature, mint: mintKeypair.publicKey };
}

async function mintTokens(mint: PublicKey, authority: Keypair, connection: Connection, numTokens: number) {
    // 创建一个代币账户
    const tokenATA = getAssociatedTokenAddressSync(mint, authority.publicKey);
    const ix1 = createAssociatedTokenAccountIdempotentInstruction(
        authority.publicKey,//将支付新代币账户的源账户的公钥
        tokenATA,
        authority.publicKey,
        mint
    );

    // Instruction 2 - 将新代币铸造到目标钱包
    const ix2 = createMintToInstruction(
        mint,
        tokenATA,
        authority.publicKey,//将支付新代币账户的源账户的公钥
        numTokens //要铸造的代币数量
    );

    // Create and send transaction
    const mintTokensTransaction = new Transaction().add(ix1, ix2);
    const mintSignature = await sendAndConfirmTransaction(connection, mintTokensTransaction, [tokenAuthority], { skipPreflight: true });
    return { mintSignature };
}

async function transferTokens(mint: PublicKey, authority: Keypair, destination: PublicKey, connection: Connection, numTokens: number) {
    // 使用单个命令来获取账户地址（并在必要时创建）
    const destinationAta = await getOrCreateAssociatedTokenAccount(connection, authority, mint, destination, undefined, undefined, { skipPreflight: true });
    console.log(`Destination ATA: ${destinationAta.address.toBase58()}`);
    // 使用单个命令来获取账户地址（并在必要时创建）
    const sourceAta = await getOrCreateAssociatedTokenAccount(connection, authority, mint, authority.publicKey, undefined, undefined, { skipPreflight: true });
    console.log(`Source ATA: ${sourceAta.address.toBase58()}`);
    const transferSignature = await transfer(connection, authority, sourceAta.address, destinationAta.address, authority, numTokens)
    return { transferSignature };
}

async function burnTokens(mint: PublicKey, authority: Keypair, connection: Connection, numberTokens: number, decimals: number) {
    const ata = await getOrCreateAssociatedTokenAccount(connection, authority, mint, authority.publicKey, undefined, undefined, { skipPreflight: true });
    const burnSignature = await burnChecked(
        connection,
        authority,
        ata.address,
        mint,
        authority.publicKey,
        numberTokens,
        decimals,
        undefined,
        { skipPreflight: true }
    );
    return { burnSignature };
}
async function main() {
    const { initSignature, mint } = await createNewToken(tokenAuthority, connection, 0);
    console.log(`Init Token Tx: https://explorer.solana.com/tx/${initSignature}?cluster=devnet`);
    console.log(`Mint ID: ${mint.toBase58()}`);
    const { mintSignature } = await mintTokens(mint, tokenAuthority, connection, 100);
    console.log(`Mint Tokens Tx: https://explorer.solana.com/tx/${mintSignature}?cluster=devnet`);
    const { transferSignature } = await transferTokens(mint, tokenAuthority, receiver.publicKey, connection, 1);
    console.log(`Transfer Tokens Tx: https://explorer.solana.com/tx/${transferSignature}?cluster=devnet`);
    const { burnSignature } = await burnTokens(mint, tokenAuthority, connection, 1, 0);
    console.log(`Burn Tokens Tx: https://explorer.solana.com/tx/${burnSignature}?cluster=devnet`);
}

main()
    .then(() => process.exit())
    .catch((err) => {
        console.error(err);
        process.exit(-1);
    });