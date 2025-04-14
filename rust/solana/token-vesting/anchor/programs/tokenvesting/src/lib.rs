#![allow(clippy::result_large_err)] // 允许 Result 类型返回较大的错误类型

// 导入必要的依赖
use anchor_lang::prelude::*;
use anchor_spl::{
    associated_token::AssociatedToken, // 关联代币程序
    token_interface::{
        self, Mint, TokenAccount, // 代币相关接口
        TokenInterface, TransferChecked, // 代币转账接口
    }
};

// 声明程序 ID
declare_id!("BGiHL68abERnzhEGafTTKUtgieTj1yrgqJX2bTnhdih5");

#[program]
pub mod vesting {
    use super::*;

    // 创建代币归属账户的指令
    pub fn create_vestiong_account(
        ctx: Context<CreateVestingAccount>,
        company_name: String, // 公司名称参数
    ) -> Result<()> {
        *ctx.accounts.vesting_account = VestingAccount {
            owner: ctx.accounts.signer.key(), // 设置所有者
            mint: ctx.accounts.mint.key(), // 设置代币铸造地址
            treasury_token_account: ctx.accounts.treasury_token_account.key(), // 设置国库账户
            company_name: company_name, // 设置公司名称
            treasury_bump: ctx.bumps.treasury_token_account, // 设置国库账户的 bump
            bump: ctx.bumps.vesting_account, // 设置归属账户的 bump
        };
        
        Ok(())
    }

    // 创建员工账户的指令
    pub fn create_employee_account(
        ctx: Context<CreateEmployeeAccount>,
        start_time: i64,     // 开始时间   
        end_time: i64,       // 结束时间
        total_amount: i64,   // 总代币数量
        cliff_time: i64,     // 悬崖时间
    ) -> Result<()> {
        *ctx.accounts.employee_account = EmployeeAccount {
            beneficiary: ctx.accounts.owner.key(), // 设置受益人
            vesting_account: ctx.accounts.vesting_account.key(), // 关联的归属账户
            start_time,      // 设置开始时间
            cliff_time,      // 设置悬崖时间
            end_time,        // 设置结束时间
            total_amount,    // 设置总数量
            total_withdraw: 0, // 初始已提取数量为 0
            bump: ctx.bumps.employee_account, // 设置账户的 bump
        };
        Ok(())
    }

    // 员工提取代币的指令
    pub fn claim_tokens(
        ctx: Context<ClaimTokens>,
        company_name: String, // 公司名称
    ) -> Result<()> {
        let employee_account = &mut ctx.accounts.employee_account;        
        let now = Clock::get()?.unix_timestamp; // 获取当前时间

        // 检查是否到达开始时间
        if now < employee_account.start_time {
            return Err(ErrorCode::ClaimNotAvailableYet.into());
        }

        // 计算从开始到现在的时间
        let time_since_start = now - employee_account.start_time;
        // 计算总的归属时间
        let total_vesting_time = employee_account.end_time.saturating_sub(employee_account.start_time);
        
        // 检查时间是否有效
        if time_since_start >= total_vesting_time {
            return Err(ErrorCode::InvalidVestingPeriod.into());
        }

        // 计算已归属的代币数量
        let vested_amount = if now >= employee_account.end_time {
            employee_account.total_amount
        } else {
            match employee_account.total_amount.checked_mul(time_since_start) {
                Some(product) => {
                    product / total_vesting_time
                },
                None => return Err(ErrorCode::CalculationOverflow.into()),
            }
        };
        
        // 计算可提取的数量
        let claimable_amount = vested_amount.saturating_sub(employee_account.total_withdraw);
        
        // 各种检查
        if claimable_amount == 0 {
            return Err(ErrorCode::NotingToClaim.into());
        }
        if claimable_amount > employee_account.total_amount {
            return Err(ErrorCode::TotalAmountWithdrawn.into());
        }
        if now < employee_account.cliff_time {
            return Err(ErrorCode::CliffTimeNotReached.into());
        }
        if now >= employee_account.end_time {
            return Err(ErrorCode::EndTimeReached.into());
        }

        // 构建转账指令
        let cpi_accounts = TransferChecked {
            from: ctx.accounts.treasury_token_account.to_account_info(),
            mint: ctx.accounts.mint.to_account_info(),
            to: ctx.accounts.employee_token_account.to_account_info(),            
            authority: ctx.accounts.treasury_token_account.to_account_info(),
        };
        
        // 获取程序账户信息
        let cpi_program = ctx.accounts.token_program.to_account_info();
        
        // 构建签名种子
        let signer_seeds: &[&[&[u8]]] = &[&[
            b"treasury".as_ref(),
            company_name.as_ref(),
            &[ctx.accounts.vesting_account.treasury_bump],
        ]];

        // 创建 CPI 上下文并执行转账
        let cpi_context = CpiContext::new(cpi_program, cpi_accounts).with_signer(signer_seeds);
        let deciamls = ctx.accounts.mint.decimals;
        token_interface::transfer_checked(cpi_context, claimable_amount as u64, deciamls)?;
        
        // 更新已提取数量
        employee_account.total_withdraw = employee_account
            .total_withdraw
            .saturating_add(claimable_amount);
        Ok(())
    }
}

