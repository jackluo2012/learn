
import React, { FC, useCallback, useState } from 'react';
import { Transaction, TransactionInstruction } from '@solana/web3.js';
import { useConnection, useWallet } from '@solana/wallet-adapter-react';
import type { Keypair, TransactionSignature } from '@solana/web3.js';
import { getExplorerUrl, shortenHash, confirmTransaction } from '@/utils/utils';
import { Toaster, toast } from 'sonner';
import { cluster } from '@/utils/constants';

type SendTransactionTemplateProps = {
    transactionInstructions: TransactionInstruction[];
    buttonLabel: string;
    extraSigners?: Keypair[];
    invisible?: boolean;
    width?: number;
    onSuccess?: () => void;
};

// 多重签名
export const SendTransactionTemplate: FC<SendTransactionTemplateProps> = ({ transactionInstructions, buttonLabel, extraSigners, width, invisible = false, onSuccess }) => {
    const { connection } = useConnection();
    const { publicKey, sendTransaction } = useWallet();
    const [isLoading, setIsLoading] = useState(false);
    // 当按钮被点击时会调用该函数。该函数会创建并发送交易。
    const onClick = useCallback(async () => {
        try {
            if (!publicKey) throw new Error('Wallet not connected!');
            setIsLoading(true);
            // 最新的区块哈希和上下文
            const {
                context: { slot: minContextSlot },
                value: { blockhash, lastValidBlockHeight },
            } = await connection.getLatestBlockhashAndContext();
            // 并使用扩展运算符添加作为
            const transaction = new Transaction().add(...transactionInstructions);
            // 最近的区块哈希，并将 feePayer 定义为连接的钱包
            transaction.recentBlockhash = blockhash;
            transaction.feePayer = publicKey;
            if (extraSigners) transaction.partialSign(...extraSigners);
            // useWallet 钩子中的 sendTransaction 方法将交易发送到集群
            let signature: TransactionSignature = await sendTransaction(transaction, connection, { minContextSlot });

            const url = getExplorerUrl(signature, cluster);
            // 函数来确认交易是否成功
            await confirmTransaction(connection, signature);
            // 返回交易的签名
            toast.success(<div><a href={url} target='_blank' rel='noreferrer'>Success! {shortenHash(signature)}</a></div>);
            if (onSuccess) { 
                onSuccess() 
            }
        } catch (error: any) {
            toast.error(`Error: ${error.message}`);
        } finally {
            setIsLoading(false);
        }

    }, [publicKey, connection, sendTransaction, transactionInstructions, extraSigners, onSuccess]);

    return (
        <div className={`${invisible ? 'w-full h-full' : ''} flex items-center justify-center w-full h-full`}>
            <Toaster richColors />
            <button
                onClick={onClick}
                disabled={!publicKey || isLoading}
                className={invisible
                    ? `w-full h-full bg-transparent border-none focus:outline-none z-10 text-opacity-0 hover:text-opacity-40 text-white`
                    : `w-${width ?? 80} inline-flex items-center justify-center bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50 disabled:cursor-not-allowed transition duration-150 ease-in-out transform active:scale-95 m-5 ${isLoading ? 'opacity-75' : ''}`
                }

            >
                {isLoading ? (
                    <div className="flex items-center justify-center">
                        <SpinnerIcon />
                    </div>
                ) : (
                    buttonLabel
                )}
            </button>

        </div>
    );

};
// 加载旋转图标
const SpinnerIcon = () => (
    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 0116 0H4z"></path>
    </svg>
);