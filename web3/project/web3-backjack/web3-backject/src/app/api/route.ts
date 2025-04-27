import dotenv from 'dotenv';
dotenv.config();
//  使用mongodb 
import { MongoClient, Db, Collection } from 'mongodb';
import { verifyMessage } from 'viem';

import jwt from 'jsonwebtoken';

// 定义Player接口
interface Player {
  _id?: string;
  player: string;
  score: number;
}

// MongoDB连接配置
const uri = process.env.MONGO_URI as string;//'mongodb://localhost:27017'; // 替换为你的MongoDB连接字符串

console.log('MongoDB URI:', uri);

const dbName = 'blackjack';
const collectionName = 'players';

class BlackjackDB {
  private client: MongoClient;
  private db: Db | null = null;
  private collection: Collection<Player> | null = null;
  private isConnected: boolean = false; // 标志位

  constructor() {
    this.client = new MongoClient(uri);
  }

  // 连接数据库并初始化
  async connect(): Promise<void> {
    try {
      await this.client.connect();
      this.db = this.client.db(dbName);
      this.collection = this.db.collection<Player>(collectionName);
      this.isConnected = true; // 设置标志位
      console.log('Connected to MongoDB');
    } catch (error) {
      console.error('Failed to connect to MongoDB:', error);
      throw error;
    }
  }

  // 关闭数据库连接
  async close(): Promise<void> {
    await this.client.close();
    console.log('MongoDB connection closed');
  }

  // 创建新玩家记录
async createPlayer(playerName: string, score: number): Promise<void> {
    if (!this.isConnected) throw new Error('Database not connected'); // 检查标志位
    if (!this.collection) throw new Error('Collection not initialized');

    try {
        const existingPlayer = await this.collection.findOne({ player: playerName });
        if (existingPlayer) {
            console.log(`Player ${playerName} already exists`);
        } else {
            const player: Player = {
                player: playerName,
                score: score
            };
            await this.collection.insertOne(player);
            console.log(`Player ${playerName} created with score ${score}`);
        }
    } catch (error) {
        console.error('Failed to create or check player:', error);
        throw error;
    }
}

  // 读取所有玩家记录
  async getAllPlayers(): Promise<Player[]> {
    if (!this.collection) throw new Error('Collection not initialized');
    
    try {
      const players = await this.collection.find({}).toArray();
      return players;
    } catch (error) {
      console.error('Failed to read players:', error);
      throw error;
    }
  }

  // 根据玩家名称读取记录
  async getPlayerByName(playerName: string): Promise<Player | null> {
    if (!this.collection) throw new Error('Collection not initialized');
    
    try {
      const player = await this.collection.findOne({ player: playerName });
      return player;
    } catch (error) {
      console.error('Failed to read player:', error);
      throw error;
    }
  }

  // 更新玩家分数
  async updatePlayerScore(playerName: string, newScore: number): Promise<void> {
    if (!this.collection) throw new Error('Collection not initialized');
    
    try {
      const result = await this.collection.updateOne(
        { player: playerName },
        { $set: { score: newScore } }
      );
      if (result.matchedCount === 0) {
        console.log(`Player ${playerName} not found`);
      } else {
        console.log(`Player ${playerName}'s score updated to ${newScore}`);
      }
    } catch (error) {
      console.error('Failed to update player score:', error);
      throw error;
    }
  }

  // 删除玩家记录
  async deletePlayer(playerName: string): Promise<void> {
    if (!this.collection) throw new Error('Collection not initialized');
    
    try {
      const result = await this.collection.deleteOne({ player: playerName });
      if (result.deletedCount === 0) {
        console.log(`Player ${playerName} not found`);
      } else {
        console.log(`Player ${playerName} deleted`);
      }
    } catch (error) {
      console.error('Failed to delete player:', error);
      throw error;
    }
  }
}

const db = new BlackjackDB();

(async () => {
  try {
    await db.connect(); // 确保连接完成
    const DEFAULT_PLAYER = "jackluo";
    await db.createPlayer(DEFAULT_PLAYER, 0); // 创建玩家
  } catch (error) {
    console.error("Error initializing database:", error);
  }
})();


const DEFAULT_PLAYER = "jackluo";

