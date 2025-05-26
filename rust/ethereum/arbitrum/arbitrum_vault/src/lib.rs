use alloy_primitives::{Address, U256};
use stylus_sdk::{
    contract, call::{self, Call}, msg, prelude::*, evm,
    storage::{StorageAddress, StorageU256, StorageBool}
};
use alloy_sol_types::{sol, SolCall};

// 模块和导入
mod erc20;
use crate::erc20::{Erc20, Erc20Params, Erc20Error};

// 定义 Vault 代币的不可变参数
struct StylusTokenParams;
impl Erc20Params for StylusTokenParams {
    const NAME: &'static str = "VAULT Token"; // 代币名称
    const SYMBOL: &'static str = "VAULT"; // 代币符号
    const DECIMALS: u8 = 18; // 代币精度
}

// 定义 ERC20 接口，用于外部调用
sol! {
    interface IERC20 {
        function transfer(address recipient, uint256 amount) external returns (bool);
        function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
        function balanceOf(address account) external view returns (uint256);
    }
}

// 定义事件
#[derive(SolidityEvent)]
pub struct Deposit {
    #[indexed] user: Address, // 存款用户地址
    assets: U256, // 存款资产数量
    shares: U256, // 获得的份额数量
    total_assets: U256, // 存款后的总资产
    total_shares: U256, // 存款后的总份额
}

#[derive(SolidityEvent)]
pub struct Withdraw {
    #[indexed] user: Address, // 提取用户地址
    assets: U256, // 提取资产数量
    shares: U256, // 销毁的份额数量
    total_assets: U256, // 提取后的总资产
    total_shares: U256, // 提取后的总份额
}

// 定义错误类型
#[derive(SolidityError)]
pub enum VaultError {
    AssetNotSet, // 资产地址未设置
    ZeroAmount, // 金额为零
    InsufficientShares, // 份额不足
    InsufficientAssets, // 资产不足
    TransferFailed, // 转账失败
    Reentrancy, // 重入攻击
    Overflow, // 数值溢出
    DivideByZero, // 除零错误
    InvalidReturnData, // 无效的返回数据
    Unauthorized, // 未授权操作
    BalanceMismatch, // 余额不匹配
}

// 实现错误转换
impl From<Erc20Error> for VaultError {
    fn from(_: Erc20Error) -> Self {
        VaultError::TransferFailed // 将 Erc20Error 映射到 VaultError
    }
}

impl From<stylus_sdk::call::Error> for VaultError {
    fn from(_: stylus_sdk::call::Error) -> Self {
        VaultError::TransferFailed // 将 call::Error 映射到 VaultError
    }
}

// 定义存储结构
sol_storage! {
    #[entrypoint]
    struct StylusToken {
        #[borrow]
        Erc20<StylusTokenParams> erc20; // ERC20 代币逻辑
        StorageU256 total_shares; // 总份额
        StorageAddress asset; // 资产代币地址
        StorageBool locked; // 非重入锁
        StorageAddress owner; // 合约所有者
    }
}

#[external]
#[inherit(Erc20<StylusTokenParams>)]
impl StylusToken {
    /// 设置资产代币地址，仅限所有者
    pub fn set_asset(&mut self, asset: Address) -> Result<Address, VaultError> {
        // 检查调用者是否为所有者
        if self.owner.get() == Address::ZERO {
            self.owner.set(msg::sender()); // 首次调用设置所有者
        } else if msg::sender() != self.owner.get() {
            return Err(VaultError::Unauthorized);
        }
        // 验证资产地址
        if asset == Address::ZERO {
            return Err(VaultError::AssetNotSet);
        }
        self.asset.set(asset);
        Ok(asset)
    }

    /// 存入资产到 Vault，铸造相应份额
    #[payable]
    pub fn deposit(&mut self, assets: U256) -> Result<U256, VaultError> {
        // 检查非重入锁
        if self.locked.get() {
            return Err(VaultError::Reentrancy);
        }
        self.locked.set(true);

        // 验证输入
        if assets == U256::ZERO {
            self.locked.set(false);
            return Err(VaultError::ZeroAmount);
        }
        let asset_addr = self.asset.get();
        if asset_addr == Address::ZERO {
            self.locked.set(false);
            return Err(VaultError::AssetNotSet);
        }

        // 获取当前余额
        let balance_before = self.vault_balance()?;

        // 计算份额
        let total_assets = self.total_assets()?;
        let total_shares = self.total_shares.get();
        let shares = Self::calculate_shares(assets, total_assets, total_shares)?;

        // 更新状态
        self.total_shares.set(total_shares + shares);
        self.erc20._mint(msg::sender(), shares)?;

        // 调用资产合约的 transferFrom
        let call_data = IERC20::transferFromCall {
            sender: msg::sender(),
            recipient: contract::address(),
            amount: assets,
        }.abi_encode();
        let return_data = call::call(Call::new(), asset_addr, &call_data)?;
        let success = IERC20::transferFromCall::abi_decode(&return_data, true)
            .map(|result| result._0)
            .unwrap_or(false);
        if !success {
            self.locked.set(false);
            return Err(VaultError::TransferFailed);
        }

        // 验证余额增加
        let balance_after = self.vault_balance()?;
        if balance_after != balance_before + assets {
            self.locked.set(false);
            return Err(VaultError::BalanceMismatch);
        }

        // 发出存款事件
        evm::emit(Deposit {
            user: msg::sender(),
            assets,
            shares,
            total_assets: balance_after,
            total_shares: total_shares + shares,
        })?;

        // 释放锁
        self.locked.set(false);
        Ok(shares)
    }

