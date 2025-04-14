import { Rpc, RpcSubscriptions, SolanaRpcApi, SolanaRpcSubscriptionsApi } from "@solana/kit";
import { createSolanaRpc, createSolanaRpcSubscriptions } from "@solana/kit"; 
export type Client = {
  rpc: Rpc<SolanaRpcApi>;
  rpcSubscriptions: RpcSubscriptions<SolanaRpcSubscriptionsApi>;
};

//创建一个帮助程序函数来创建一个可以在整个应用程序中使用的新缓存 Client 对象：
let client: Client | undefined;
export function createClient(): Client {
  if (!client) {
    client = {
      rpc: createSolanaRpc("http://127.0.0.1:8899"),
      rpcSubscriptions: createSolanaRpcSubscriptions("ws://127.0.0.1:8900"),
    };
  }
  return client;
}