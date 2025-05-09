use anchor_lang::prelude::*;
use mpl_core::{
    ID as MPL_CORE_ID,
    accounts::BaseCollectionV1, 
    instructions::CreateV2CpiBuilder, 
};

// 导入额外的插件
use mpl_core::types::{
    Plugin, FreezeDelegate, PluginAuthority,
    ExternalPluginAdapterInitInfo, AppDataInitInfo, 
    ExternalPluginAdapterSchema
};

declare_id!("CQehoB8sTthDQnN9ebttbPzFnxdp7NhdDBp93hbkCaSs");

#[derive(AnchorDeserialize, AnchorSerialize)]
pub struct CreateAssetArgs {
    name: String,
    uri: String,
}

#[program]
pub mod create_core_asset_example {
    use mpl_core::{collection, types::{AppData, PluginAuthorityPair}};

    use super::*;

    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        msg!("Greetings from: {:?}", ctx.program_id);
        Ok(())
    }

    pub fn create_core_asset(ctx: Context<CreateAsset>, args: CreateAssetArgs)->Result<()> {
        let collection = Some(ctx.accounts.collection.to_account_info());
        
        let authrity = match &ctx.accounts.authority {
            Some(authority) => Some(authority.to_account_info()),
            None => None,
        };
        let owner = match &ctx.accounts.owner {
            Some(owner) => Some(owner.to_account_info()),
            None => None  
        };
        let  update_authority = match &ctx.accounts.update_authority {
            Some(update_authority) => Some(update_authority.to_account_info()),
            None => None,
        };
        // 创建向量来存储插件和外部插件适配器，以便我们可以使用正确的导入轻松添加插件
        let mut plugins = vec![];
        plugins.push(PluginAuthorityPair{
            plugin: Plugin::FreezeDelegate(FreezeDelegate { frozen: true }),
            authority: Some(PluginAuthority::UpdateAuthority)
        });
        // 外部插件适配器        
        // let mut external_plugin_adapter = vec![];
        // external_plugin_adapter.push(
        //     ExternalPluginAdapterInitInfo::AppData(
        //         AppDataInitInfo{
        //             init_plugin_authority: Some(PluginAuthority::UpdateAuthority),
        //             data_authority: PluginAuthority::Address { address: data_authority },
        //             schema: Some(ExternalPluginAdapterSchema::Binary),
        //         }
        //     ));



        CreateV2CpiBuilder::new(
            &ctx.accounts.mpl_core_program.to_account_info())
            .asset(&ctx.accounts.asset.to_account_info())
            .collection(collection.as_ref())
            .authority(authrity.as_ref())
            .payer(&ctx.accounts.payer.to_account_info())
            .owner(owner.as_ref())
            .update_authority(update_authority.as_ref())
            .system_program(&ctx.accounts.system_program.to_account_info())
            .name(args.name)
            .uri(args.uri)
            .plugins(plugins) // 插件
            // .external_plugin_adapter(external_plugin_adapter) // 外部插件适配器
            .invoke()?;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize {}
#[derive(Accounts)]
pub struct CreateAsset<'info> {
    #[account(mut)]
    pub asset: Signer<'info>,
    #[account(mut)]
    pub collection: Account<'info, BaseCollectionV1>,
    pub authority: Option<Signer<'info>>,
    #[account(mut)]
    pub payer: Signer<'info>,
    /// CHECK: this account will be checked by the mpl_core program
    pub owner: Option<UncheckedAccount<'info>>,
    /// CHECK: this account will be checked by the mpl_core program
    pub update_authority: Option<Signer<'info>>,
    pub system_program: Program<'info, System>,
    #[account(address = MPL_CORE_ID)]
    /// CHECK: this account will be checked by the mpl_core program
    pub mpl_core_program: UncheckedAccount<'info>,
}