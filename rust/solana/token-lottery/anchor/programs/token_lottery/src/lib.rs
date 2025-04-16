#![allow(clippy::result_large_err)]

use anchor_lang::{
    prelude::*,
    system_program,    
};
use anchor_spl::{
    associated_token::AssociatedToken, 
    
    metadata::{
        create_master_edition_v3, create_metadata_accounts_v3, mpl_token_metadata::types::{CollectionDetails, Creator, DataV2}, set_and_verify_sized_collection_item, sign_metadata, CreateMasterEditionV3, CreateMetadataAccountsV3, Metadata, MetadataAccount, SetAndVerifySizedCollectionItem, SignMetadata
    },
    
    token_interface::{mint_to, Mint, MintTo, TokenAccount, TokenInterface}
};
use switchboard_on_demand::accounts::RandomnessAccountData;

declare_id!("3CTrgdWWrzHE7Gr1Gx7yEzrEhbiQofFgtemM1N48jayt");

// 定义 常量 
#[constant]
pub const NAME:&str = "Token Lottery Ticket #";
#[constant]
pub const SYMBOL:&str = "TLT";
#[constant]
pub const URI:&str = "https://github.com/solana-developers/developer-bootcamp-2024/blob/anchor-31/project-9-token-lottery/metadata.json";
#[program]
pub mod token_lottery {
    

    use super::*;

    pub fn initialize_config(ctx: Context<InitializeConfig>,start:u64,end:u64) -> Result<()> {
        ctx.accounts.token_lottery.bump = ctx.bumps.token_lottery;
        ctx.accounts.token_lottery.start_time = start;
        ctx.accounts.token_lottery.end_time = end;
        ctx.accounts.token_lottery.authority = ctx.accounts.payer.key();
        ctx.accounts.token_lottery.randomness_account = Pubkey::default();
        ctx.accounts.token_lottery.winner_chosen = false;
        ctx.accounts.token_lottery.winner = 0;
        Ok(())
    }

    pub fn initialize_lottery(ctx:Context<InitializeLottery>) -> Result<()> {
        //  我们要用cpi 签名种子
        let signer_seeds:&[&[&[u8]]] = &[&[
        &b"collection_mint".as_ref(),
        &[ctx.bumps.collection_mint]]];
        msg!("创建 mint 帐号");
        
        mint_to(
            CpiContext::new_with_signer(
               ctx.accounts.token_program.to_account_info(),
               MintTo{
                    mint: ctx.accounts.collection_mint.to_account_info(),
                    to: ctx.accounts.collection_token_account.to_account_info(),
                    authority: ctx.accounts.collection_mint.to_account_info(),
               },
               signer_seeds,               
            ),
            1, //铸造1个代币
        )?;
        msg!("创建 token 元数据");
        create_metadata_accounts_v3(CpiContext::new_with_signer(
            ctx.accounts.token_metadata_program.to_account_info(), 
            CreateMetadataAccountsV3{
                metadata: ctx.accounts.metadata.to_account_info(),
                mint: ctx.accounts.collection_mint.to_account_info(),
                mint_authority: ctx.accounts.collection_mint.to_account_info(),
                payer: ctx.accounts.payer.to_account_info(),
                update_authority: ctx.accounts.collection_mint.to_account_info(),
                system_program: ctx.accounts.system_program.to_account_info(),
                rent: ctx.accounts.rent.to_account_info(),
            }, &signer_seeds),
         DataV2{
            name: NAME.to_string(),
            symbol: SYMBOL.to_string(),
            uri: URI.to_string(),
            seller_fee_basis_points: 0,
            // 创建者 分配利润
            creators: Some(vec![Creator{
                address: ctx.accounts.collection_mint.key(),
                verified: false,
                share: 100,
            }]),
            collection: None,
            uses: None,
         }, true, true, Some(CollectionDetails::V1 { size: 0 }))?;

         msg!("创建 主版本 帐号");
         create_master_edition_v3(
            CpiContext::new_with_signer(
                ctx.accounts.token_metadata_program.to_account_info(), 
                CreateMasterEditionV3{
                    payer: ctx.accounts.payer.to_account_info(),
                    mint: ctx.accounts.collection_mint.to_account_info(),
                    edition: ctx.accounts.master_edition.to_account_info(),
                    mint_authority: ctx.accounts.collection_mint.to_account_info(),
                    update_authority: ctx.accounts.collection_mint.to_account_info(),
                    metadata: ctx.accounts.metadata.to_account_info(),
                    token_program: ctx.accounts.token_program.to_account_info(),
                    system_program: ctx.accounts.system_program.to_account_info(),
                    rent: ctx.accounts.rent.to_account_info(),
                }, 
                &signer_seeds), 
                Some(0))?;
        msg!("验证合集");
        sign_metadata(
            CpiContext::new_with_signer(
                ctx.accounts.token_metadata_program.to_account_info(),
                SignMetadata {
                    metadata: ctx.accounts.metadata.to_account_info(),
                    creator: ctx.accounts.collection_mint.to_account_info(),
                },

                signer_seeds)
            )?;

        Ok(())
    }
      
