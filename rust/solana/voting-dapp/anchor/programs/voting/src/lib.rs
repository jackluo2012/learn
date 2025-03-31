#![allow(clippy::result_large_err)]

use anchor_lang::prelude::{borsh::de, *};

declare_id!("coUnmi3oBUtwtd9fjeAvSsJssXh5A5xyPbhpewyzRVF");

#[program]
pub mod voting {
    use super::*;

    // 初始化投票
    pub fn initialize_poll(
        ctx: Context<InitializePoll>,
        poll_id: u64,
        description: String,
        poll_start: i64,
        poll_end: i64,
    ) -> Result<()> {
      let poll = &mut ctx.accounts.poll;
      poll.poll_id = poll_id;
      poll.description = description;
      poll.poll_start = poll_start;
      poll.poll_end = poll_end;
      poll.candidate_amount = 0;
      Ok(())
    }
    // 初始化候选人
    pub fn initialize_candidate(
        ctx: Context<InitializeCandidate>,        
        candidate_name: String,
        poll_id: u64,
    ) -> Result<()> {
        let candidate = &mut ctx.accounts.candidate;
        
        let poll = &mut ctx.accounts.poll;//
        poll.candidate_amount += 1;// 增加候选人数量

        candidate.candidate_name = candidate_name;
        candidate.candidate_votes = 0;
      Ok(())
    }

    // 投票
    pub fn vote(
        ctx: Context<Vote>,
        poll_id: u64,
        candidate_name: String,
    ) -> Result<()> {
        let candidate  = &mut ctx.accounts.candidate;
        candidate.candidate_votes += 1; // 增加候选人的投票数量
    
        msg!("投票给了候选人: {}", candidate.candidate_name);
        msg!("候选人 {} 的投票数量: {}", candidate.candidate_name, candidate.candidate_votes);
        msg!("投票给了投票: {}", ctx.accounts.poll.description);

      Ok(())
    }

}
#[derive(Accounts)]
#[instruction(poll_id: u64, candidate_name: String)]
pub struct Vote<'info>{
    #[account()]
    pub signer: Signer<'info>,
    #[account(
        seeds = [poll_id. to_le_bytes().as_ref()], // 通过 poll_id 生成种子
        bump
    )]
    pub poll: Account<'info, Poll>,// 投票的账户

    #[account(
            seeds = [poll_id. to_le_bytes().as_ref(),candidate_name.as_bytes()], // 通过 poll_id 生成种子
            bump
    )]
    pub candidate: Account<'info, Candidate>,
    // 因为要创建一个新的账户，所以需要系统程序
    pub system_program: Program<'info, System>, // 添加 system_program 字段
}


#[derive(Accounts)]
#[instruction(candidate_name:String, poll_id: u64)]
struct InitializeCandidate<'info> {
    #[account(mut)]
    pub signer: Signer<'info>,
    #[account(
        seeds = [poll_id. to_le_bytes().as_ref()], // 通过 poll_id 生成种子
        bump
    )]
    pub poll: Account<'info, Poll>,// 投票的账户

    #[account(init, 
              payer = signer, // 由 signer 账户支付交易费用
              space = 8 + Candidate::INIT_SPACE,
              seeds = [poll_id. to_le_bytes().as_ref(),candidate_name.as_bytes()], // 通过 poll_id 生成种子
             bump
    )]
    pub candidate: Account<'info, Candidate>,
    // 因为要创建一个新的账户，所以需要系统程序
    pub system_program: Program<'info, System>, // 添加 system_program 字段
}
#[account]
#[derive(InitSpace)] // 自动计算空间大小
pub struct Candidate {
    #[max_len(32)]
    pub candidate_name: String, // 候选人的名字
    pub candidate_votes: u64, // 候选人的投票数量
}

/// 初始化投票
/// 1. `signer` 是投票的发起者
/// 2. `poll` 是投票的账户
/// 3. `payer` 是支付交易费用的账户
#[derive(Accounts)]
#[instruction(poll_id: u64)]
pub struct InitializePoll<'info> {
    #[account(mut)]
    pub signer: Signer<'info>,
    #[account(init, 
              payer = signer, // 由 signer 账户支付交易费用
              space = 8 + Poll::INIT_SPACE,
              seeds = [poll_id. to_le_bytes().as_ref()], // 通过 poll_id 生成种子
              bump
    )]
    pub poll: Account<'info, Poll>,
    // 因为要创建一个新的账户，所以需要系统程序
    pub system_program: Program<'info, System>, // 添加 system_program 字段   
}

#[account]
#[derive(InitSpace)] // 自动计算空间大小
pub struct Poll {
    pub poll_id: u64, //投票的id
    #[max_len(280)]
    pub description: String, // 投票的描述
    pub poll_start: i64, // 投票开始时间
    pub poll_end: i64, // 投票结束时间
    pub candidate_amount: u64,// 投票的候选人数量
}
