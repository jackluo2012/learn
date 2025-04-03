pub mod constants;
pub mod error;
pub mod instructions;
pub mod state;

use anchor_lang::prelude::*;

pub use constants::*;
pub use instructions::*;
pub use state::*;

declare_id!("6AXyJSJuMYs6PRtfq3yUUcS5rhSSnwfmt6426sp7NJRv");

#[program]
pub mod swap {
    use crate::instruction::MakeOffer;

    use super::*;

    pub fn make_offer(ctx: Context<MakeOffer>) -> Result<()> {
        instructions::make_offer::send_offered_tokens_to_vault(ctx)?;
        instructions::make_offer::save_offer(ctx)
    }
}