    pub fn buy_ticket(ctx:Context<BuyTicket>) -> Result<()> {

        let clock = Clock::get()?;
        let ticket_name = NAME.to_owned() + 
                                ctx.accounts.token_lottery.total_tickets.to_string().as_str();
        //如果当前时间小于
        if clock.slot < ctx.accounts.token_lottery.start_time || 
        clock.slot > ctx.accounts.token_lottery.end_time {
            return Err(ErrorCode::LotteryNotOpen.into());
        }
        // 拿钱买票
        system_program::transfer(
            CpiContext::new(
                ctx.accounts.system_program.to_account_info(),
                system_program::Transfer {
                    from: ctx.accounts.payer.to_account_info(),
                    //买票就是往这个账户里存钱
                    to: ctx.accounts.token_lottery.to_account_info(),
                    
                },
            ),
            ctx.accounts.token_lottery.ticket_price,
        )?;
        let signer_seeds:&[&[&[u8]]] = &[&[
            &b"collection_mint".as_ref(),
            &[ctx.bumps.collection_mint]]];

        msg!("创建 token 币");
        mint_to(
            CpiContext::new_with_signer(
                ctx.accounts.token_program.to_account_info(), 
                MintTo { 
                    mint: ctx.accounts.ticket_mint.to_account_info(), 
                    to: ctx.accounts.destination.to_account_info(), 
                    authority: ctx.accounts.collection_mint.to_account_info(), 
                }, 
                &signer_seeds
            ), 
            1,// 铸造 1 个代币
        )?;
        msg!("创建 token 元数据");
        create_metadata_accounts_v3(CpiContext::new_with_signer(
            ctx.accounts.token_metadata_program.to_account_info(), 
            CreateMetadataAccountsV3{
                metadata: ctx.accounts.ticket_metadata.to_account_info(),
                mint: ctx.accounts.ticket_mint.to_account_info(),
                mint_authority: ctx.accounts.collection_mint.to_account_info(),
                payer: ctx.accounts.payer.to_account_info(),
                update_authority: ctx.accounts.collection_mint.to_account_info(),
                system_program: ctx.accounts.system_program.to_account_info(),
                rent: ctx.accounts.rent.to_account_info(),
            }, &signer_seeds),
         DataV2{
            name: ticket_name,
            symbol: SYMBOL.to_string(),
            uri: URI.to_string(),
            seller_fee_basis_points: 0,
            // 创建者 分配利润
            creators: None,
            collection: None,
            uses: None,
         }, 
         true, 
         true, 
         None)?;

         msg!("创建 主版本 帐号");
         create_master_edition_v3(
            CpiContext::new_with_signer(
                ctx.accounts.token_metadata_program.to_account_info(), 
                CreateMasterEditionV3{
                    payer: ctx.accounts.payer.to_account_info(),
                    mint: ctx.accounts.ticket_mint.to_account_info(),
                    edition: ctx.accounts.ticket_master_edition.to_account_info(),
                    mint_authority: ctx.accounts.collection_mint.to_account_info(),
                    update_authority: ctx.accounts.collection_mint.to_account_info(),
                    metadata: ctx.accounts.ticket_metadata.to_account_info(),
                    token_program: ctx.accounts.token_program.to_account_info(),
                    system_program: ctx.accounts.system_program.to_account_info(),
                    rent: ctx.accounts.rent.to_account_info(),
                }, 
                &signer_seeds), 
                Some(0))?;
        msg!("验证合集");
        set_and_verify_sized_collection_item(
            CpiContext::new_with_signer(
                ctx.accounts.token_metadata_program.to_account_info(),
                SetAndVerifySizedCollectionItem {
                    metadata:ctx.accounts.ticket_metadata.to_account_info(),
                    collection_authority: ctx.accounts.collection_mint.to_account_info(),
                    payer: ctx.accounts.payer.to_account_info(),
                    update_authority: ctx.accounts.collection_mint.to_account_info(),
                    collection_mint:ctx.accounts.collection_mint.to_account_info(),
                    collection_metadata: ctx.accounts.collection_metadata.to_account_info(),
                    collection_master_edition: ctx.accounts.collection_master_edition.to_account_info(),
                    
                },
                &signer_seeds
            ), 
            None
        )?;
        ctx.accounts.token_lottery.total_tickets += 1;
        Ok(())
    }
    pub fn commit_randomness(ctx:Context<CommitRandomness>)->Result<()>{
        let clock = Clock::get()?;
        let token_lottery = &mut ctx.accounts.token_lottery;

        if ctx.accounts.payer.key() != token_lottery.authority {
            return Err(ErrorCode::NotAuthorized.into());
        }
        // 检查随机数，是不是我们想要的
        let randomness_data= RandomnessAccountData::parse(ctx.accounts.randomness_account.data.borrow()).unwrap();

        if randomness_data.seed_slot != clock.slot -1 {
            return Err(ErrorCode::RandomnessAlreadyRevealed.into());
        }
        // 提交随机数
        token_lottery.randomness_account = ctx.accounts.randomness_account.key();
        
        Ok(())
    }
    
