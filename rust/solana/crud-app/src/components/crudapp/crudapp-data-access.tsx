'use client'

import { getCrudappProgram, getCrudappProgramId } from '@project/anchor'
import { useConnection } from '@solana/wallet-adapter-react'
import { Cluster, Keypair, PublicKey } from '@solana/web3.js'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'
import toast from 'react-hot-toast'
import { useCluster } from '../cluster/cluster-data-access'
import { useAnchorProvider } from '../solana/solana-provider'
import { useTransactionToast } from '../ui/ui-layout'

interface CreateEntryArgs {
  title: string | undefined
  message: string
  owner: PublicKey
}

export function useCrudappProgram() {
  const { connection } = useConnection()
  const { cluster } = useCluster()
  const transactionToast = useTransactionToast()
  const provider = useAnchorProvider()
  const programId = useMemo(() => getCrudappProgramId(cluster.network as Cluster), [cluster])
  const program = useMemo(() => getCrudappProgram(provider, programId), [provider, programId])

  const accounts = useQuery({
    queryKey: ['crudapp', 'all', { cluster }],
    queryFn: () => program.account.journalEntryState.all(),
  })

  const getProgramAccount = useQuery({
    queryKey: ['get-program-account', { cluster }],
    queryFn: () => connection.getParsedAccountInfo(programId),
  })

  // 创建 
  const createEntry = useMutation<string, Error, CreateEntryArgs>({
    mutationKey: ['journalEntry', 'create', { cluster }],
    mutationFn: async ({ title, message, owner }) => {
      return program.methods
        .createJournalEntry(title, message)
        .rpc();
    },
    onSuccess: (signature) => {
      // 签名交易
      transactionToast(signature)
      // 重新获取所有权
      accounts.refetch()
    },
    onError: (error) => {
      toast.error(`Failed to create entry: ${error.message}`)
    }
  });
  
  return {
    program,
    accounts,    
    getProgramAccount,
    createEntry,
  }
}

export function useCrudappProgramAccount({ account }: { account: PublicKey }) {
  const { cluster } = useCluster()
  const transactionToast = useTransactionToast()
  const { program, accounts } = useCrudappProgram()

  const accountQuery = useQuery({
    queryKey: ['crudapp', 'fetch', { cluster, account }],
    queryFn: () => program.account.journalEntryState.fetch(account),
  })

  //更新 
  const updateEntry = useMutation<string, Error, CreateEntryArgs>({
    mutationKey: ['journalEntry', 'update', { cluster }],
    mutationFn: async ({ title, message }) => {
      return program.methods
        .updateJournalEntry(title, message)
        .rpc();
    },
    onSuccess: (signature) => {
      // 签名交易
      transactionToast(signature)
      // 重新获取所有权
      accounts.refetch()
    },
    onError: (error) => {
      toast.error(`Failed to update entry: ${error.message}`)
    }
  });
  // 删除
  const deleteEntry = useMutation({
    mutationKey: ['journalEntry', 'delete', { cluster }],
    mutationFn: (title:string) => {
      return program.methods
        .deleteJournalEntry(title)
        .rpc();
    },
    onSuccess: (signature) => {
      // 签名交易
      transactionToast(signature)
      // 重新获取所有权
      accounts.refetch()
    },
    onError: (error) => {
      toast.error(`Failed to delete entry: ${error.message}`)
    }
  });
  
    return {
    accountQuery,
    updateEntry,
    deleteEntry,
  }
}
