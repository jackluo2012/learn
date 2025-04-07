use solana_client::nonblocking::rpc_client::RpcClient;
use solana_sdk::{
    address_lookup_table::program, 
    commitment_config::CommitmentConfig, 
    signature::Keypair, signer::Signer, 
    system_instruction, system_program, 
    transaction::Transaction,
    pubkey,
    pubkey::Pubkey,
};
use std::fs;
use serde_json;
use shellexpand;

#[tokio::main]
async  fn main() -> anyhow::Result<()> {
    
    let url = String::from("https://api.devnet.solana.com");
    let client = RpcClient::new_with_commitment(url, CommitmentConfig::confirmed());
    // 获取本的账户
    let keypair = load_local_keypair();
    // 创建一个新的账户
    {
        let new_account = create_new_account(&client, &keypair).await?;
        println!("新账户公钥: {}", new_account.pubkey());
    }
    // 创建 PDA 账户
    {
        let program_id = pubkey!("11111111111111111111111111111111");
        let seeds:&[&[u8]] = &[b"example_seed", b"OKK"];
        let pda_account = create_pda_account(&client, &keypair, &program_id, seeds).await?;
        println!("PDA 账户公钥: {}", pda_account);
        // 这里可以添加对 PDA 账户的进一步操作
    }
    Ok(())
}
// 如何创建 PDA 的帐户
// 在程序派生地址 （PDA） 中找到的帐户只能在链上创建。这些账户的地址具有关联的 off-curve 公有密钥，但没有 secret key。
// 要生成 PDA，请将 findProgramAddressSync 与所需的种子一起使用。使用相同的种子生成将始终生成相同的 PDA。
/**
 * 传入程序 ID 和种子数组，返回 PDA 地址
 */
fn find_program_address_sync(program_id: &Pubkey, seeds: &[&[u8]]) -> Pubkey {
    // 定义种子和程序 ID
    let (pda, _bump_seed) = Pubkey::find_program_address(seeds, program_id);
    pda
}
// 创建 pad 账户
async fn create_pda_account(client: &RpcClient, payer_acount: &Keypair,program_id: &Pubkey, seeds: &[&[u8]]) -> anyhow::Result<Pubkey> {
    // 计算 PDA 地址
    let pda = find_program_address_sync(program_id, seeds);
    // 计算账户租金豁免所需的最低余额
    let data_len = 0; // 账户数据长度（0表示空账户）
    let rent_exemption_amount = calculate_account_creation_cost(client, data_len).await?;
    // 创建系统程序的交易指令（创建账户）
    let create_account_ix = system_instruction::create_account(
        &payer_acount.pubkey(),// 支付方的id
        &pda,
        rent_exemption_amount,
        data_len as u64, // // 账户数据长度（0表示空账户）
        program_id, //  PDA 的所属程序 ID
    );
    // 构建交易（包含指令，并指定支付方）
    let mut transaction = Transaction::new_with_payer(
        &[create_account_ix], // 交易指令列表
        Some(&payer_acount.pubkey()), // 交易费用支付方
    );
    // 签名交易
    transaction.sign(
        &[payer_acount], // // 签名者列表（仅支付方签名）
        client.get_latest_blockhash().await?, // 当前区块哈希
    );
    // 发送交易
    client.send_and_confirm_transaction(&transaction).await?;
    println!("创建 PDA 账户成功，交易签名: {}", transaction.signatures[0]);
    Ok(pda)
}


// 计算账户创建成本
async fn calculate_account_creation_cost(client: &RpcClient,data_len:u64) -> anyhow::Result<u64> {
    
    // let data_len = 0; // 账户数据长度（0表示空账户）
    // 计算账户租金豁免所需的最低余额
    let rent_exemption_amount = client
        .get_minimum_balance_for_rent_exemption(data_len as usize)
        .await?;
    Ok(rent_exemption_amount)

}
// 创建一个新的账户
async fn create_new_account(client: &RpcClient, from: &Keypair) -> anyhow::Result<Keypair>  {
    // 创建一个新的账户
    let new_account_keypair = Keypair::new();
    let data_len = 0; // 账户数据长度（0表示空账户）
    let rent_exemption_amount = calculate_account_creation_cost(client,data_len).await?; // 计算账户创建成本
    // 创建系统程序的交易指令（创建账户）
    let create_account_ix = system_instruction::create_account(
        &from.pubkey(),
        &new_account_keypair.pubkey(),
        rent_exemption_amount,
        data_len as u64, // 账户数据长度
        &system_program::id(), // 转帐程序的id
    );
    // 构建交易（包含指令，并指定支付方）
    let mut transaction = Transaction::new_with_payer(
        &[create_account_ix], // 交易指令列表
        Some(&from.pubkey()), // 交易费用支付方
    );
    // 签名交易
    transaction.sign(
        &[from, &new_account_keypair], // 签名者列表（需包含所有必要密钥对）
        client.get_latest_blockhash().await?, // 当前区块哈希
    );
    // 发送交易
    client.send_and_confirm_transaction(&transaction).await?;
    println!("创建账户成功，交易签名: {}", transaction.signatures[0]);
    // 返回创建的账户密钥对
    Ok(new_account_keypair)
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