    pub fn reveal_winner(ctx:Context<RevealWinner>)->Result<()>{
        let clock = Clock::get()?;
        // 让代币抽奖
        let token_lottery = &mut ctx.accounts.token_lottery;
        
        if ctx.accounts.payer.key() != token_lottery.authority {
            return Err(ErrorCode::NotAuthorized.into());
        }
        
        if ctx.accounts.randomness_account.key() != token_lottery.randomness_account {
            return Err(ErrorCode::RandomnessNotCommitted.into());
        }

        if clock.slot < token_lottery.end_time {
            return Err(ErrorCode::LotteryNotEnded.into());
        }

        require!(!token_lottery.winner_chosen, ErrorCode::WinnerChosen);
        let randomness_data= RandomnessAccountData::parse(
            ctx.accounts.randomness_account.data.borrow()
        ).unwrap();

        let reveal_random_values = randomness_data
        .get_value(&clock)
        .map_err(|_| ErrorCode::RandomnessNotResolved)?;

        if reveal_random_values.len() == 0 {
            return Err(ErrorCode::RandomnessNotReady.into());
        }

        let winner = reveal_random_values[0] as u64 % token_lottery.total_tickets;

        // 打印获胜者信息
        msg!(" Winner  chose: {}", winner);

        token_lottery.winner = winner;
        token_lottery.winner_chosen = true;

        Ok(())
    }
    
    pub fn claim_winnings(ctx:Context<ClaimWinnings>)->Result<()>{
        // 领奖时彩票中奖者是否已经选择
        require!(ctx.accounts.token_lottery.winner_chosen, ErrorCode::WinnerNotChosen);
        
        // 确保已经验证过了集合 collection_mint
        require!(ctx.accounts.ticket_metadata.collection.as_ref().unwrap().verified, ErrorCode::CollectionNotVerified);
        // 是我们集合的一部份
        require!(ctx.accounts.ticket_metadata.collection.as_ref().unwrap().key == ctx.accounts.collection_mint.key(), ErrorCode::IncorrectCollection);

        let ticket_name =  NAME.to_owned() + &ctx.accounts.token_lottery.winner.to_string();
        
        let metadata_name = ctx.accounts.ticket_metadata.name.replace("\u{0}", "");

        require!(metadata_name == ticket_name, ErrorCode::IncorrectTicket);

        require!(ctx.accounts.ticket_account.amount >0,ErrorCode::NoTickets);
        // 减去池底的奖池
        **ctx.accounts.token_lottery.to_account_info().lamports.borrow_mut() -= ctx.accounts.token_lottery.lottery_pot_amount;
        **ctx.accounts.payer.to_account_info().lamports.borrow_mut() += ctx.accounts.token_lottery.lottery_pot_amount;

        ctx.accounts.token_lottery.lottery_pot_amount = 0;

        Ok(())
    }
}

