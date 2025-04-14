'use client'

import { Keypair, PublicKey } from '@solana/web3.js'
import { useMemo, useState } from 'react'
import { ellipsify } from '../ui/ui-layout'
import { ExplorerLink } from '../cluster/cluster-ui'
import { useTokenvestingProgram, useTokenvestingProgramAccount } from './tokenvesting-data-access'
import { useWallet } from '@solana/wallet-adapter-react'
import DatePicker from 'react-datepicker'
import 'react-datepicker/dist/react-datepicker.css'

export function TokenvestingCreate() {
  const { createTokenvesting } = useTokenvestingProgram()
  const [companyName, setCompanyName] = useState('')
  const [mint, setMint] = useState('')
  // 获取钱包的公钥
  const { publicKey } = useWallet()

  const isFormValid = companyName.trim().length>0 && mint.trim().length>0 
  const handleCreate = async () => {
    if (!isFormValid || !publicKey) {
      alert('Please fill in all fields and ensure your wallet is connected.')
      return
    }
    try {
      await createTokenvesting.mutateAsync({
        companyName,
        mint,        
      });
      alert('Token vesting account created successfully!')
      setCompanyName('')
      setMint('')
    } catch (error) {
      console.error(error)
      alert('Failed to create token vesting account.')
    }
  }
  // 如果没有连接钱包，提示连接钱包
  if (!publicKey) {
    return (
      <div className="alert alert-error flex justify-center">
        <span>Please connect your wallet to create a new token vesting account.</span>
      </div>
    )
  }


  return (
    <div className="space-y-4">
      <div className="form-control">
        <label className="label">
          <span className="label-text">Company Name</span>
        </label>
        <input
          type="text"
          placeholder="Enter company name"
          className="input input-bordered"
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
        />
      </div>
      <div className="form-control">
        <label className="label">
          <span className="label-text">Mint Address</span>
        </label>
        <input
          type="text"
          placeholder="Enter mint address"
          className="input input-bordered"
          value={mint}
          onChange={(e) => setMint(e.target.value)}
        />
      </div>
      <button
        className="btn btn-primary w-full"
        onClick={handleCreate}
        disabled={createTokenvesting.isPending || !isFormValid}
      >
        Create New Vesting Account {createTokenvesting.isPending && '...'}
      </button>
    </div>
  )
}

export function TokenvestingList() {
  const { accounts, getProgramAccount } = useTokenvestingProgram()

  if (getProgramAccount.isLoading) {
    return <span className="loading loading-spinner loading-lg"></span>
  }
  if (!getProgramAccount.data?.value) {
    return (
      <div className="alert alert-info flex justify-center">
        <span>Program account not found. Make sure you have deployed the program and are on the correct cluster.</span>
      </div>
    )
  }
  return (
    <div className={'space-y-6'}>
      {accounts.isLoading ? (
        <span className="loading loading-spinner loading-lg"></span>
      ) : accounts.data?.length ? (
        <div className="grid md:grid-cols-2 gap-4">
          {accounts.data?.map((account: { publicKey: PublicKey }) => (
            <TokenvestingCard key={account.publicKey.toString()} account={account.publicKey} />
          ))}
        </div>
      ) : (
        <div className="text-center">
          <h2 className={'text-2xl'}>No accounts</h2>
          No accounts found. Create one above to get started.
        </div>
      )}
    </div>
  )
}

function TokenvestingCard({ account }: { account: PublicKey }) {
  const { accountQuery, createEmployeeVesting } = useTokenvestingProgramAccount({
    account,
  })

  const [startTime, setStartTime] = useState<Date | null>(null)
  const [endTime, setEndTime] = useState<Date | null>(null)
  const [totalAmount, setTotalAmount] = useState(0)
  const [cliffTime, setCliffTime] = useState<Date | null>(null)
  const [beneficiary, setBeneficiary] = useState('')

  const companyName = useMemo(() => accountQuery.data?.companyName, [accountQuery.data?.companyName])
  const handleCreateVesting = async () => {
    if (!startTime || !endTime || !totalAmount || !cliffTime || !beneficiary) {
      alert('Please fill in all fields.')
      return
    }
    try {
      await createEmployeeVesting.mutateAsync({
        startTime: startTime ? Math.floor(startTime.getTime() / 1000) : 0,
        endTime: endTime ? Math.floor(endTime.getTime() / 1000) : 0,
        totalAmount: parseFloat(totalAmount.toString()),
        cliffTime: cliffTime ? Math.floor(cliffTime.getTime() / 1000) : 0,
        beneficiary,
      })
      alert('Employee vesting created successfully!')
      setStartTime(null)
      setEndTime(null)
      setTotalAmount(0)
      setCliffTime(null)
      setBeneficiary('')
    } catch (error) {
      console.error(error)
      alert('Failed to create employee vesting.')
    }
  }

  return accountQuery.isLoading ? (
    <span className="loading loading-spinner loading-lg"></span>
  ) : (
    <div className="card card-bordered border-base-300 border-4 text-neutral-content shadow-lg">
      <div className="card-body">
        <h2 className="card-title text-2xl text-center mb-4">{companyName || 'Unknown Company'}</h2>
        <div className="space-y-4">
          <div className="form-control">
            <label className="label">
              <span className="label-text">Start Time</span>
            </label>
            <DatePicker
              selected={startTime}
              onChange={(date) => setStartTime(date)}
              showTimeSelect
              dateFormat="Pp"
              className="input input-bordered"
              placeholderText="Select start time"
            />
          </div>
          <div className="form-control">
            <label className="label">
              <span className="label-text">End Time</span>
            </label>
            <DatePicker
              selected={endTime}
              onChange={(date) => setEndTime(date)}
              showTimeSelect
              dateFormat="Pp"
              className="input input-bordered"
              placeholderText="Select end time"
            />
          </div>
          <div className="form-control">
            <label className="label">
              <span className="label-text">Total Amount</span>
            </label>
            <input
              type="number"
              placeholder="Enter total amount"
              className="input input-bordered"
              value={totalAmount}
              onChange={(e) => setTotalAmount(Number(e.target.value))}
            />
          </div>
          <div className="form-control">
            <label className="label">
              <span className="label-text">Cliff Time</span>
            </label>
            <DatePicker
              selected={cliffTime}
              onChange={(date) => setCliffTime(date)}
              showTimeSelect
              dateFormat="Pp"
              className="input input-bordered"
              placeholderText="Select cliff time"
            />
          </div>
          <div className="form-control">
            <label className="label">
              <span className="label-text">Beneficiary Address</span>
            </label>
            <input
              type="text"
              placeholder="Enter beneficiary address"
              className="input input-bordered"
              value={beneficiary}
              onChange={(e) => setBeneficiary(e.target.value)}
            />
          </div>
          <button
            className="btn btn-primary w-full"
            onClick={handleCreateVesting}
            disabled={createEmployeeVesting.isPending}
          >
            Create Employee Vesting Account {createEmployeeVesting.isPending && '...'}
          </button>
        </div>
        <div className="divider"></div>
      </div>
    </div>
  )
}
