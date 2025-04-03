// # 创建 代币转帐功能 
// 将tokens 写入信息，
// 关于这个人想要什么，换取什么代币，还有一些指令处理程序 
// 从金库中取出代币 并发送他们的代币 直接给提出 报价的人
use anchor_lang::prelude::*;
use anchor_spl::token_interface::{transfer_checked,Mint, TokenAccount, TransferChecked,TokenInterface};
pub fn transfer_tokens<'info>(
    from:&InterfaceAccount<'info,TokenAccount>,
    to:&InterfaceAccount<'info,TokenAccount>,
    amount:u64,
    mint:&InterfaceAccount<'info,Mint>,
    authority:&Signer<'info>,
    token_program:&Interface<'info,TokenInterface>,

) -> Result<()> {
    let transfer_accounts_options = TransferChecked{
        from:from.to_account_info(),
        to:to.to_account_info(),
        authority:authority.to_account_info(),
        mint:mint.to_account_info(),
    };
    let cpi_context 
                            =CpiContext::new(
                                token_program.to_account_info(),
                            transfer_accounts_options);
    transfer_checked(cpi_context, amount, 0)
    // msg!("Transfer {} token from {} to {}", amount, from.key(), to.key());

    // Ok(())
}