#[derive(Accounts)]
pub struct InitializeConfig<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,

    #[account(
      init,
      space = 8+ Tokenlottery::INIT_SPACE,
      payer = payer,
      seeds = [b"token_lottery".as_ref()],
      bump
  )]
    pub token_lottery: Account<'info, Tokenlottery>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct InitializeLottery<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,

    #[account(
        init,
        payer = payer,
        mint::decimals = 0,
        mint::authority = collection_mint,
        mint::freeze_authority = collection_mint,
        seeds = [b"collection_mint".as_ref()],
        bump
    )]
    pub collection_mint: InterfaceAccount<'info, Mint>,
    
    #[account(
        init,
        payer = payer,
        token::mint = collection_mint,
        token::authority = collection_token_account,
        seeds = [b"collection_token_account".as_ref()],
        bump
    )]
    pub collection_token_account: InterfaceAccount<'info, TokenAccount>,
    
    /// CHECK: This account is checked by the token metadata program.
    #[account(
        mut,
        seeds = [
            b"metadata", 
            token_metadata_program.key().as_ref(), 
            collection_mint.key().as_ref()
        ],
        bump,
        seeds::program = token_metadata_program.key(),
    )]
    pub metadata: UncheckedAccount<'info>,
    
    /// CHECK: This account is checked by the token metadata program.
    #[account(
        mut,
        seeds = [
            b"metadata".as_ref(), 
            token_metadata_program.key().as_ref(), 
            collection_mint.key().as_ref(),
            b"edition".as_ref(),
        ],
        bump,
        seeds::program = token_metadata_program,
    )]
    pub master_edition: UncheckedAccount<'info>,

    
    pub token_metadata_program: Program<'info, Metadata>,
    pub associate_token_program: Program<'info, AssociatedToken>,
    pub token_program: Interface<'info, TokenInterface>,
    pub system_program: Program<'info, System>,
    pub rent: Sysvar<'info, Rent>,
   
}

#[derive(Accounts)]
pub struct BuyTicket<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,
    #[account(
        mut,
        seeds = [b"token_lottery".as_ref()],
        bump = token_lottery.bump,
    )]
    pub token_lottery: Account<'info, Tokenlottery>,
    
    // 需要一个mint 来mnit 这张彩票
    #[account(
        mut,
        seeds = [token_lottery.total_tickets.to_le_bytes().as_ref()],// 票数
        bump,
        mint::decimals = 0,
        mint::authority = collection_mint,
        mint::freeze_authority = collection_mint,
        mint::token_program = token_program,
    )]
    pub ticket_mint: InterfaceAccount<'info, Mint>,
    //存储元数据
    #[account(
        mut,
        seeds = [
            b"metadata", 
            token_metadata_program.key().as_ref(), 
            ticket_mint.key().as_ref()
        ],
        bump,
        seeds::program = token_metadata_program.key()
    )]
    /// CHECK: This account is checked by the token metadata program.
    pub ticket_metadata: UncheckedAccount<'info>,
    #[account(
        mut,
        seeds = [
            b"metadata", 
            token_metadata_program.key().as_ref(), 
            collection_mint.key().as_ref()
        ],
        bump,
        seeds::program = token_metadata_program.key()
    )]
    /// CHECK: This account is checked by the token metadata program.
    pub collection_metadata: UncheckedAccount<'info>,
    /// CHECK: This account is checked by the token metadata program.
    #[account(
        mut,
        seeds = [
            b"metadata".as_ref(), 
            token_metadata_program.key().as_ref(), 
            collection_mint.key().as_ref(),
            b"edition".as_ref(),
        ],
        bump,
        seeds::program = token_metadata_program.key(),
    )]
    pub collection_master_edition: UncheckedAccount<'info>,
    /// CHECK: This account is checked by the token metadata program.
    #[account(
        mut,
        seeds = [
            b"metadata".as_ref(), 
            token_metadata_program.key().as_ref(), 
            ticket_mint.key().as_ref(),
            b"edition".as_ref(),
        ],
        bump,
        seeds::program = token_metadata_program.key(),
    )]
    pub ticket_master_edition: UncheckedAccount<'info>,
    // 需要一个代币帐号来买票
    #[account(
        init,
        payer = payer,
        associated_token::mint = ticket_mint,
        associated_token::authority = payer,
        associated_token::token_program = token_program,
    )]
    pub destination: InterfaceAccount<'info, TokenAccount>,

    #[account(
        mut,
        seeds = [b"collection_mint".as_ref()],
        bump,        
    )]
    pub collection_mint: InterfaceAccount<'info, Mint>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub token_metadata_program: Program<'info, Metadata>,
    pub token_program: Interface<'info, TokenInterface>,
    pub system_program: Program<'info, System>,
    // rent 帐户需要租金
    pub rent: Sysvar<'info, Rent>,
}

