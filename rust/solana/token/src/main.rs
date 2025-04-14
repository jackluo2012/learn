use solana_client::nonblocking::rpc_client::RpcClient;
use solana_sdk::{
    // address_lookup_table::program, 
    commitment_config::CommitmentConfig, 
    program_pack::Pack, pubkey::{self,  Pubkey}, 
    signature::Keypair, signer::Signer, 
    system_instruction::{self, create_account}, system_program,
    
    transaction::Transaction,
};
use spl_associated_token_account::{
    get_associated_token_address_with_program_id, instruction::create_associated_token_account,
};
use spl_token_2022::{id, 
    instruction::{initialize_mint, initialize_account,mint_to,transfer_checked}, 
    state::{Mint,Account},
};
use std::fs;
use serde_json;
use shellexpand;
const LAMPORTS_PER_SOL: u64 = 1_000_000_000;
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // 1. 初始化客户端和支付账户
    let client = RpcClient::new_with_commitment(
        "https://api.devnet.solana.com".to_string(),
        CommitmentConfig::confirmed()
    );
    let payer = load_local_keypair();
    println!("==== 初始化完成 ====");
    println!("使用账户: {}", payer.pubkey());

    // 2. 创建 Mint 账户
    let mint = create_mint_account(&client, &payer, 9).await?;
    println!("Mint 账户: {}", mint.pubkey());

    // 3. 创建源账户和目标账户
    let (source_owner, source_account) = create_token_account(&client, &payer, &mint).await?;
    let (dest_owner, dest_account) = create_token_account(&client, &payer, &mint).await?;

    // 4. 铸造代币到源账户
    let mint_amount = 1_000_000_000_000;
    mint_tokens(&client, &payer, &mint, &source_account, mint_amount).await?;
    
    // 5. 执行转账
    let transfer_amount = 1_200;
    print_token_balance(&client, &source_account, "转账前源账户").await?;
    transfer_tokens(
        &client,
        &source_owner,
        &mint,
        &source_account,
        &dest_account,
        transfer_amount,
    ).await?;

    // 6. 打印最终余额
    print_token_balance(&client, &source_account, "转账后源账户").await?;
    print_token_balance(&client, &dest_account, "转账后目标账户").await?;

    println!("==== 所有操作完成 ✓ ====");
    Ok(())
}

// 获取token 账户的余额
async fn get_token_account_balance(
    client: &RpcClient,
    token_account_pubkey: &Pubkey,
) -> anyhow::Result<u64> {
    let account = client.get_token_account_balance(token_account_pubkey).await?;
    Ok(account.amount.parse::<u64>()?)
}


// 如何转移代币
// 要转移代币，请调用 转账 指令。您可以找到此指令的实现 这里 。
// 转移代币的交易需要两个说明：
// 调用系统程序为 Token 账户创建和分配空间，并将所有权转移给 Token Program。
// 调用 Token Program 以转移代币并将其发送到指定的 Token 账户。
/// 在账户之间转移代币
/// 
/// # Arguments
/// * `client` - RPC 客户端
/// * `owner` - 源账户所有者的密钥对
/// * `mint` - 代币的 Mint 账户
/// * `source` - 源 Token 账户地址
/// * `destination` - 目标 Token 账户地址
/// * `amount` - 转账金额
async fn transfer_tokens(
    client: &RpcClient,
    owner: &Keypair,
    mint: &Keypair,
    source: &Pubkey,
    destination: &Pubkey,
    amount: u64,
) -> anyhow::Result<()> {
    // 1. 打印转账详情
    println!("==== 代币转账详情 ====");
    println!("源账户: {}", source);
    println!("目标账户: {}", destination);
    println!("转账金额: {}", amount);

    // 2. 创建转账指令
    let transfer_ix = transfer_checked(
        &spl_token_2022::id(),
        source,
        &mint.pubkey(),
        destination,
        &owner.pubkey(),
        &[&owner.pubkey()],
        amount,
        9, // decimals
    )?;

    // 3. 创建并签名交易
    let latest_blockhash = client.get_latest_blockhash().await?;
    let tx = Transaction::new_signed_with_payer(
        &[transfer_ix],
        Some(&owner.pubkey()),
        &[owner],
        latest_blockhash,
    );

    // 4. 发送交易并等待确认
    let signature = client.send_and_confirm_transaction(&tx).await?;
    println!("转账成功 ✓");
    println!("交易签名: {}", signature);

    Ok(())
}

// 原生代币转账
// 调用 Token Program 以转移代币并将其发送到指定的 Token 账户。
async fn transfer_native_tokens(
    client: &RpcClient,
    payer: &Keypair,
    destination: &Keypair,
    amount: u64,
) -> anyhow::Result<()> {
        
    // 创建转账指令
    let transfer_ix = system_instruction::transfer(
        &payer.pubkey(),// mint 账户的公钥
        &destination.pubkey(),// 目mint 账户的公钥
        amount,// 铸造的数量
    );
    // 创建交易 并签名
    let tx = Transaction::new_signed_with_payer(
        &[transfer_ix],
        Some(&payer.pubkey()),
        &[payer],
        client.get_latest_blockhash().await?,
    );
    // 发送交易
    let transaction_signature = client.send_and_confirm_transaction(&tx).await?;
    println!("转移原生代币成功，交易签名: {}", transaction_signature);
    Ok(())
}



