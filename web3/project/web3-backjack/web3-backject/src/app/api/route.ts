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
  private static instance: BlackjackDB;
  private client: MongoClient;
  private db: Db | null = null;
  private collection: Collection<Player> | null = null;
  private isConnected: boolean = false;
  private connectionPromise: Promise<void> | null = null;

  private constructor() {
    const uri = process.env.MONGO_URI || 'mongodb://localhost:27017';
    // 设置最大连接数和超时
    this.client = new MongoClient(uri, {
        maxPoolSize: 20, // 连接池最大连接数，可根据业务调整
        minPoolSize: 2,
        serverSelectionTimeoutMS: 5000, // 选择服务器超时
        socketTimeoutMS: 10000,         // 套接字超时
    });
  }

  public static getInstance(): BlackjackDB {
    if (!BlackjackDB.instance) {
      BlackjackDB.instance = new BlackjackDB();
    }
    return BlackjackDB.instance;
  }

  async connect(): Promise<void> {
    if (this.isConnected) return;
    if (!this.connectionPromise) {
      this.connectionPromise = this._connect();
    }
    return this.connectionPromise;
  }

  private async _connect(): Promise<void> {
    try {
      await this.client.connect();
      this.db = this.client.db(dbName);
      this.collection = this.db.collection<Player>(collectionName);
      this.isConnected = true;
      console.log('Connected to MongoDB');
    } catch (error) {
      console.error('Failed to connect to MongoDB:', error);
      this.connectionPromise = null;
      throw error;
    }
  }

  // 修改其他方法，确保在使用前已连接
  async createPlayer(playerName: string, score: number): Promise<void> {
    await this.connect(); // 确保连接
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
    await this.connect(); // 确保连接
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
    await this.connect(); // 确保连接
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
    await this.connect(); // 确保连接
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
    await this.connect(); // 确保连接
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

  public async ping(): Promise<boolean> {
    try {
        await this.connect();
        await this.db?.command({ ping: 1 });
        return true;
    } catch {
        this.isConnected = false;
        this.connectionPromise = null;
        return false;
    }
  }
}

// 修改数据库实例化方式
const db = BlackjackDB.getInstance();

(async () => {
  try {
    await db.connect(); // 确保连接完成
    // 删除默认创建玩家的代码，改为仅确保数据库连接
    console.log('Database connected successfully');
  } catch (error) {
    console.error("Error initializing database:", error);
  }
})();

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

// 用于存储每个玩家的游戏状态
const gameStates = new Map<string, typeof gameState>();

// ===================== 工具函数 =====================

/**
 * 构建标准 JSON 响应
 */
function buildResponse(data: object, status = 200) {
    return new Response(JSON.stringify(data), {
        status,
        headers: { "Content-Type": "application/json" }
    });
}

/**
 * 计算一手牌的点数，A可作1或11
 */
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

/**
 * 从牌堆中随机抽取 count 张牌
 */
function getRandomCard(deck: Card[], count: number): [Card[], Card[]] {
    const randomIndexSet = new Set<number>();
    while (randomIndexSet.size < count) {
        const randomIndex = Math.floor(Math.random() * deck.length);
        randomIndexSet.add(randomIndex);
    }
    const randomCards = deck.filter((_, index) => randomIndexSet.has(index));
    const remainingDeck = deck.filter((_, index) => !randomIndexSet.has(index));
    return [randomCards, remainingDeck];
}

// ===================== 游戏状态管理 =====================

/**
 * 获取初始游戏状态
 */
function getInitialGameState(): typeof gameState {
    return {
        playerHand: [],
        dealerHand: [],
        deck: [...initialDeck],
        playerScore: 0,
        dealerScore: 0,
        isPlayerTurn: true,
        isGameOver: false,
        winner: null,
        message: "",
        score: 0,
    };
}

/**
 * 获取或创建某玩家的游戏状态
 */
function getOrCreateGameState(address: string): typeof gameState {
    if (!gameStates.has(address)) {
        gameStates.set(address, getInitialGameState());
    }
    return gameStates.get(address)!;
}

// ===================== 业务逻辑分离 =====================

/**
 * 处理玩家 hit 操作
 */
function handleHit(state: typeof gameState) {
    const [cards, newDeck] = getRandomCard(state.deck, 1);
    state.playerHand.push(...cards);
    state.deck = newDeck;
    const playerHandValue = calculateHandValue(state.playerHand);
    if (playerHandValue === 21) {
        state.message = "玩家赢，二十一点";
        state.isGameOver = true;
        state.score += 100;
        state.winner = "player";
    } else if (playerHandValue > 21) {
        state.message = "玩家输，弃牌";
        state.isGameOver = true;
        state.winner = "dealer";
        state.score -= 100;
    }
}

