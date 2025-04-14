// 如何创建 Mint 帐户

import {
    airdropFactory,
    appendTransactionMessageInstructions,
    createSolanaRpc,
    createSolanaRpcSubscriptions,
    createTransactionMessage,
    generateKeyPairSigner,
    getSignatureFromTransaction,
    lamports,
    
    pipe,
    sendAndConfirmTransactionFactory,
    setTransactionMessageFeePayerSigner,
    setTransactionMessageLifetimeUsingBlockhash,
    signTransactionMessageWithSigners,
  } from "@solana/kit";
  import { getCreateAccountInstruction } from "@solana-program/system";
  import {
    getInitializeMintInstruction,
    getMintSize,
    TOKEN_2022_PROGRAM_ADDRESS,
  } from "@solana-program/token-2022";

const rpc = createSolanaRpc("http://api.devnet.solana.com");
const rpcSubscriptions = createSolanaRpcSubscriptions("ws://api.devnet.solana.com");

