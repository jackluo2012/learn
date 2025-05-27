use anchor_lang::prelude::*;

#[account]
#[derive(InitSpace)]
pub struct Config {
    pub seed: u64,
    pub mint_x: Pubkey,
    pub mint_y: Pubkey,
    pub fee: u16, // 0% => 0, 100% => 10000
    pub locked: bool,
    pub bump: u8, //config bump
    pub mint_lp_bump: u8,
    // pub auth_bump: u8,
    // pub authority: Option<Pubkey>, //In the future we might want to implent a PDA just to undle the signing, all accounts that have confi as authority will pass to this
}
