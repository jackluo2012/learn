// 导入创建NFT和相关功能的模块
import { createNft, fetchDigitalAsset, mplTokenMetadata } from "@metaplex-foundation/mpl-token-metadata";
// 导入Solana开发者工具的辅助函数
import {
    airdropIfRequired,
    getKeypairFromFile,
} from "@solana-developers/helpers";
// 导入Umi框架的默认配置
import {
    createUmi
} from "@metaplex-foundation/umi-bundle-defaults";
// 导入Solana网络连接和工具
import { Connection, LAMPORTS_PER_SOL, clusterApiUrl } from "@solana/web3.js";
// 导入Umi框架的签名生成和身份工具
import { generateSigner, keypairIdentity, percentAmount } from "@metaplex-foundation/umi";

try {
    // 创建到Solana Devnet的连接
    const connection = new Connection(clusterApiUrl("devnet"), "confirmed");

    // 从本地文件加载用户的密钥对
    const user = await getKeypairFromFile("~/.config/solana/id.json");

    // 如果需要，为用户的钱包空投SOL（确保账户有足够的余额）
    await airdropIfRequired(connection, user.publicKey, 2 * LAMPORTS_PER_SOL, 0.5 * LAMPORTS_PER_SOL);

    // 打印加载的用户公钥
    console.log("Loaded user", user.publicKey.toBase58());

    // 创建Umi实例并设置RPC端点
    const umi = createUmi(connection.rpcEndpoint);

    // 使用Metaplex Token Metadata插件
    umi.use(mplTokenMetadata());

    // 使用用户的密钥对创建Umi身份
    const umiUser = umi.eddsa.createKeypairFromSecretKey(user.secretKey);
    umi.use(keypairIdentity(umiUser));

    // 打印Umi实例已设置完成
    console.log("Set up Umi instance for user");

    // 生成一个新的签名者，用于创建集合的Mint账户
    const collectionMint = generateSigner(umi);

    // 打印生成的Mint账户地址
    console.log("Generated collection mint address:", collectionMint.publicKey);

    // 创建一个NFT集合
    const transaction = await createNft(umi, {
        name: "My Collection", // 集合的名称
        symbol: "MCP", // 集合的符号
        uri: "https://example.com/new-collection-metadata", // 集合的元数据URI
        sellerFeeBasisPoints: percentAmount(0), // 卖家手续费（0%）
        mint: collectionMint, // 集合的Mint账户
        isCollection: true, // 标记为集合
    });

    // 发送并确认交易
    console.log("Sending transaction to create NFT collection...");
    await transaction.sendAndConfirm(umi);
    console.log("Transaction confirmed!");

    // 获取创建的集合NFT的元数据
    const createCollectionNft = await fetchDigitalAsset(umi, collectionMint.publicKey);

    // 打印集合NFT的地址和元数据
    console.log("Created collection NFT! Address is ", createCollectionNft, createCollectionNft.publicKey);

    // 打印成功消息
    console.log("Collection NFT created successfully");
} catch (error) {
    // 捕获并打印错误信息
    console.error("An error occurred:", error);
}













