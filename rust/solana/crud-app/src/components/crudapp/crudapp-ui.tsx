'use client'

import { Keypair, PublicKey } from '@solana/web3.js'
import { ellipsify } from '../ui/ui-layout'
import { ExplorerLink } from '../cluster/cluster-ui'
import { useCrudappProgram, useCrudappProgramAccount } from './crudapp-data-access'
import { useState } from 'react'
import { useWallet } from '@solana/wallet-adapter-react'

export function CrudappCreate() {
 
  const [title,setTitle] = useState('')
  const [message,setMessage] = useState('')
  const {createEntry} = useCrudappProgram()
  // 使用钱包地址公钥
  const { publicKey } = useWallet();
  const isFormValid = title.trim().length > 0 && message.length > 0 && publicKey !== null;
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isFormValid) {
      alert('Please fill in all fields.')
      return;
    }
    try {
      await createEntry.mutateAsync({title,message,owner: publicKey})
      // Reset the form fields after successful submission
      setTitle('')
      setMessage('')
    } catch (error) {
      console.error('Failed to create entry:', error);
    }
  };
  if (!publicKey) {
    return (
      <div className="alert alert-error flex justify-center">
        <span>Please connect your wallet to create an entry.</span>
      </div>
    );
  }

  // 构建一个表单，需要上面的数据做为input
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="title" className="block text-sm font-medium">
          Title
        </label>
        <input
          id="title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="input input-bordered w-full max-w-xs"
          placeholder="Enter title"
          required
        />
      </div>
      <div>
        <label htmlFor="message" className="block text-sm font-medium">
          Message
        </label>
        <textarea
          id="message"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="textarea textarea-bordered w-full max-w-xs"
          placeholder="Enter message"
          required
        />
      </div>
      <button
        type="submit"
        className="btn btn-primary w-full"
        disabled={createEntry.isPending || !isFormValid}
      >
        Create Entry
      </button>
    </form>
  );
}

export function CrudappList() {
  const { accounts, getProgramAccount } = useCrudappProgram()

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
          {accounts.data?.map((account) => (
            <CrudappCard key={account.publicKey.toString()} account={account.publicKey} />
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

function CrudappCard({ account }: { account: PublicKey }) {
  const { accountQuery, updateEntry, deleteEntry } = useCrudappProgramAccount({
    account,
  });

  const { publicKey } = useWallet();
  const [message, setMessage] = useState('');
  const [localContent, setLocalContent] = useState<string | undefined>(accountQuery.data?.message);
  const title = accountQuery.data?.title;
  const hash = account.toString();

  const isFormValid = message.trim().length > 0 && publicKey !== null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid) {
      alert('Please fill in all fields.');
      return;
    }
    try {
      await updateEntry.mutateAsync({ title, message, owner: publicKey });
      setLocalContent(message); // Update the local content after successful submission
      setMessage(''); // Reset the message field after successful submission
    } catch (error) {
      console.error('Failed to update entry:', error);
    }
  };

  return accountQuery.isLoading ? (
    <span className="loading loading-spinner loading-lg"></span>
  ) : (
    <div className="card card-bordered border-primary border-2 text-neutral-content shadow-lg bg-base-100">
      <div className="card-body space-y-6">
        <h2 className="card-title text-2xl font-bold text-primary">{title || 'Untitled'}</h2>
        <p className="text-base text-gray-800 whitespace-pre-line">{localContent || 'No content available.'}</p>
        <p className="text-sm text-gray-500">
          <span className="font-semibold">Hash:</span>{' '}
          <ExplorerLink path={`account/${account}`} label={ellipsify(hash)} />
        </p>
        <form onSubmit={handleSubmit} className="space-y-4 mt-6">
          <label htmlFor={`update-message-${hash}`} className="block text-sm font-medium text-gray-700">
            Update Message
          </label>
          <textarea
            id={`update-message-${hash}`}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="textarea textarea-bordered w-full bg-white text-gray-800"
            placeholder="Enter updated message"
            required
          />
          <div className="flex justify-between items-center mt-4">
            <button
              type="submit"
              className="btn btn-primary btn-wide"
              disabled={updateEntry.isPending || !isFormValid}
            >
              Update
            </button>
            <button
              type="button"
              className="btn btn-error btn-wide"
              onClick={() => {
                const title = accountQuery.data?.title;
                if (title && window.confirm('Are you sure you want to delete this entry?')) {
                  deleteEntry.mutate(title);
                }
              }}
              disabled={deleteEntry.isPending}
            >
              Delete
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
