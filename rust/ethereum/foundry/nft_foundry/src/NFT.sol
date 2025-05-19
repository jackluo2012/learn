// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;
import "solmate/tokens/ERC721.sol";
import "openzeppelin-contracts/contracts/utils/Strings.sol";
import "openzeppelin-contracts/contracts/access/Ownable.sol";

// 定义一个名为 MintPriceNotPaid 的 error
error MintPriceNotPaid();
// 定义一个名为 MaxSupply 的 error  设置一个最大供应量
error MaxSupply();
// 定义一个名为 NonExistentTokenURI 的 error  访问不存在的 NFT 元数据的情况
error NonExistentTokenURI();

contract NFT is ERC721, Ownable {
    // 这里我们使用solmate的ERC721实现
    using Strings for uint256;
    // 这里我们使用一个简单的计数器来给每个token分配一个唯一的id
    // 定义一个名为 baseURI 的 public 变量，类型为 string。
    string public baseURI;
    uint256 public currentTokenId;
    // 这里我们设置一个最大容量
    uint256 public constant MAX_CAPACITY = 10_000;
    // 这里我们设置一个铸造价格
    uint256 public constant MINT_PRICE = 0.05 ether;

    constructor(
        string memory _name,
        string memory _symbol,
        string memory _baseURI
    ) ERC721(_name, _symbol) Ownable(msg.sender){
        baseURI = _baseURI;
    }

    function mintTo(address recipient) public payable returns (uint256) {
        // 使用 if 语句和 revert 关键字来验证用户输入。如果 msg.value != MINT_PRICE ，则 revert MintPriceNotPaid 错误。
        if (msg.value != MINT_PRICE) {
            revert MintPriceNotPaid();
        }
        // 如果没有错误，则增加当前的 tokenId，并使用 _safeMint 函数将其分配给接收者。
        uint256 newItemId = ++currentTokenId;
        // 如果当前的 tokenId 大于等于最大供应量，则 revert MaxSupply 错误。
        if (newItemId >= MAX_CAPACITY) {
            revert MaxSupply();
        }

        _safeMint(recipient, newItemId);
        return newItemId;
    }

    // 返回token的uri
    // 这里我们直接返回tokenId
    function tokenURI(
        uint256 tokenId
    ) public view virtual override returns (string memory) {
        // 使用 if 语句和 revert 关键字来验证用户输入。如果 ownerOf(tokenId) == address(0) ，则 revert NonExistentTokenURI 错误。
        if (ownerOf(tokenId) == address(0)) {
            revert NonExistentTokenURI();
        }

        // 验证 baseURI 是否有效并生成完整的 URI
        if (bytes(baseURI).length > 0) {
            return string(abi.encodePacked(baseURI, tokenId.toString()));
        } else {
            return "";
        }

        // 如果没有错误，则返回 token 的 URI。
        return Strings.toString(tokenId);
    }
}
