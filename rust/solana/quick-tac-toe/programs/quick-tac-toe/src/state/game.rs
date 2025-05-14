use anchor_lang::prelude::*;
use crate::errors::TicTacToeError;
use crate::state::Player;
// use num_derive::*;
use std::str::FromStr; 
use num_derive::{FromPrimitive, ToPrimitive};
#[account]
pub struct Game {
    pub id: u64,                       // 8
    pub player_x: Pubkey,              // 32
    pub player_o: Pubkey,              // 32
    pub board: [[Option<Sign>; 3]; 3], // 9 * (1 + 1) = 18 游戏状态
    pub state: GameState,              // 32 + 1 游戏状态
    pub turn: u8,                      // 1  轮到哪儿了
    pub bump: u8,                      // 1 游戏的
    pub winner: Option<Pubkey>         // 32 获胜者
}

impl Game {
    pub fn calculate_account_space() -> usize {
        8 +     // discriminator
        8 +     // id
        32 +    // player_x
        32 +    // player_o
        18 +    // board
        33 +    // game state
        1 +     // turn
        1 +     // bump + 20
        32
    }
//  创建游戏
    pub fn create(&mut self, player_x: Pubkey, bump: u8, id: u64) {
        self.id = id;
        self.player_x = player_x;
        self.player_o = player_x; // placeholder
        self.board = [[None; 3]; 3];
        self.state = GameState::NotStarted;
        self.turn = 0;
        self.bump = bump;
        self.winner = None;
    }
// 开始游戏
    pub fn start(&mut self, player_o: Pubkey) {
        self.player_o = player_o;
        self.state = GameState::Active;
        self.turn = 1;
        self.log_board();
    }

    pub fn is_active(&self) -> bool {
        self.state == GameState::Active
    }

    fn current_player_index(&self) -> u8 {
        ((self.turn - 1) % 2) + 1
    }
// 轮到哪个玩家
    pub fn current_player(&self) -> Pubkey {
        if self.current_player_index() == 1 {
            self.player_x
        } else {
            self.player_o
        }
    }
// 将用于根据当前玩家的公钥获取其符号,玩家1是白棋学是黑棋，x或者o
    pub fn current_player_sign(&self) -> Sign {
        if self.current_player() == self.player_x {
            Sign::X
        } else {
            Sign::O
        }
    }
// 根据程序的id 以及  玩家id 生成PDA
    pub fn other_player_pda(&self) -> Pubkey {
        // 
        let program_id = Pubkey::from_str("2Uu3bSun9P8CrkAyCvYtUoMdTqET6FA2N5wKpJVQzM6L").unwrap();
        let other_player = if self.current_player_index() == 1 {
            self.player_o
        } else {
            self.player_x
        };
        let (pda, _bump) = Pubkey::find_program_address(
            &[
                b"player".as_ref(),
                other_player.key().as_ref(),
            ],
            &program_id,
        );
        pda.key()
    }
// 将游戏板记录到我们的程序日志中，以便我们可以在 Solana Explorer 中看到它。这将呈现一个简单的板
    fn log_board(&self) {
        for row in 0..=2 {
            let mut row_representation = String::new();

            for column in 0..=2 {
                row_representation.push(match self.board[row][column] {
                    Some(Sign::X) => 'X',
                    Some(Sign::O) => 'O',
                    None => '_',
                });
                row_representation.push(' ');
            }

            row_representation.pop(); // Remove the extra space at the end of the row
            msg!("Row {}: {}", row + 1, row_representation);
        }
    }

    pub fn play(&mut self, square: &Square,  player_record: &mut Player, other_player_record: &mut Player) -> Result<()> {
        let sign = self.current_player_sign();
        // 尝试将玩家的标记添加到目标方格
        match square {
            // 表示只接受行和列都在 0~2 范围内的格子
            // 绑定到变量 square
            square @ Square {
                row: 0..=2,
                column: 0..=2,
                    // 已经有棋子
            } => match self.board[square.row as usize][square.column as usize] {
                // 格子已被占用
                Some(_) => return Err(TicTacToeError::SquareAlreadySet.into()),
                // 把当前玩家的棋子放上去
                None => self.board[square.row as usize][square.column as usize] = Some(sign),
            },
            _ => return Err(TicTacToeError::SquareOffBoard.into()),
        }

        // 然后它将检查游戏是赢还是平.
        self.update_state();

        // Update Record. 

        if GameState::Won == self.state {
            player_record.record_win();
            other_player_record.record_lose();
        }
        if GameState::Tie == self.state {
            player_record.record_tie();
            other_player_record.record_tie();
        }
        if GameState::Active == self.state {
            self.turn += 1;
        }

        self.log_board();
        Ok(())
    }
    // 用于检查玩家是否赢得了游戏
    fn is_winning_trio(&self, trio: [(usize, usize); 3]) -> bool {
        let [first, second, third] = trio;
        self.board[first.0][first.1].is_some()
            && self.board[first.0][first.1] == self.board[second.0][second.1]
            && self.board[first.0][first.1] == self.board[third.0][third.1]
    }

    fn update_state(&mut self) {
        for i in 0..=2 {
            // three of the same in one row
            if self.is_winning_trio([(i, 0), (i, 1), (i, 2)]) {
                self.state = GameState::Won;
                self.winner = Some(self.current_player());
                msg!("Winner is: {}", self.current_player());
                return;
            }
            // three of the same in one column
            if self.is_winning_trio([(0, i), (1, i), (2, i)]) {
                self.state = GameState::Won;
                self.winner = Some(self.current_player());
                msg!("Winner is: {}", self.current_player());
                return;
            }
        }

        // three of the same in one diagonal
        if self.is_winning_trio([(0, 0), (1, 1), (2, 2)])
            || self.is_winning_trio([(0, 2), (1, 1), (2, 0)])
        {
            self.state = GameState::Won;
            self.winner = Some(self.current_player());
            msg!("Winner is: {}", self.current_player());
            return;
        }

        //Reaching this code means the game has not been won,
        // so if there are unfilled tiles left, it's still active
        for row in 0..=2 {
            for column in 0..=2 {
                if self.board[row][column].is_none() {
                    return;
                }
            }
        }

        //The game has not been won
        // game has no more free tiles
        // -> game ends in a tie
        self.state = GameState::Tie;
    }
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Debug, PartialEq, Eq)]
pub enum GameState {
    NotStarted,
    Active,
    Tie,
    Won,
}

#[derive(AnchorSerialize, AnchorDeserialize,FromPrimitive,Copy, ToPrimitive, Clone, Debug, PartialEq, Eq)]
pub enum Sign {
    X, // Player 1
    O, // Player 2
}

#[derive(AnchorSerialize, AnchorDeserialize)]
// 用于标识玩家在棋盘上放置 “X” 或 “O” 的位置
pub struct Square {
    row: u8, //“X” “X” 或 “O” 的位置
    column: u8,
}