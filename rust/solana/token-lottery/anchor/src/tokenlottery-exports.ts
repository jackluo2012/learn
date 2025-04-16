// Here we export some useful types and functions for interacting with the Anchor program.
import { AnchorProvider, Program } from '@coral-xyz/anchor'
import { Cluster, PublicKey } from '@solana/web3.js'
import TokenlotteryIDL from '../target/idl/tokenlottery.json'
import type { Tokenlottery } from '../target/types/tokenlottery'

// Re-export the generated IDL and type
export { Tokenlottery, TokenlotteryIDL }

// The programId is imported from the program IDL.
export const TOKENLOTTERY_PROGRAM_ID = new PublicKey(TokenlotteryIDL.address)

// This is a helper function to get the Tokenlottery Anchor program.
export function getTokenlotteryProgram(provider: AnchorProvider, address?: PublicKey) {
  return new Program({ ...TokenlotteryIDL, address: address ? address.toBase58() : TokenlotteryIDL.address } as Tokenlottery, provider)
}

// This is a helper function to get the program ID for the Tokenlottery program depending on the cluster.
export function getTokenlotteryProgramId(cluster: Cluster) {
  switch (cluster) {
    case 'devnet':
    case 'testnet':
      // This is the program ID for the Tokenlottery program on devnet and testnet.
      return new PublicKey('coUnmi3oBUtwtd9fjeAvSsJssXh5A5xyPbhpewyzRVF')
    case 'mainnet-beta':
    default:
      return TOKENLOTTERY_PROGRAM_ID
  }
}