// 当游戏开始时，分别给玩家和庄家2张随机牌。
export interface Card {
    suit: string;
    rank: string;
}
const ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"];
const suits = ["♥️", "♠️", "♣️", "♦️"];
const initialDeck = ranks.flatMap((rank) => suits.map((suit) => { return { "rank": rank, "suit": suit } }));

// 获取游戏 的状态
const gameState: {
    playerHand: Card[],
    dealerHand: Card[],
    deck: Card[],
    playerScore: number,
    dealerScore: number,
    isPlayerTurn: boolean,
    isGameOver: boolean,
    winner: string | null,
    message: string,
    score:number,

} = {
    playerHand: [],
    dealerHand: [],
    deck: initialDeck,
    playerScore: 0,
    dealerScore: 0,
    isPlayerTurn: true,
    isGameOver: false,
    winner: null,
    message: "",
    score:0,
};
//  获取随机的卡片
// deck 中 抽取count 张卡片
function getRandomCard(deck: Card[], count: number): Card[][] {
    // count 是要抽取的卡片数量，这个要获取 deck 中 随机的下标，而且不会重复 
    const randomIndexSet = new Set<number>();
    while (randomIndexSet.size < count) {
        const randomIndex = Math.floor(Math.random() * deck.length);
        randomIndexSet.add(randomIndex);
    }
    // 根据从 randomIndexSet 中获取下标，从 deck 中获取对应的卡片
    const randomCards = deck.filter((_, index) => randomIndexSet.has(index));
    // 上面已经抽取了count 张卡片，所以需要更新 deck
    const remainingDeck = deck.filter((_, index) => !randomIndexSet.has(index));

    return [randomCards, remainingDeck]
}
export async function GET(request:Request) {
    const url = new URL(request.url);
    const address = url.searchParams.get("address");
    if (!address){
        return new Response(JSON.stringify({
            playerHand: [],
            dealerHand: [],
            message: "address is required",
            score:0,
        }), {
            status: 400,
            headers: {
                "Content-Type": "application/json"
            }
        });
    }
    //    重置状态
    gameState.playerHand = [];
    gameState.dealerHand = [];
    gameState.deck = initialDeck;
    gameState.message = "";
    const [playerCards, remainingDeck] = getRandomCard(gameState.deck, 2);
    //   
    const [dealerCards, newDeck] = getRandomCard(remainingDeck, 1);
    //   更新 gameState
    gameState.playerHand = playerCards;
    gameState.dealerHand = dealerCards;
    gameState.deck = newDeck;
    gameState.message = "";

    // 从数据中读取数据
    const player = await db.getPlayerByName(address);
    gameState.score = player?.score || 0;


    return new Response(JSON.stringify({
        playerHand: gameState.playerHand,
        dealerHand: [gameState.dealerHand[0], { suit: "？", rank: "？" } as Card],
        message: gameState.message,
        score:gameState.score,

    }), {
        status: 200,
        headers: {
            "Content-Type": "application/json"
        }
    });
}


