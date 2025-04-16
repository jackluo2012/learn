'use client'

import { getTokenlotteryProgram, getTokenlotteryProgramId } from '@project/anchor'
import { useConnection } from '@solana/wallet-adapter-react'
import { Cluster, Keypair, PublicKey } from '@solana/web3.js'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'
import toast from 'react-hot-toast'
import { useCluster } from '../cluster/cluster-data-access'
import { useAnchorProvider } from '../solana/solana-provider'
import { useTransactionToast } from '../ui/ui-layout'

export function useTokenlotteryProgram() {
  const { connection } = useConnection()
  const { cluster } = useCluster()
  const transactionToast = useTransactionToast()
  const provider = useAnchorProvider()
  const programId = useMemo(() => getTokenlotteryProgramId(cluster.network as Cluster), [cluster])
  const program = useMemo(() => getTokenlotteryProgram(provider, programId), [provider, programId])

  const accounts = useQuery({
    queryKey: ['tokenlottery', 'all', { cluster }],
    queryFn: () => program.account.tokenlottery.all(),
  })

  const getProgramAccount = useQuery({
    queryKey: ['get-program-account', { cluster }],
    queryFn: () => connection.getParsedAccountInfo(programId),
  })

  const initialize = useMutation({
    mutationKey: ['tokenlottery', 'initialize', { cluster }],
    mutationFn: (keypair: Keypair) =>
      program.methods.initialize().accounts({ tokenlottery: keypair.publicKey }).signers([keypair]).rpc(),
    onSuccess: (signature) => {
      transactionToast(signature)
      return accounts.refetch()
    },
    onError: () => toast.error('Failed to initialize account'),
  })

  return {
    program,
    programId,
    accounts,
    getProgramAccount,
    initialize,
  }
}

export function useTokenlotteryProgramAccount({ account }: { account: PublicKey }) {
  const { cluster } = useCluster()
  const transactionToast = useTransactionToast()
  const { program, accounts } = useTokenlotteryProgram()

  const accountQuery = useQuery({
    queryKey: ['tokenlottery', 'fetch', { cluster, account }],
    queryFn: () => program.account.tokenlottery.fetch(account),
  })

  const closeMutation = useMutation({
    mutationKey: ['tokenlottery', 'close', { cluster, account }],
    mutationFn: () => program.methods.close().accounts({ tokenlottery: account }).rpc(),
    onSuccess: (tx) => {
      transactionToast(tx)
      return accounts.refetch()
    },
  })

  const decrementMutation = useMutation({
    mutationKey: ['tokenlottery', 'decrement', { cluster, account }],
    mutationFn: () => program.methods.decrement().accounts({ tokenlottery: account }).rpc(),
    onSuccess: (tx) => {
      transactionToast(tx)
      return accountQuery.refetch()
    },
  })

  const incrementMutation = useMutation({
    mutationKey: ['tokenlottery', 'increment', { cluster, account }],
    mutationFn: () => program.methods.increment().accounts({ tokenlottery: account }).rpc(),
    onSuccess: (tx) => {
      transactionToast(tx)
      return accountQuery.refetch()
    },
  })

  const setMutation = useMutation({
    mutationKey: ['tokenlottery', 'set', { cluster, account }],
    mutationFn: (value: number) => program.methods.set(value).accounts({ tokenlottery: account }).rpc(),
    onSuccess: (tx) => {
      transactionToast(tx)
      return accountQuery.refetch()
    },
  })

  return {
    accountQuery,
    closeMutation,
    decrementMutation,
    incrementMutation,
    setMutation,
  }
}
