
import { useWallet } from '@solana/wallet-adapter-react';
import Balance from './Balance';
import SendMemoButton from './SendTransactionButtons/SendMemo';
import CreateTokenButton from './SendTransactionButtons/CreateToken';
import TokenTable from './TokenTable';
const Main = () => {
    const { connected } = useWallet();
    return (
        <div className="flex flex-col items-center justify-between p-24">
            {connected ?
                <div className="flex flex-col items-center justify-center">
                    <Balance />
                    <SendMemoButton message='Hello from Jack Solana!' />
                    <CreateTokenButton />
                    <TokenTable />
                </div>
                :
                <div>Wallet Not Connected</div>}
        </div>
    )
}
export default Main;