    /// 提取资产，销毁相应份额
    pub fn withdraw(&mut self, assets: U256) -> Result<U256, VaultError> {
        // 检查非重入锁
        if self.locked.get() {
            return Err(VaultError::Reentrancy);
        }
        self.locked.set(true);

        // 验证输入
        if assets == U256::ZERO {
            self.locked.set(false);
            return Err(VaultError::ZeroAmount);
        }
        let asset_addr = self.asset.get();
        if asset_addr == Address::ZERO {
            self.locked.set(false);
            return Err(VaultError::AssetNotSet);
        }

        // 获取当前余额
        let balance_before = self.vault_balance()?;
        if assets > balance_before {
            self.locked.set(false);
            return Err(VaultError::InsufficientAssets);
        }

        // 计算所需份额
        let total_assets = self.total_assets()?;
        let total_shares = self.total_shares.get();
        let shares = Self::calculate_shares(assets, total_assets, total_shares)?;
        let user_shares = self.erc20._balance_of(msg::sender());
        if shares > user_shares {
            self.locked.set(false);
            return Err(VaultError::InsufficientShares);
        }

        // 更新状态
        self.erc20._burn(msg::sender(), shares)?;
        self.total_shares.set(total_shares - shares);

        // 调用资产合约的 transfer
        let call_data = IERC20::transferCall {
            recipient: msg::sender(),
            amount: assets,
        }.abi_encode();
        let return_data = call::call(Call::new(), asset_addr, &call_data)?;
        let success = IERC20::transferCall::abi_decode(&return_data, true)
            .map(|result| result._0)
            .unwrap_or(false);
        if !success {
            self.locked.set(false);
            return Err(VaultError::TransferFailed);
        }

        // 验证余额减少
        let balance_after = self.vault_balance()?;
        if balance_before != balance_after + assets {
            self.locked.set(false);
            return Err(VaultError::BalanceMismatch);
        }

        // 发出提取事件
        evm::emit(Withdraw {
            user: msg::sender(),
            assets,
            shares,
            total_assets: balance_after,
            total_shares: total_shares - shares,
        })?;

        // 释放锁
        self.locked.set(false);
        Ok(assets)
    }

    /// 查询 Vault 的资产代币地址
    pub fn asset(&self) -> Result<Address, VaultError> {
        let asset_addr = self.asset.get();
        if asset_addr == Address::ZERO {
            return Err(VaultError::AssetNotSet);
        }
        Ok(asset_addr)
    }

    /// 查询 Vault 的总资产余额
    pub fn total_assets(&self) -> Result<U256, VaultError> {
        self.vault_balance()
    }

    /// 查询用户份额
    pub fn balance_of(&self, account: Address) -> Result<U256, VaultError> {
        Ok(self.erc20._balance_of(account))
    }

    /// 内部函数：计算份额
    fn calculate_shares(assets: U256, total_assets: U256, total_shares: U256) -> Result<U256, VaultError> {
        if total_assets == U256::ZERO {
            if total_shares != U256::ZERO {
                return Err(VaultError::DivideByZero); // 资产为零但份额非零，不一致
            }
            Ok(assets) // 初始 1:1 比例
        } else {
            assets.checked_mul(total_shares)
                .ok_or(VaultError::Overflow)?
                .checked_div(total_assets)
                .ok_or(VaultError::DivideByZero)
        }
    }

    /// 内部函数：查询 Vault 的资产余额
    fn vault_balance(&self) -> Result<U256, VaultError> {
        let asset_addr = self.asset.get();
        if asset_addr == Address::ZERO {
            return Err(VaultError::AssetNotSet);
        }
        let call_data = IERC20::balanceOfCall {
            account: contract::address(),
        }.abi_encode();
        let return_data = call::static_call(Call::new(), asset_addr, &call_data)?;
        let balance = IERC20::balanceOfCall::abi_decode(&return_data, true)
            .map(|result| result._0)
            .map_err(|_| VaultError::InvalidReturnData)?;
        Ok(balance)
    }
}