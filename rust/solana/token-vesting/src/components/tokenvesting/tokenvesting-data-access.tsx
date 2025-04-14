'use client'

import { getTokenvestingProgram, getTokenvestingProgramId } from '@project/anchor'
import { useConnection } from '@solana/wallet-adapter-react'
import { Cluster, PublicKey } from '@solana/web3.js'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'
import toast from 'react-hot-toast'
import { useCluster } from '../cluster/cluster-data-access'
import { useAnchorProvider } from '../solana/solana-provider'
import { useTransactionToast } from '../ui/ui-layout'
import { TOKEN_PROGRAM_ID } from '@solana/spl-token'
import { create } from 'domain'

interface CreateVestingArgs {
  companyName: string,
  mint: string, //谁创建的mint token
}

interface CreateEmployeeArgs {
  startTime: number,
  endTime: number,
  totalAmount: number,
  cliffTime: number,
  beneficiary: string,
  // vestingAccount: string,
}

export function useTokenvestingProgram() {
  const { connection } = useConnection()
  const { cluster } = useCluster()
  const transactionToast = useTransactionToast()
  const provider = useAnchorProvider()
  const programId = useMemo(() => getTokenvestingProgramId(cluster.network as Cluster), [cluster])
  const program = useMemo(() => getTokenvestingProgram(provider, programId), [provider, programId])

  const accounts = useQuery({
    queryKey: ['tokenvesting', 'all', { cluster }],
    queryFn: () => program.account.vestingAccount.all(),
  })

  const getProgramAccount = useQuery({
    queryKey: ['get-program-account', { cluster }],
    queryFn: () => connection.getParsedAccountInfo(programId),
  })

  const createTokenvesting = useMutation<string, unknown, CreateVestingArgs>({
    mutationKey: ['vestingAccount', 'create', { cluster }],
    mutationFn: async ({companyName, mint}) => {
      const tx = await program.methods
        .createVestiongAccount(companyName)        
        .accounts({
          mint: new PublicKey(mint),
          tokenProgram: TOKEN_PROGRAM_ID,
        })        
        .rpc()
      return tx
    },
    onSuccess: (tx) => {
      transactionToast(tx)
      return accounts.refetch()
    },
    onError: (error) => {
      toast.error(`创建失败: ${error}`)
    }
  })

  return {
    program,
    programId,
    accounts,
    getProgramAccount,
    createTokenvesting,
  }
}

export function useTokenvestingProgramAccount({ account }: { account: PublicKey }) {
  const { cluster } = useCluster()
  const transactionToast = useTransactionToast()
  const { program, accounts } = useTokenvestingProgram()

  const accountQuery = useQuery({
    queryKey: ['tokenvesting', 'fetch', { cluster, account }],
    queryFn: () => program.account.vestingAccount.fetch(account) //.tokenvesting.fetch(account),
  })
  // 创建员工
  const createEmployeeVesting = useMutation<string, unknown, CreateEmployeeArgs>({
    mutationKey: ['employeeAccount', 'create', { cluster }],
    mutationFn: async ({startTime, endTime, totalAmount, cliffTime,beneficiary}) => {
      const tx = await program.methods
        .createEmployeeAccount(startTime,endTime,totalAmount,cliffTime) // 这里的参数需要和rust的函数一             
        .rpc()
      return tx
    },
    onSuccess: (tx) => {
      transactionToast(tx)
      return accounts.refetch()
    },
    onError: (error) => {
      toast.error(`创建失败: ${error}`)
    }
  })

  return {
    accountQuery,
    createEmployeeVesting,
  }
}
