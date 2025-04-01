import { BN, Program } from "@coral-xyz/anchor";
import { ActionGetResponse, ACTIONS_CORS_HEADERS, createPostResponse } from "@solana/actions"
import { Connection, PublicKey, Transaction } from "@solana/web3.js";
import { Voting } from "anchor/target/types/voting";
const IDL = require("@/../anchor/target/idl/voting.json");

export const OPTIONS = GET;
export async function GET(request: Request) {
  const actionMetadata :ActionGetResponse = {
    icon: "https://rust-boom.github.io/rust-boom/photo/flux-rust5.jpg",
    title: "投出你最喜欢的候选人",
    description: "Vote on a poll333",
    label: "Vote4",
    links: {
      actions: [
        {
          label: "投票给jackluo",
          href: "/api/vote?candidate=jackluo"
        },
        {
          label: "投票给TOM",
          href: "/api/vote?candidate=tome"
        },
      ],
    },
  }
  return Response.json(actionMetadata,{headers:ACTIONS_CORS_HEADERS})
}

export async function POST(request: Request) {
  
  const url = new URL(request.url)
  const candidate = url.searchParams.get("candidate")
  if (candidate !="jackluo" && candidate != "tome") {
    return new Response("Invalid candidate", { status: 400,headers:ACTIONS_CORS_HEADERS })
  }
  // 连接本地solana节点
  const connection = new Connection("http://127.0.0.1:8899","confirmed");
  const program = new Program<Voting>(IDL, { connection });
  
  // 获取请求的post 数据
  const body = await request.json();
  // 获取请求的公钥
  let voter;
  try {    
    voter = new PublicKey(body.account);
  } catch (error) {
    return new Response("无效的帐号"+ error, { status: 400,headers:ACTIONS_CORS_HEADERS })
  }
  // 创建 指令
  const instruction = await program.methods
        .vote(new BN(1), candidate)
        .accounts({signer: voter})
        .instruction();
  // 获取最后一个区块哈希
  const  blockhash  = await connection.getLatestBlockhash();
  // 创建交易
  const transaction = new Transaction({
    feePayer: voter, // 设置支付者
    blockhash: blockhash.blockhash, // 设置区块哈希
    lastValidBlockHeight:blockhash.lastValidBlockHeight, // 设置最后一个区块高度
  }).add(instruction);
  
  const response = await createPostResponse({
    fields: {
      type: "transaction",
      transaction
    }
  });
  return Response.json(response);
}