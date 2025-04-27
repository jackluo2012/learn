"use client"
import { act, useEffect, useState } from "react";
import { ConnectButton } from "@rainbow-me/rainbowkit";
import { useAccount,useSignMessage } from "wagmi";
export default function Page() {

  //  设置谁赢了
  const [winner, setWinner] = useState<string>("");
  // 设置消息
  const [message, setMessage] = useState<string>("");
  const [score, setScore] = useState<number>(0);
  const [playerHand, setPlayerHand] = useState<{ rank: string, suit: string }[]>([]);
  const [dealerHand, setDealerHand] = useState<{ rank: string, suit: string }[]>([]);
  const [isSignature, setIsSignature] = useState<boolean>(false);
  const { address,isConnected } = useAccount();
 
  const { signMessageAsync } = useSignMessage();
  // 始化化
 
  const initGame = async () => {
    // 获取数据
    const response = await fetch(`/api/?address=${address}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    // 解析数据
    const data = await response.json();

    // 设置数据
    setPlayerHand(data.playerHand);
    setDealerHand(data.dealerHand);
    setMessage(data.message);
    setWinner(data.winner);
    setScore(data.score);

    console.log(address,isConnected);

  };
  async function handleHit() {
    // 调用 API 获取数据
    const response = await fetch(`/api/?address=${address}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        bearer: `Bearer ${localStorage.getItem("jwt")} || ""`,
      },
      body: JSON.stringify({
        action: "hit",
        address
      }),
    });

    // 解析数据
    const data = await response.json();
    // 设置数据
    setPlayerHand(data.playerHand);
    setDealerHand(data.dealerHand);
    setMessage(data.message);
    setWinner(data.winner);
    setScore(data.score);
  }
  async function handleStand() {
    // 调用 API 获取数据
    const response = await fetch(`/api/?address=${address}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        bearer: `Bearer ${localStorage.getItem("jwt")} || ""`,
      },
      body: JSON.stringify({
        action: "stand",
        address
      }),
    });

    // 解析数据
    const data = await response.json();
    // 设置数据
    setPlayerHand(data.playerHand);
    setDealerHand(data.dealerHand);
    setMessage(data.message);
    setWinner(data.winner);
    setScore(data.score);
  }

  async function handleRest() {
    const response = await fetch(`/api/?address=${address}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        bearer: `Bearer ${localStorage.getItem("jwt")} || ""`,
      },
    });
    const data = await response.json();
    setPlayerHand(data.playerHand);
    setDealerHand(data.dealerHand);
    setMessage(data.message);
    setWinner(data.winner);
    setScore(data.score);
  }
//验证是否是用户的钱包
  async function handleSign() {
    // 要进行签名的消息,加入随机 时间，免得 重复
    const message = `Welcome to Web3 game Black Jack ${new Date().toString()}`
    // 进行消息签名认证
    const signature = await signMessageAsync({message});

    // 调用 API 获取数据
    const response = await fetch(`/api/?address=${address}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        action: "auth",
        address: address,
        message,
        signature,
      }),
    });

     if (response.status === 200){
      const {jsonwebtoken} = await response.json();
      //存入 本地缓存中
      localStorage.setItem("jwt", jsonwebtoken);


      setIsSignature(true);
      initGame();
      console.log("验证成功");
     }
  }
  if (! isSignature){
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold mb-4 text-gray-800">
            Welcome to Web3 game Black Jack
          </h1>
          <p className="text-lg font-semibold  text-gray-700 mb-8">
          <ConnectButton />
          <button onClick={handleSign} className="px-8 py-4 bg-yellow-400 text-gray-800 font-bold rounded-lg hover:bg-yellow-500 transition duration-300 shadow-md">
          签名验证你的钱包
        </button>
         </p>
        </div>
        
      </div>
    )
  }
  return (
    <div className="font-sans p-5 text-center bg-gray-200 min-h-screen">
      
      <ConnectButton />
      

      {/* 网页名称 */}
      <h1 className="text-4xl font-extrabold mb-4 text-gray-800">
        Welcome to Web3 game Black Jack
      </h1>

      {/* 提示信息 */}
      <p className={`text-lg font-semibold text-gray-700 mb-8 ${winner === "player" ? "bg-green-500" : "bg-amber-500"}`}>
        Score: {score}  {message}
      </p>

      {/* Dealer 区域 */}
      <div className="my-5 p-5 border border-gray-400 bg-white rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">Dealer's hand</h2>
        <div className="flex justify-center gap-6">
          {dealerHand.map((card, index) => (
            <div
              key={index}
              className="w-28 h-40 sm:w-32 sm:h-48 md:w-36 md:h-52 lg:w-40 lg:h-56 border border-gray-500 bg-white flex flex-col items-center justify-between rounded-lg shadow-md p-3 relative"
            >
              {/* 左上角的牌面 */}
              <div className="absolute top-2 left-2 text-sm md:text-base font-bold text-black">
                {card.rank}
                <span className="text-lg md:text-xl">{card.suit}</span>
              </div>

              {/* 中间的花色 */}
              <div className="flex items-center justify-center h-full text-4xl md:text-5xl text-black">
                {card.suit}
              </div>

              {/* 右下角的牌面 */}
              <div className="absolute bottom-2 right-2 text-sm md:text-base font-bold text-black rotate-180">
                {card.rank}
                <span className="text-lg md:text-xl">{card.suit}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Player 区域 */}
      <div className="my-5 p-5 border border-gray-400 bg-white rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">Player's hand</h2>
        <div className="flex justify-center gap-6">
          {playerHand.map((card, index) => (
            <div
              key={index}
              className="w-28 h-40 sm:w-32 sm:h-48 md:w-36 md:h-52 lg:w-40 lg:h-56 border border-gray-500 bg-white flex flex-col items-center justify-between rounded-lg shadow-md p-3 relative"
            >
              {/* 左上角的牌面 */}
              <div className="absolute top-2 left-2 text-sm md:text-base font-bold text-black">
                {card.rank}
                <span className="text-lg md:text-xl">{card.suit}</span>
              </div>

              {/* 中间的花色 */}
              <div className="flex items-center justify-center h-full text-4xl md:text-5xl text-black">
                {card.suit}
              </div>

              {/* 右下角的牌面 */}
              <div className="absolute bottom-2 right-2 text-sm md:text-base font-bold text-black rotate-180">
                {card.rank}
                <span className="text-lg md:text-xl">{card.suit}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 按钮组合 */}
      <div className="my-5 flex justify-center gap-4">
       {
        message === ""?
        <>
        <button onClick={handleHit} className="px-8 py-4 bg-yellow-400 text-gray-800 font-bold rounded-lg hover:bg-yellow-500 transition duration-300 shadow-md">
          Hit
        </button>
        <button onClick={handleStand} className="px-8 py-4 bg-yellow-400 text-gray-800 font-bold rounded-lg hover:bg-yellow-500 transition duration-300 shadow-md">
          Stand
        </button>
        </>:
         <button onClick={handleRest} className="px-8 py-4 bg-yellow-400 text-gray-800 font-bold rounded-lg hover:bg-yellow-500 transition duration-300 shadow-md">
         Reset
       </button>
       }
      </div>
    </div>
  );
}