#[derive(Accounts)]
pub struct CommitRandomness<'info> {    
    #[account(mut)]
    pub payer: Signer<'info>,

    #[account(
        mut,
        seeds = [b"token_lottery".as_ref()],
        bump = token_lottery.bump,
    )]
    pub token_lottery: Account<'info, Tokenlottery>,
    //随机数的帐户
    /// CHECK: This account is checked by the Switchboard smart contract.
    pub randomness_account: UncheckedAccount<'info>, 

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct RevealWinner<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,
    // 这个是我们的彩票
    #[account(
        mut,
        seeds = [b"token_lottery".as_ref()],
        bump = token_lottery.bump,
    )]
    pub token_lottery: Account<'info, Tokenlottery>,
    // 随机数的帐户
    /// CHECK: This account is checked by the Switchboard smart contract.
    pub randomness_account: UncheckedAccount<'info>,

}

#[account]
#[derive(InitSpace)]
pub struct Tokenlottery {
    pub  bump: u8,
    pub winner: u64,
    pub winner_chosen: bool,
    pub start_time: u64,
    pub end_time: u64,
    pub lottery_pot_amount: u64,// 奖池金额
    pub total_tickets: u64,// 总票数
    pub ticket_price: u64, // 票价
    pub authority: Pubkey,// 管理员
    pub randomness_account: Pubkey,// 随机性账户
}
#[derive(Accounts)]
pub struct ClaimWinnings<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,

    #[account(
        mut,
        seeds = [b"token_lottery".as_ref()],
        bump = token_lottery.bump,
    )]
    pub token_lottery: Account<'info, Tokenlottery>,

    #[account(
        mut,
        seeds = [token_lottery.winner.to_le_bytes().as_ref()],
        bump,
    )]
    pub ticket_mint: InterfaceAccount<'info, Mint>,

    #[account(
        mut,
        seeds = [b"collection_mint".as_ref()],
        bump,
    )]
    pub collection_mint: InterfaceAccount<'info, Mint>,

    #[account(
        mut,
        seeds = [
            b"metadata",
            token_metadata_program.key().as_ref(),
            ticket_mint.key().as_ref()
        ],
        bump,
        seeds::program = token_metadata_program.key(),
    )]
    pub ticket_metadata: Account<'info, MetadataAccount>,

    #[account(
        associated_token::mint = ticket_mint,
        associated_token::authority = payer,
        associated_token::token_program = token_program,
    )]
    pub ticket_account: InterfaceAccount<'info, TokenAccount>,

    #[account(
        mut,
        seeds = [
            b"metadata",
            token_metadata_program.key().as_ref(),
            collection_mint.key().as_ref()
        ],
        bump,
        seeds::program = token_metadata_program.key(),
    )]
    pub collection_metadata: Account<'info, MetadataAccount>,

    pub token_metadata_program: Program<'info, Metadata>,
    pub token_program: Interface<'info, TokenInterface>,
}

#[derive(Accounts)]
pub struct InitializeTokenlottery<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,

    #[account(
  init,
  space = 8 + Tokenlottery::INIT_SPACE,
  payer = payer
  )]
    pub tokenlottery: Account<'info, Tokenlottery>,
    pub system_program: Program<'info, System>,
}
#[error_code]
pub enum ErrorCode {
    #[msg("彩票还没有开放")]
    LotteryNotOpen,
    #[msg("没有权限")]
    NotAuthorized,
    #[msg("随机性已经透露")]
    RandomnessAlreadyRevealed,
    #[msg("赢家已经选择")]
    WinnerChosen,
    #[msg("随机性没有被揭开")]
    RandomnessNotResolved,
    #[msg("没有准备好随机性")]
    RandomnessNotReady,
    #[msg("随机性没有提交")]
    RandomnessNotCommitted,
    #[msg("抽奖还没有结束")]
    LotteryNotEnded,
    #[msg("彩票还没有选中中奖人")]
    WinnerNotChosen,
    #[msg("彩票没有验证通过")]
    CollectionNotVerified,
    #[msg("错误的彩票")]
    IncorrectCollection,
    #[msg("彩票不正确")]
    IncorrectTicket,
    #[msg("没有彩票")]
    NoTickets,
}