export async function POST(request: Request) {
    // 接收参数
    const body = await request.json();
    const { action,address } = body;
    if (action === "auth") {
        const {address,message,signature} = body;
        const isValid = await verifyMessage({address,message,signature});
        if(!isValid){
            return new Response(JSON.stringify({
                message: "签名验证失败",
            }), {
                status: 400,
                headers: {
                    "Content-Type": "application/json"
                }
            });
        }else{
            const token = jwt.sign({ address },process.env.JWT_SECRET || "",{expiresIn:"1h"});

            return new Response(JSON.stringify({
                message: "签名验证成功",
                jsonwebtoken: token,
            }), {
                status: 200,
                headers: {
                    "Content-Type": "application/json"
                }
            });
        }
    }

    //  验证token 
    const token = request.headers.get("bearer")?.split(" ")[1];
    if (!token) {
        return new Response(JSON.stringify({
            message: "token is required",
        }), {
            status: 400,
            headers: {
                "Content-Type": "application/json"
            }
        });
    }
    const decoded = jwt.verify(token, process.env.JWT_SECRET || "") as { address: string };
    if (!decoded || decoded.address.toLocaleLowerCase !== address.toLocaleLowerCase) {
        return new Response(JSON.stringify({
            message: "token is invalid",
        }), {
            status: 400,
            headers: {
                "Content-Type": "application/json"
            }
        });
    }



    if (action === "hit") {
        // 当点击时，从牌组中随机抽取一张牌并将其添加到玩家手中// 计算玩家手牌值
        // //玩家手牌值为21:玩家赢，二十一点
        // //玩家手牌超过21:玩家输，弃牌
        // //玩家手牌小于21:继续玩家可以击牌或站立
        // 从现有的游戏状态中获取牌组，抽取一张牌，更新游戏状态，并返回更新后的游戏状态
        const [cards, newDeck] = getRandomCard(gameState.deck, 1);
        // 更新 游戏状态，投取的值 
        gameState.playerHand.push(...cards);
        //  设置游戏的新的状态 
        gameState.deck = newDeck;
        const playerHandValue = calculateHandValue(gameState.playerHand);
        if (playerHandValue === 21) {
            gameState.message = "玩家赢，二十一点";
            gameState.isGameOver = true;
            gameState.score=gameState.score+100;
            gameState.winner = "player";
        } else if (playerHandValue > 21) {
            gameState.message = "玩家输，弃牌";
            gameState.isGameOver = true;
            gameState.winner = "dealer";
            gameState.score=gameState.score-100;
        }
    } else if (action === "stand") {
        // /当点击站立时，从牌堆中随机抽取一张牌并将其添加到庄家手中
        // //继续这样做，直到庄家有17分或更多
        // /计算庄家手牌值
        // //庄家手牌值为21:玩家输，庄家黑桃J
        // //庄家底牌是21:玩家赢，庄家弃牌
        // //庄家手牌少于21
        // //计算玩家手牌值
        // //玩家>庄家:玩家赢
        // //玩家<庄家:玩家输
        // //玩家=庄家:平局
        
        while (calculateHandValue(gameState.dealerHand) < 17) {
            const [randomCards, newDeck] = getRandomCard(gameState.deck, 1);
            // 更新抽卡以后的gameState
            gameState.dealerHand.push(...randomCards);
            gameState.deck = newDeck;
        }
        const dealerHandValue = calculateHandValue(gameState.dealerHand);
        if (dealerHandValue === 21) {
            gameState.message = "庄家赢，庄家BlackJack";
            gameState.isGameOver = true;
            gameState.winner = "dealer";
            gameState.score=gameState.score-100;
        } else if (dealerHandValue > 21) {
            gameState.message = "庄家弃牌，玩家赢";
            gameState.isGameOver = true;
            gameState.winner = "player";
            gameState.score=gameState.score+100;
        }else{
            // 计算玩家的牌值
            const playerHandValue = calculateHandValue(gameState.playerHand);
            if (playerHandValue > dealerHandValue) {
                gameState.message = "玩家赢";
                gameState.isGameOver = true;
                gameState.winner = "player";
                gameState.score=gameState.score+100;
            } else if (playerHandValue < dealerHandValue) {
                gameState.message = "庄家赢";
                gameState.isGameOver = true;
                gameState.winner = "dealer";
                gameState.score=gameState.score-100;
            } else{
                gameState.message = "平局";
            }
        }

    } else {
        return new Response(JSON.stringify({
            message: "无效的操作"
        }), {
            status: 400,
            headers: {
                "Content-Type": "application/json"
            }
        });
    }
    // 写入操作
    try {
        await db.updatePlayerScore(address, gameState.score);
    } catch (error) {
        console.error("Failed to update player score:", error);
    }

    return new Response(JSON.stringify({
        playerHand: gameState.playerHand,
        dealerHand:gameState.message===""?[gameState.dealerHand[0],{ suit: "？", rank: "？" } as Card]:gameState.dealerHand ,
        message: gameState.message,
        winner: gameState.winner,
        score:gameState.score,
    }), {
        status: 200,
        headers: {
            "Content-Type": "application/json"
        }
    });
}
//  计算 卡片的值 
function calculateHandValue(hand: Card[]): number {
    let value = 0;
    let aceCount = 0;
    hand.forEach((card) => {
        if (card.rank === "A") {
            value += 11;
            aceCount++;
        } else if (["J", "Q", "K"].includes(card.rank)) {
            value += 10;
        } else {
            value += parseInt(card.rank);
        }
    });
    while (value > 21 && aceCount > 0) {
        value -= 10;
        aceCount--;
    }
    return value;
}



