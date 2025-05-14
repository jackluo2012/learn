use anchor_lang::prelude::*;
use instructions::*;
use state::game::Square;

pub mod errors;
pub mod instructions;
pub mod state;


declare_id!("CWrQhPHDgwYrm7h3twob8tVmbbf48uiyKvixc26Dkx7V");

#[program]
pub mod quick_tac_toe {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        msg!("Greetings from: {:?}", ctx.program_id);
        Ok(())
    }
    // 初始化游戏 
    pub fn init(ctx: Context<Init>) -> Result<()> {
        init(ctx)
    }
    // 创建新玩家
    pub fn create_player(ctx: Context<CreatePlayer>) -> Result<()> {
        create_player(ctx)
    }
    // 创建新游戏
    pub fn create_game(ctx: Context<CreateGame>,  game_id: u64) -> Result<()> {
        create_game(ctx, game_id)
    }
    // 加入游戏
    pub fn join_game(ctx: Context<JoinGame>) -> Result<()> {
        join_game(ctx)
    }
    // 玩
    pub fn play(ctx: Context<Play>, square: Square) -> Result<()> {
        play(ctx, square)
    }
    // 领取奖励
    pub fn claim_reward(ctx: Context<ClaimReward>) -> Result<()> {
        claim_reward(ctx)
    }
}

#[derive(Accounts)]
pub struct Initialize {}
