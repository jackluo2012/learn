use bip39::{
    Mnemonic,
    Language,
};
use solana_sdk::{
    pubkey::Pubkey,
    signature::{Keypair, Signer},
};
use bs58;
use anyhow::{Ok, Result};
use std::str::FromStr;

fn main() -> Result<()> {
    // # 如何创建密钥对
    let keypair_bytes:[u8; 64];
    let address:Pubkey;
    let keypair_base58:String;
    let mnemonic_str:String;
    println!("创建密钥对");
    {
        let keypair = Keypair::new();
        address = keypair.pubkey();
        keypair_bytes = keypair.to_bytes();
        println!("创建的地址: {},", address);
        println!("创建的密钥: {:?}", keypair.to_base58_string());
        println!("创建的密钥对: {:?}", keypair_bytes);
        
//      Address: EowyBLQ9co6RBz7qUvKpD73ztgZyUi9YE9MTE3GgKLDn,
//      Secret Key: [224, 129, 172, 48, 78, 2, 24, 102, 31, 227, 141, 117, 122, 180, 125, 13, 137, 235, 69, 99, 234, 246, 24, 68, 127, 250, 4, 77, 186, 60, 246, 226, 205, 46, 204, 233, 198, 99, 195, 90, 154, 87, 163, 191, 137, 161, 45, 194, 146, 47, 68, 26, 37, 39, 0, 121, 93, 85, 232, 49, 227, 197, 196, 49]
//      Public Key: [205, 46, 204, 233, 198, 99, 195, 90, 154, 87, 163, 191, 137, 161, 45, 194, 146, 47, 68, 26, 37, 39, 0, 121, 93, 85, 232, 49, 227, 197, 196, 49]
//      Secret Key: SecretKey: [224, 129, 172, 48, 78, 2, 24, 102, 31, 227, 141, 117, 122, 180, 125, 13, 137, 235, 69, 99, 234, 246, 24, 68, 127, 250, 4, 77, 186, 60, 246, 226]
    
    }
    // 如何恢复密钥对或签名者
    println!("通过字节数组恢复密钥对或签名者");
    {
        // let keypair_bytes  = [224, 129, 172, 48, 78, 2, 24, 102, 31, 227, 141, 117, 122, 
        // 180, 125, 13, 137, 235, 69, 99, 234, 246, 24, 68, 127, 250, 4, 77, 186, 60, 
        // 246, 226, 205, 46, 204, 233, 198, 99, 195, 90, 154, 87, 163, 191, 137, 161, 
        // 45, 194, 146, 47, 68, 26, 37, 39, 0, 121, 93, 85, 232, 49, 227, 197, 196, 49];
        let keypair = Keypair::from_bytes(&keypair_bytes)?;
        keypair_base58 = keypair.to_base58_string();
        println!("通keypair字节数组恢复的密钥: {:?}", keypair_base58);
        let address = keypair.pubkey();  
        println!("通keypair字节数组恢复的地址是: {:?}", address);      
    }
    println!("从Base58编码恢复密钥对或签名者");
    // 从Base58编码恢复密钥对或签名者
    {
        // let keypair_base58 =        "5VLfe3gZwzS5y8i4xjUakXkctPx8SwuxDKTVE6HZJUnPXG3hXHDrEW6W2n37Jq4AX3Be3F3nSpoBizAs6oxdeRiY";
        let keypair_bytes = bs58::decode(keypair_base58).into_vec()?;
        let keypair = Keypair::from_bytes(&keypair_bytes)?;
        println!("从 Base58 字符串恢复地址: {:?}", keypair.pubkey());

    }
    println!("验证密码对");
    {
        let keypair = Keypair::from_bytes(&keypair_bytes)?;
        let pubkey = Pubkey::from_str(&address.to_string())?; // 使用 Pubkey::from_str

        println!("验证密钥是否和公钥一致{}", keypair.pubkey().eq(&pubkey));
    }

    // 如何验证公钥
    println!("在某些特殊情况下（例如程序派生地址），公钥可能没有与之关联的私钥。您可以通过查看公钥是否位于 ed25519 曲线上来检查这一点。只有位于曲线上的公钥才能由拥有钱包的用户控制。");
    {
        println!("生成程序 派生地址:{}",address.is_on_curve());

    }

    println!("如何为 Keypairs 生成助记词");
    {
        let entropy = [0u8; 16]; // Example: 16 bytes of entropy
        let mnemonic = Mnemonic::from_entropy_in(Language::English, &entropy)?;
        mnemonic_str = mnemonic.to_string();
        println!("助记词: {}", mnemonic_str);
    }
    println!("如何从助记词恢复 Keypairs");
    {
        let mnemonic = Mnemonic::parse_in (Language::English, &mnemonic_str)?; // 使用 parse_in_normalized
        let seed = mnemonic.to_seed(""); // 生成种子
        let keypair = Keypair::from_bytes(&seed[..64])?; // 使用 Keypair::from_seed 方法
        println!("恢复的地址: {}", keypair.pubkey());
    }

    Ok(())
}
