
require('dotenv').config();
import { Connection, LAMPORTS_PER_SOL, PublicKey,Transaction,
    SystemProgram,
    TransactionInstruction,
    Keypair,
    sendAndConfirmTransaction } from "@solana/web3.js";

const quickNodeEndpoint = process.env.QUICKNODE_ENDPOINT || "";
const connection = new Connection(quickNodeEndpoint);
connection.getVersion().then(version => {
    console.log('Connection to cluster established:', quickNodeEndpoint);
    console.log('Version:', version);
}).catch(error => console.error(error));

//获取余额
const myAddress = 'AEav14XC2m11X5F6iBRrmK7cu8L2GhD9A2QGzGUDfLYD'; // 👈 REPLACE THIS WITH YOUR ADDRESS
const myPublicKey = new PublicKey(myAddress);

console.log(`Address: `, myPublicKey.toBase58());


connection.getAccountInfo(myPublicKey).then((info) => {
    console.log(`Account Info: \n`, info);
});

connection.getBalance(myPublicKey).then((balance) => {
    console.log(`Balance: ${balance / LAMPORTS_PER_SOL} SOL`);
});


async function sendTransaction() {
    // Define Keys    
    const receiver = Keypair.generate();
    console.log(`Receiver Address: ${receiver.publicKey.toBase58()}`);
    // 👇 替换成你自己的
    const secret = [203,12,200,183,35,197,220,201,90,196,104,247,85,35,186,113,84,12,142];
    const sender = Keypair.fromSecretKey(new Uint8Array(secret));

    // Create Instruction
    const ix: TransactionInstruction = SystemProgram.transfer({
        fromPubkey: sender.publicKey,
        toPubkey: receiver.publicKey,
        lamports: LAMPORTS_PER_SOL / 10
    })
    
    // Create and Prepare Transaction
    const transaction = new Transaction().add(ix);
    const { blockhash } = await connection.getLatestBlockhash();
    transaction.feePayer = sender.publicKey;
    transaction.recentBlockhash = blockhash;
    transaction.sign(sender);

    // Send and Confirm Transaction
    const signature = await sendAndConfirmTransaction(connection, transaction, [sender]);
    console.log(`Tx: https://explorer.solana.com/tx/${signature}?cluster=devnet`);
}
sendTransaction().then(() => process.exit());