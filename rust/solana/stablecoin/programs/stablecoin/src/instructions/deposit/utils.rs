use anchor_lang::prelude::*;
use anchor_lang::system_program::{transfer, Transfer};
use anchor_spl::{token_2022::{mint_to,MintTo,Token2022},token_interface::{Mint, TokenAccount}};

use crate::{SEED_MINT_ACCOUNT,
    SEED_COLLATERAL_ACCOUNT,
    SEED_SOL_ACCOUNT,
    Collateral, Config, MINT_DECIMALS
};

// 铸造代币
// 现在当我们铸造代币时，它来自铸币账户
// 我们创建 Mint账户的时候 ,它有一个PDA
// 所以我们实际上必须 在这里使用签名种子 
//  能够签署CPI
pub fn mint_tokens<'info> (
    mint_account:&InterfaceAccount<'info, Mint>,
    token_account:&InterfaceAccount<'info, TokenAccount>,
    token_program: &Program<'info, Token2022>,
    amount:u64,
    bump:u8
) -> Result<()> {

    let signer_seeds: &[&[&[u8]]] = &[&[SEED_MINT_ACCOUNT, &[bump]]];
    
    mint_to(
        CpiContext::new_with_signer(
            token_program.to_account_info(),
            MintTo {
                // 从铸币账户 铸造代币 到用户令牌账户,这是他们相关联的代币账户
                mint: mint_account.to_account_info(),
                to: token_account.to_account_info(),
                authority: mint_account.to_account_info(),
            },
            signer_seeds,
        ),
        amount,
    )
}
// 存入 sol
// 我们不会铸造和销销毁代币，我们只是存入sol
//  从sol 账户转账，从一个账户到另一个账户

// 这是一个系统程序
pub fn deposit_sol<'info>(
    from :&Signer<'info>,
    to:&SystemAccount<'info>,    
    system_program:&Program<'info, System>,
    amount:u64
) -> Result<()> {
    // 转帐这里不是pda账户
    // 我们不需要适配器,所以我们就用new
    // 因为我只是在转账sol，所以它是一个系统程序
    transfer(
        CpiContext::new(system_program.to_account_info(), 
        Transfer { 
            from: from.to_account_info(),
            to: to.to_account_info(),
        },
        ), amount)
}
