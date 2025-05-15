import { Cluster, Connection, TransactionSignature, TransactionConfirmationStatus, SignatureStatus } from "@solana/web3.js";

export const getExplorerUrl = (signature: string, cluster: Cluster) => {
    return `https://explorer.solana.com/tx/${signature}?cluster=${cluster}`;
}
// 并缩短长哈希值
export const shortenHash = (str:string) => {
    return `${str.slice(0, 4)}...${str.slice(-4)}`;
}
// 函数来确认交易是否成功
export async function confirmTransaction(
    connection: Connection,
    signature: TransactionSignature,
    desiredConfirmationStatus: TransactionConfirmationStatus = 'confirmed',
    timeout: number = 30000,
    pollInterval: number = 1000,
    searchTransactionHistory: boolean = false
): Promise<SignatureStatus> {
    const start = Date.now();

    while (Date.now() - start < timeout) {
        const { value: statuses } = await connection.getSignatureStatuses([signature], { searchTransactionHistory });

        if (!statuses || statuses.length === 0) {
            throw new Error('Failed to get signature status');
        }

        const status = statuses[0];

        if (status === null) {
            await new Promise(resolve => setTimeout(resolve, pollInterval));
            continue;
        }

        if (status.err) {
            throw new Error(`Transaction failed: ${JSON.stringify(status.err)}`);
        }

        if (status.confirmationStatus && status.confirmationStatus === desiredConfirmationStatus) {
            return status;
        }

        if (status.confirmationStatus === 'finalized') {
            return status;
        }

        await new Promise(resolve => setTimeout(resolve, pollInterval));
    }

    throw new Error(`Transaction confirmation timeout after ${timeout}ms`);
};

