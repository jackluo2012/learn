use anchor_lang::{prelude::*, system_program::{transfer, Transfer}};
use crate::{SEED_SOL_ACCOUNT, SEED_COLLATERAL_ACCOUNT};
use anchor_spl::{
    token_2022::{burn, Burn}, token_interface::{self, Mint, MintTo, Token2022, TokenAccount, TokenInterface, TransferChecked}
};
// // 这个是用来提取sol的
pub fn withdraw_sol<'info>(
    depositor_key: &Pubkey,
    bump: u8,
    system_program: &Program<'info, System>,
    from:&SystemAccount<'info>,
    to:&AccountInfo<'info>,
    amount: u64,
) -> Result<()> {
    // 我们要将sol转到存款人账户,我们之前定义的pda账户,
    // 我们需要sol账号的签名种子
    let signer_seeds: &[&[&[u8]]] = &[&[
        SEED_SOL_ACCOUNT,
        depositor_key.as_ref(),
        &[bump]
    ]];
    //
    transfer(
        CpiContext::new_with_signer(
            system_program.to_account_info(), 
            Transfer {
                from: from.to_account_info(),
                to: to.to_account_info(),
            },
            signer_seeds), 
            amount,
        )?;
    // 我们需要一个转账的上下文,我们需要一个系统程序的上下文
    Ok(())
}

// 销提取好多抵押,燃烧好多少代币
pub fn burn_tokens<'info>(
    token_program: &Program<'info, Token2022>,
    mint_account: &InterfaceAccount<'info, Mint>,
    token_account: &InterfaceAccount<'info, TokenAccount>,
    authority: &Signer<'info>,
    amount: u64,
) -> Result<()> {
    // 因为我们正在销毁稳定币,这是一个Token2022
    // 因为铸币账户本身就是权威,我们不用使用pda签名,所以不用定义签名种子 
    burn(CpiContext::new(
        token_program.to_account_info(), 
        Burn{
            mint: mint_account.to_account_info(),
            from: token_account.to_account_info(),
            authority:authority.to_account_info(),
        
            },
        ), 
        amount
    )?;
    // 我们需要一个转账的上下文,我们需要一个系统程序的上下文
    Ok(())
}