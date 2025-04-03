use solana_client::nonblocking::rpc_client::RpcClient;
use solana_sdk::{
    client, commitment_config::CommitmentConfig, native_token::LAMPORTS_PER_SOL, pubkey:: Pubkey, signature::Keypair, signer::Signer, system_instruction::transfer, transaction::{self, Transaction}
};
use spl_memo::build_memo;
use std::fs;
use std::path::Path;

#[tokio::main]
async fn main() ->anyhow::Result<()> {
    // let url = String::from("http://localhost:8899");
    let url = String::from("https://api.devnet.solana.com");
    let client = RpcClient::new_with_commitment(url, CommitmentConfig::confirmed());
    // 获取本的账户
    let keypair = load_local_keypair();


    println!("如何发送SOL==============start===============");

    // 创建一个异步运行时
    {
        send_sol(&client,&keypair).await?;
    }
    println!("如何发送SOL==============end===============");

    println!("如何计算交易成本==============start===============");
    {
        calculate_transaction_cost(&client,&keypair).await?;
    }
    println!("如何计算交易成本==============end===============");
    println!("如何将 Memo 添加到交易中==============start===============");
    {
        add_memo_to_transaction(&client,&keypair,"如何将 Memo 添加到交易中".to_string()).await?;
    }
    println!("如何将 Memo 添加到交易中==============end===============");

    {
        load_local_keypair();
        // let private_key_base58 = "";
        // // 从 Phantom 钱包导出的私钥（Base58 编码字符串）
        // write_phantom_wallet_to_env(private_key_base58).await?;
    }

    Ok(())
}

// 发送SOL
async fn send_sol(client: &RpcClient,from_keypair:&Keypair) -> anyhow::Result<()> {
    // 创建一个异步运行时
    
    
    // 转账的帐号
    // let from_keypair = Keypair::new();
    let to_keypair = Keypair::new();
    let from = from_keypair.pubkey();
    let to = to_keypair.pubkey();
    
    // 进行空投
    // airdrop(&client, from, 5).await?;
    // 获取最新的区块哈希
    let latest_blockhash = client.get_latest_blockhash().await?;

    // 创建一个转账指令
    let transfer_ix = transfer(&from, &to, LAMPORTS_PER_SOL);
    let mut transaction = Transaction::new_with_payer(&[transfer_ix], Some(&from));

    // 签名交易
    transaction.sign(&[&from_keypair], latest_blockhash);

    // 发送交易
    match client.send_transaction(&transaction).await {
        Ok(sig) => {
            println!("交易成功，签名为：{}", sig);
        }
        Err(err) => {
            println!("交易失败，错误信息为：{}", err);
        }
    }
    Ok(())
}
// 进行空投
async fn airdrop(client: &RpcClient,pb:Pubkey,amount:u64) -> anyhow::Result<()> {
    let transation_signature = client.request_airdrop(&pb, amount*LAMPORTS_PER_SOL).await?;
    loop {
        if client.confirm_transaction(&transation_signature).await? {
            println!("airdrop成功");
            break;
        } else {
            println!("airdrop失败，正在重试");
            tokio::time::sleep(std::time::Duration::from_secs(1)).await;
        }
    }
    Ok(())
}