// 创建帐号
async fn create_account_keypair(
    client: &RpcClient,
    payer: &Keypair,
) -> anyhow::Result<Keypair> {
    // 创建一个新的密钥对作为 token 账户
    let token_keypair = Keypair::new();
    let token_pubkey = token_keypair.pubkey();
    println!("新帐号公钥: {}", token_pubkey);
    transfer_native_tokens(client, payer, &token_keypair,  LAMPORTS_PER_SOL).await?;
    
    Ok(token_keypair)
}


// 如何铸造代币
// 要铸造代币，请调用铸造指令。您可以找到此指令的实现 这里 。
// 铸造代币的交易需要两个说明：
// 调用系统程序为铸币厂账户创建和分配空间，并将所有权转移给代币计划。
// 调用 Token Program 以铸造代币并将其发送到指定的 Token 账户。
/// 铸造代币到指定的 Token 账户
/// 
/// # Arguments
/// * `client` - RPC 客户端
/// * `payer` - 支付者/铸币权限拥有者的密钥对
/// * `mint` - Mint 账户的密钥对
/// * `associated_token_address` - 接收代币的关联账户地址
/// * `amount` - 要铸造的代币数量
async fn mint_tokens(
    client: &RpcClient,
    payer: &Keypair,
    mint: &Keypair,
    associated_token_address: &Pubkey,
    amount: u64
) -> anyhow::Result<()> {
    // 1. 验证 Mint 账户
    let mint_account = client.get_account(&mint.pubkey()).await?;
    if mint_account.owner != id() {
        anyhow::bail!("Mint 账户所有权不正确，期望: {}, 实际: {}", id(), mint_account.owner);
    }

    // 2. 打印调试信息
    println!("==== 铸造代币详情 ====");
    println!("Mint Authority: {}", payer.pubkey());
    println!("Mint Account: {}", mint.pubkey());
    println!("Token Account: {}", associated_token_address);
    println!("铸造数量: {}", amount);

    // 3. 创建铸造指令
    let mint_ix = mint_to(
        &id(),
        &mint.pubkey(),
        associated_token_address,
        &payer.pubkey(), // mint authority
        &[&payer.pubkey()], // signers
        amount,
    )?;

    // 4. 创建并签名交易
    let latest_blockhash = client.get_latest_blockhash().await?;
    let tx = Transaction::new_signed_with_payer(
        &[mint_ix],
        Some(&payer.pubkey()),
        &[payer], // 只需要 mint authority 的签名
        latest_blockhash,
    );

    // 5. 发送交易并等待确认
    let signature = client.send_and_confirm_transaction(&tx).await?;
    println!("铸造代币成功 ✓");
    println!("交易签名: {}", signature);

    Ok(())
}


// 如何创建关联的 Token 账户
// 要创建关联的令牌账户，请调用 创造 指令。您可以找到此指令的实现 这里 。

// 创建关联 Token 账户的指令会自动调用 System Program 创建 Token 账户，
// 并调用 Token Program 初始化 Token 账户数据。这是通过跨程序调用 （CPI） 实现的。

async fn create_associated_token_address(
    client: &RpcClient,
    payer: &Keypair,    
    mint: &Keypair,
) -> anyhow::Result<Pubkey> {
    let associated_token_address = get_associated_token_address_with_program_id(
        &payer.pubkey(), 
        &mint.pubkey(), 
        &id(),
    );

    let create_ata_instruction = create_associated_token_account(
        &payer.pubkey(),
        &payer.pubkey(),
        &mint.pubkey(),
        &id(),
    );

    let transaction = Transaction::new_signed_with_payer(
        &[create_ata_instruction],
        Some(&payer.pubkey()),
        &[payer],
        client.get_latest_blockhash().await?,
    );
    // 发送交易
    let transaction_signature = client.send_and_confirm_transaction(&transaction).await?;
    println!("关联 Token 账户创建成功，交易签名: {}", transaction_signature);
    println!("关联 Token 账户公钥: {}", associated_token_address);

    // 检查账户是否已初始化
    let account_data = client.get_account_data(&associated_token_address).await?;
    if account_data.is_empty() {
        anyhow::bail!("关联 Token 账户未初始化");
    }

    Ok(associated_token_address)
}




