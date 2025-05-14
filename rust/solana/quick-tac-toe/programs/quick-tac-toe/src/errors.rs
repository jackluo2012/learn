use anchor_lang::error_code;

#[error_code]
pub enum TicTacToeError {
    #[msg("Square is not inside 3x3 board")]
    SquareOffBoard,
    #[msg("Someone has already played this square")]
    SquareAlreadySet,
    #[msg("The game is not active")]
    GameNotActive,
    #[msg("Not your turn")]
    NotPlayersTurn,
    #[msg("This game has already started")]
    GameAlreadyStarted,
    #[msg("Invalid Player")]
    InvalidPlayer,
    #[msg("Reward already claimed")]
    RewardAlreadyClaimed, 
    #[msg("Not eligible for reward")]
    NotEligibleForReward
}