// 计算交易成本 
async fn calculate_transaction_cost(client: &RpcClient,signer_keypair:&Keypair) -> anyhow::Result<()> {
    // 创建一个帐号
    // let signer_keypair = from_keypair;
    let from = signer_keypair.pubkey();
    //构建一个指令
    let memo = String::from("Hello, Solana!");
    let memo_ix = build_memo(memo.as_bytes(), &[&from]);    
    let mut transaction = Transaction::new_with_payer(&[memo_ix], Some(&from));
    // 进行签名
    // 获取最新的区块哈希
    // let latest_blockhash = client.get_latest_blockhash().await?;
    transaction.sign(&[&signer_keypair], client.get_latest_blockhash().await?);

    // 给帐号进行允钱
    // airdrop(client, from, 10).await?;

    
   // 估计CU使用量
    let cu_used = estimate_cu_used(client, &transaction).await?;
    println!("模拟交易成本为：{}", cu_used);

    let tx_cost = client.get_fee_for_message(&transaction.message).await?;
    println!("交易成本为：{}", tx_cost);

    match client.send_transaction(&transaction).await {
        Ok(sig) => {
            println!("交易成功，签名为：{}", sig);
        }
        Err(err) => {
            println!("交易失败，错误信息为：{}", err);
        }
    }
    Ok(())

}
// 计算交易成本
async fn estimate_cu_used(client: &RpcClient, tx: &Transaction) -> anyhow::Result<u64> {
    let sim_res = client.simulate_transaction(tx).await?;

    let units_consumed = sim_res
        .value
        .units_consumed
        .expect("couldn't estimate CUs used");

    Ok(units_consumed)
}

// 如何将 Memo 添加到交易中
async fn add_memo_to_transaction(client: &RpcClient,signer_keypair:&Keypair,message:String) -> anyhow::Result<()> {
    // 创建一个帐号
    // let signer_keypair = Keypair::new();
    let from = signer_keypair.pubkey();
    //构建一个指令
    
    let memo_ix = build_memo(message.as_bytes(), &[&from]); 

    // 进行空投
    // airdrop(client, from, 10).await?;

    let mut transaction = Transaction::new_with_payer(&[memo_ix], Some(&from));
    transaction.sign(&[&signer_keypair], client.get_latest_blockhash().await?);
    // 发送交易
    match client.send_and_confirm_transaction(&transaction).await {
        Ok(sig) => {
            println!("交易成功，签名为：{}", sig);
        }
        Err(err) => {
            println!("交易失败，错误信息为：{}", err);
        }
    }
    Ok(())
}

// 将 Phantom 钱包写入本地环境中
async fn write_phantom_wallet_to_env(private_key_base58: &str) -> anyhow::Result<()> {
    // 从 Phantom 钱包导出的私钥（Base58 编码字符串）
    // 将私钥解析为 Keypair
    let keypair = Keypair::from_base58_string(private_key_base58);

    // 打印钱包地址
    println!("导入的 Phantom 钱包地址: {}", keypair.pubkey());

    // 将密钥对写入到 ~/.config/solana/id.json 文件
    let expanded_path = shellexpand::tilde("~/.config/solana/id.json").to_string(); // 将路径绑定到变量
    let keypair_path = Path::new(&expanded_path); // 使用绑定的变量
    save_keypair_to_file(&keypair, keypair_path).expect("Failed to save keypair");

    println!("密钥对已保存到: {}", keypair_path.display());
    Ok(())
}

// 将密钥对保存到文件
fn save_keypair_to_file(keypair: &Keypair, path: &Path) -> std::io::Result<()> {
    // 确保父目录存在
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }

    // 将密钥对字节数组转换为 JSON 格式
    let json_data = serde_json::to_string(&keypair.to_bytes().to_vec())
        .expect("Failed to serialize keypair");

    // 写入文件
    fs::write(path, json_data)?;

    Ok(())
}

// 加载本地帐号钱包
fn load_local_keypair() -> Keypair {
    // 加载本地密钥对
    let keypair_path = shellexpand::tilde("~/.config/solana/id.json").to_string(); // 展开路径
    let keypair = read_keypair_file(&keypair_path).expect("Failed to read keypair file");
    println!("本地账户公钥: {}", keypair.pubkey());
    keypair
}

// 从文件加载密钥对
fn read_keypair_file(path: &str) -> Result<Keypair, Box<dyn std::error::Error>> {
    // 读取文件内容
    let json_data = fs::read_to_string(path)?;
    // 将 JSON 数据解析为字节数组
    let keypair_bytes: Vec<u8> = serde_json::from_str(&json_data)?;
    // 将字节数组转换为 Keypair
    let keypair = Keypair::from_bytes(&keypair_bytes).expect("Invalid keypair format");
    Ok(keypair)
}