// 定义提取代币指令的账户结构
#[derive(Accounts)]
#[instruction(company_name: String)]
pub struct ClaimTokens<'info> {
    #[account(mut)]
    pub beneficiary: Signer<'info>, // 受益人（必须签名）

    #[account(
        mut,
        seeds = [b"employee_vesting".as_ref(), beneficiary.key().as_ref(), vesting_account.key().as_ref()],
        bump = employee_account.bump,
        has_one = beneficiary,
        has_one = vesting_account,
    )]
    pub employee_account: Account<'info, EmployeeAccount>, // 员工账户

    #[account(
        mut,
        seeds = [company_name.as_ref()],
        bump = vesting_account.bump,
        has_one = treasury_token_account,
        has_one = mint,
    )]
    pub vesting_account: Account<'info, VestingAccount>, // 归属账户
    
    pub mint: InterfaceAccount<'info, Mint>, // 代币铸造账户
    
    #[account(mut)]
    pub treasury_token_account: InterfaceAccount<'info, TokenAccount>, // 国库代币账户
    
    #[account(
        init_if_needed,
        payer = beneficiary,
        associated_token::mint = mint,
        associated_token::authority = beneficiary,
        associated_token::token_program = token_program,
    )]
    pub employee_token_account: InterfaceAccount<'info, TokenAccount>, // 员工代币账户

    pub token_program: Interface<'info, TokenInterface>, // 代币程序
    pub associated_token_program: Program<'info, AssociatedToken>, // 关联代币程序
    pub system_program: Program<'info, System>, // 系统程序
}

// 定义创建归属账户指令的账户结构
#[derive(Accounts)]
#[instruction(company_name: String)]
pub struct CreateVestingAccount<'info> {
    #[account(mut)]
    pub signer: Signer<'info>, // 创建者签名
    
    #[account(
        init, 
        payer = signer, 
        space = 8 + VestingAccount::INIT_SPACE,
        seeds = [company_name.as_ref()],
        bump,
    )]
    pub vesting_account: Account<'info, VestingAccount>, // 归属账户
    
    pub mint: InterfaceAccount<'info, Mint>, // 代币铸造账户
    
    #[account(
        init,
        payer = signer,
        token::mint = mint,
        token::authority = vesting_account,
        seeds = [b"treasury".as_ref(), company_name.as_ref()],
        bump,
    )]
    pub treasury_token_account: InterfaceAccount<'info, TokenAccount>, // 国库代币账户
    
    pub token_program: Interface<'info, TokenInterface>, // 代币程序
    pub system_program: Program<'info, System>, // 系统程序
}

// 归属账户数据结构
#[account]
#[derive(InitSpace)]
pub struct VestingAccount {
    pub owner: Pubkey,                   // 创建代币的账户
    pub mint: Pubkey,                    // 代币的 mint 地址
    pub treasury_token_account: Pubkey,  // 国库代币账户
    #[max_len(50)]
    pub company_name: String,             // 公司名称
    pub treasury_bump: u8,               // 国库账户的 bump
    pub bump: u8,                        // 归属账户的 bump
}

// 定义创建员工账户指令的账户结构
#[derive(Accounts)]
pub struct CreateEmployeeAccount<'info> {
    #[account(mut)]
    pub owner: Signer<'info>, // 创建者签名
    
    pub beneficiary: SystemAccount<'info>, // 受益人账户
    
    #[account(has_one = owner)]
    pub vesting_account: Account<'info, VestingAccount>, // 归属账户
    
    #[account(
        init,
        payer = owner,
        space = 8 + EmployeeAccount::INIT_SPACE,
        seeds = [b"employee_vesting", beneficiary.key().as_ref(), vesting_account.key().as_ref()],
        bump,
    )]
    pub employee_account: Account<'info, EmployeeAccount>, // 员工账户
    
    pub system_program: Program<'info, System>, // 系统程序
}

// 员工账户数据结构
#[account]
#[derive(InitSpace)]
pub struct EmployeeAccount {
    pub beneficiary: Pubkey,    // 受益人地址
    pub vesting_account: Pubkey, // 关联的归属账户
    pub start_time: i64,        // 开始时间
    pub cliff_time: i64,        // 悬崖时间
    pub end_time: i64,          // 结束时间
    pub total_amount: i64,      // 总代币数量
    pub total_withdraw: i64,    // 已提取的代币数量
    pub bump: u8,               // 账户的 bump
}

// 错误代码枚举
#[error_code]
pub enum ErrorCode {
    #[msg("Claim not available yet")]
    ClaimNotAvailableYet,           // 还未到提取时间
    #[msg("Invalid vesting period")]
    InvalidVestingPeriod,           // 无效的归属期间
    #[msg("The cliff time has not been reached yet")]
    CliffTimeNotReached,            // 未到悬崖时间
    #[msg("Calculation overflow")]
    CalculationOverflow,            // 计算溢出
    #[msg("The end time has been reached")]
    EndTimeReached,                 // 已到结束时间
    #[msg("The total amount has been withdrawn")]
    TotalAmountWithdrawn,           // 已提取全部数量
    #[msg("Nothing to claim")]
    NotingToClaim                   // 没有可提取的代币
}