/**
 * 处理玩家 stand 操作
 */
function handleStand(state: typeof gameState) {
    // 庄家补牌直到17点或以上
    while (calculateHandValue(state.dealerHand) < 17) {
        const [randomCards, newDeck] = getRandomCard(state.deck, 1);
        state.dealerHand.push(...randomCards);
        state.deck = newDeck;
    }
    const dealerHandValue = calculateHandValue(state.dealerHand);
    if (dealerHandValue === 21) {
        state.message = "庄家赢，庄家BlackJack";
        state.isGameOver = true;
        state.winner = "dealer";
        state.score -= 100;
    } else if (dealerHandValue > 21) {
        state.message = "庄家弃牌，玩家赢";
        state.isGameOver = true;
        state.winner = "player";
        state.score += 100;
    } else {
        const playerHandValue = calculateHandValue(state.playerHand);
        if (playerHandValue > dealerHandValue) {
            state.message = "玩家赢";
            state.isGameOver = true;
            state.winner = "player";
            state.score += 100;
        } else if (playerHandValue < dealerHandValue) {
            state.message = "庄家赢";
            state.isGameOver = true;
            state.winner = "dealer";
            state.score -= 100;
        } else {
            state.message = "平局";
        }
    }
}

/**
 * 验证JWT Token
 */
function verifyToken(request: Request, address: string): string | null {
    const token = request.headers.get("bearer")?.split(" ")[1];
    if (!token) return null;
    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET || "") as { address: string };
        if (!decoded || !decoded.address || decoded.address.toLowerCase() !== address.toLowerCase()) {
            return null;
        }
        return token;
    } catch {
        return null;
    }
}

// ===================== API 入口 =====================

/**
 * GET: 初始化一局游戏
 */
export async function GET(request: Request) {
    const url = new URL(request.url);
    const address = url.searchParams.get("address");
    if (!address) {
        return buildResponse({ playerHand: [], dealerHand: [], message: "address is required", score: 0 }, 400);
    }
    const state = getOrCreateGameState(address);
    Object.assign(state, getInitialGameState());

    // 发牌
    const [playerCards, remainingDeck] = getRandomCard(state.deck, 2);
    const [dealerCards, newDeck] = getRandomCard(remainingDeck, 1);
    state.playerHand = playerCards;
    state.dealerHand = dealerCards;
    state.deck = newDeck;
    state.message = "";

    // 查询分数
    const player = await db.getPlayerByName(address);
    state.score = player?.score || 0;

    return buildResponse({
        playerHand: state.playerHand,
        dealerHand: [state.dealerHand[0], { suit: "？", rank: "？" } as Card],
        message: state.message,
        score: state.score,
    });
}

/**
 * POST: 处理玩家操作（auth/hit/stand）
 */
export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { action, address } = body;

        // 参数校验
        if (!action || !address) {
            return buildResponse({ message: "Missing required parameters" }, 400);
        }

        await db.connect();

        // 处理登录认证
        if (action === "auth") {
            const { address, message, signature } = body;
            const isValid = await verifyMessage({ address, message, signature });
            if (!isValid) {
                return buildResponse({ message: "签名验证失败" }, 400);
            }
            const token = jwt.sign({ address }, process.env.JWT_SECRET || "", { expiresIn: "1h" });
            // 自动注册新玩家
            try {
                const player = await db.getPlayerByName(address);
                if (!player) {
                    await db.createPlayer(address, 0);
                }
            } catch (error) {
                console.error("Error checking/creating player:", error);
            }
            return buildResponse({ message: "签名验证成功", jsonwebtoken: token }, 200);
        }

        // 其它操作需校验token
        if (!verifyToken(request, address)) {
            return buildResponse({ message: "token is invalid or required" }, 400);
        }

        const state = getOrCreateGameState(address);

        // 处理游戏动作
        if (action === "hit") {
            handleHit(state);
        } else if (action === "stand") {
            handleStand(state);
        } else {
            return buildResponse({ message: "无效的操作" }, 400);
        }

        // 更新分数
        try {
            await db.updatePlayerScore(address, state.score);
        } catch (error) {
            console.error("Failed to update player score:", error);
        }

        return buildResponse({
            playerHand: state.playerHand,
            dealerHand: state.message === "" ? [state.dealerHand[0], { suit: "？", rank: "？" } as Card] : state.dealerHand,
            message: state.message,
            winner: state.winner,
            score: state.score,
        });
    } catch (error) {
        console.error('Error processing request:', error);
        return buildResponse({ message: error instanceof Error ? error.message : "Internal server error" }, 500);
    }
}



