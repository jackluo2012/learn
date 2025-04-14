import * as anchor from '@coral-xyz/anchor'
import { Program } from '@coral-xyz/anchor'
import { Keypair } from '@solana/web3.js'
import { Tokenvesting } from '../target/types/tokenvesting'

describe('tokenvesting', () => {
  // Configure the client to use the local cluster.
  const provider = anchor.AnchorProvider.env()
  anchor.setProvider(provider)
  const payer = provider.wallet as anchor.Wallet

  const program = anchor.workspace.Tokenvesting as Program<Tokenvesting>

  const tokenvestingKeypair = Keypair.generate()

  it('Initialize Tokenvesting', async () => {
    await program.methods
      .initialize()
      .accounts({
        tokenvesting: tokenvestingKeypair.publicKey,
        payer: payer.publicKey,
      })
      .signers([tokenvestingKeypair])
      .rpc()

    const currentCount = await program.account.tokenvesting.fetch(tokenvestingKeypair.publicKey)

    expect(currentCount.count).toEqual(0)
  })

  it('Increment Tokenvesting', async () => {
    await program.methods.increment().accounts({ tokenvesting: tokenvestingKeypair.publicKey }).rpc()

    const currentCount = await program.account.tokenvesting.fetch(tokenvestingKeypair.publicKey)

    expect(currentCount.count).toEqual(1)
  })

  it('Increment Tokenvesting Again', async () => {
    await program.methods.increment().accounts({ tokenvesting: tokenvestingKeypair.publicKey }).rpc()

    const currentCount = await program.account.tokenvesting.fetch(tokenvestingKeypair.publicKey)

    expect(currentCount.count).toEqual(2)
  })

  it('Decrement Tokenvesting', async () => {
    await program.methods.decrement().accounts({ tokenvesting: tokenvestingKeypair.publicKey }).rpc()

    const currentCount = await program.account.tokenvesting.fetch(tokenvestingKeypair.publicKey)

    expect(currentCount.count).toEqual(1)
  })

  it('Set tokenvesting value', async () => {
    await program.methods.set(42).accounts({ tokenvesting: tokenvestingKeypair.publicKey }).rpc()

    const currentCount = await program.account.tokenvesting.fetch(tokenvestingKeypair.publicKey)

    expect(currentCount.count).toEqual(42)
  })

  it('Set close the tokenvesting account', async () => {
    await program.methods
      .close()
      .accounts({
        payer: payer.publicKey,
        tokenvesting: tokenvestingKeypair.publicKey,
      })
      .rpc()

    // The account should no longer exist, returning null.
    const userAccount = await program.account.tokenvesting.fetchNullable(tokenvestingKeypair.publicKey)
    expect(userAccount).toBeNull()
  })
})