// 如何创建 Token 账户
async fn create_token_account(
    client: &RpcClient,
    payer: &Keypair, // 支付者的公钥
    mint: &Keypair, // mint 账户的公钥
) -> anyhow::Result<(Keypair, Pubkey)> {
    // 创建一个新的密钥对作为 token 账户持有者
    let token_keypair = Keypair::new();
    
    // 先给新账户转一些SOL用于支付租金
    transfer_native_tokens(client, payer, &token_keypair, LAMPORTS_PER_SOL / 100).await?;    

    // 获取关联token账户地址
    let associated_token_account = get_associated_token_address_with_program_id(
        &token_keypair.pubkey(), // 使用token_keypair作为所有者
        &mint.pubkey(),
        &id(),
    );

    // 创建关联token账户
    let create_ata_ix = create_associated_token_account(
        &payer.pubkey(), // 支付者
        &token_keypair.pubkey(), // token账户所有者
        &mint.pubkey(), // mint账户
        &id(),
    );


    // 创建交易 并签名
    let tx = Transaction::new_signed_with_payer(
        &[create_ata_ix],
        Some(&payer.pubkey()),
        &[payer],
        client.get_latest_blockhash().await?,
    );
    // 发送交易
    let signature = client.send_and_confirm_transaction(&tx).await?;
    println!("Token账户创建成功，交易签名: {}", signature);
    println!("关联Token账户地址: {}", associated_token_account);
    
    // 验证账户是否创建成功
    let account_data = client.get_account_data(&associated_token_account).await?;
    if account_data.is_empty() {
        anyhow::bail!("Token账户创建失败");
    }

    Ok((token_keypair, associated_token_account))

    
}


// 如何创建 Mint 帐户
// 要创建 Mint 账户，请调用 初始化 Mint 指令。您可以找到此指令的实现 这里 。

// 创建 mint 账户的交易需要两个说明：

// 调用系统程序为铸币厂账户创建和分配空间，并将所有权转移给代币计划。
// 调用 Token Program 以初始化 mint 账户数据。
async fn create_mint_account(
    client: &RpcClient,
    payer: &Keypair,
    decimals: u8,
) -> anyhow::Result<Keypair> {
    // 创建一个新的密钥对作为 mint 账户
    let mint_keypair = Keypair::new();
    let mint_pubkey = mint_keypair.pubkey();
    println!("Mint 账户公钥: {}", mint_pubkey);
    // 创建 mint 账户的空间
    let mint_account_size = Mint::LEN;
    // 获取租小的余额来创建账户
    let rent = client.get_minimum_balance_for_rent_exemption(mint_account_size).await?;
    // 创建帐号指令
    let create_account_ix = system_instruction::create_account(
        &payer.pubkey(),// 创建账户的公钥
        &mint_pubkey,// mint 账户的公钥
        rent,// 租金
        mint_account_size as u64, // mint 账户的大小
        &spl_token_2022::id(),// 创建程序的id
    );
    // 初始化 mint 账户
    let initialize_mint_ix = initialize_mint(
        &spl_token_2022::id(),// 创建程序的id
        &mint_pubkey,// mint 账户的公钥
        &payer.pubkey(),// mint 账户的拥有者
        Some(&payer.pubkey()),// 冻结账户的公钥
        decimals,// 精度
    )?;
    // 创建交易 并签名
    let tx = Transaction::new_signed_with_payer(
        &[create_account_ix, initialize_mint_ix],
        Some(&payer.pubkey()),
        &[payer, &mint_keypair],
        client.get_latest_blockhash().await?,
    );
    // 发送交易
    let transaction_signature = client.send_and_confirm_transaction(&tx).await?;
    println!("Mint 账户创建成功，交易签名: {}", transaction_signature);
    Ok(mint_keypair)

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

/// 格式化显示账户余额
async fn print_token_balance(
    client: &RpcClient,
    token_account: &Pubkey,
    account_name: &str
) -> anyhow::Result<()> {
    let balance = get_token_account_balance(client, token_account).await?;
    println!("{} 余额: {}", account_name, balance);
    Ok(())
}

async fn create_token_account_with_pda(
    client: &RpcClient,
    payer: &Keypair,
    mint: &Keypair,
    seed: &str,
) -> anyhow::Result<Pubkey> {
    // 1. 计算 PDA 地址
    let (pda, bump) = Pubkey::find_program_address(
        &[
            payer.pubkey().as_ref(),
            mint.pubkey().as_ref(),
            seed.as_bytes(),
        ],
        &id(),
    );

    // 2. 获取所需空间和租金
    let space = spl_token_2022::state::Account::LEN;
    let rent = client.get_minimum_balance_for_rent_exemption(space).await?;

    // 3. 创建账户指令
    let create_account_ix = system_instruction::create_account(
        &payer.pubkey(),
        &pda,
        rent,
        space as u64,
        &id(),
    );

    // 4. 初始化 token 账户指令
    let init_account_ix = initialize_account(
        &id(),
        &pda,
        &mint.pubkey(),
        &payer.pubkey(),
    )?;

    // 5. 创建并发送交易
    let tx = Transaction::new_signed_with_payer(
        &[create_account_ix, init_account_ix],
        Some(&payer.pubkey()),
        &[payer],
        client.get_latest_blockhash().await?,
    );

    let signature = client.send_and_confirm_transaction(&tx).await?;
    println!("Token PDA账户创建成功，交易签名: {}", signature);
    println!("Token PDA地址: {}", pda);

    Ok(pda)
}
