import { ethers } from "ethers";

const { getDefaultProvider, JsonRpcProvider } = ethers;

async function main() {
    try {
        // DefaultProvider
        const providerMainnet = ethers.getDefaultProvider("mainnet");
        const providerSepolia = ethers.getDefaultProvider("sepolia");
        const providerMatic = ethers.getDefaultProvider("matic", {
            exclusive: ["etherscan", "infura"]
        })

        const blockNumberMainnet = await providerMainnet.getBlockNumber()
        const blockNumberSepolia = await providerSepolia.getBlockNumber()
        const blockNumberMatic = await providerMatic.getBlockNumber()

        console.log("provider Mainet:", blockNumberMainnet)
        console.log("provider Sepolia:", blockNumberSepolia)
        console.log("provider matic:", blockNumberMatic)
        
        // Local network - if have
        // const providerLocal = new JsonRpcProvider('http://localhost:8545');

        // Remote URL - Infura
        // const providerInfura = new JsonRpcProvider('https://mainnet.infura.io/v3/your-infura-project-id');
        // const blockNumberMainnetInfura = await providerInfura.getBlockNumber();
        // console.log("Provider Mainnet (Infura):", blockNumberMainnetInfura);

        // Remote URL - Alchemy
        const providerAlchemy = new JsonRpcProvider('https://eth-mainnet.g.alchemy.com/v2/-t6rLvfkU794BdiDw6MPHSFgFag_ilxQ');
        const blockNumberMainnetAlchemy = await providerAlchemy.getBlockNumber();
        console.log("Provider Mainnet (Alchemy):", blockNumberMainnetAlchemy);

    } catch (error) {
        console.error("Error:", error);
    }
}

main();