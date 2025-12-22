use anyhow::{Context, Result};
use zip::ZipArchive;
use std::path::{Path, PathBuf};
use std::fs::{self, File};
use std::io::{self, copy, Read};

/// 通达信日线数据记录
#[derive(Debug, Clone)]
pub struct DayRecord {
    date: u32,       // yyyymmdd
    open: u32,       // 开盘价 * 100
    high: u32,       // 最高价 * 100
    low: u32,        // 最低价 * 100
    close: u32,      // 收盘价 * 100
    amount: f32,     // 成交额
    vol: u32,        // 成交量
    reserved: u32,   // 保留字
}

/// 通达信数据管理器
pub struct TdxDataManager {
    pub download_url: String, // 下载地址
    pub workspace: PathBuf, // 工作目录
    pub zip_path: PathBuf, // 压缩包路径
    pub extract_path: PathBuf, // 解压目录
}

impl TdxDataManager {
    ///  初始化管理器
    pub fn new(url: String, workspace: &str) -> Self {
        Self {
            download_url: url,
            workspace: PathBuf::from(workspace),
            zip_path: PathBuf::from(workspace).join("hsjday.zip"),
            extract_path: PathBuf::from(workspace).join("data"),
        }
    }

    /// 从通达信服务器下载数据
    pub fn download_data(&self) -> Result<()> {
        // 创建工作目录
        if !self.workspace.exists() {
            fs::create_dir_all(&self.workspace)?;
        }
        /// 1. 下载
        println!("🚀 正在下载数据...");
        let mut response = reqwest::blocking::get(&self.download_url)
            .context("网络请求失败")?;
        let mut file = File::create(&self.zip_path)?;
        copy(&mut response, &mut file)?;
        Ok(())
    }
    
    /// 解压数据
    pub fn unzip_data(&self) -> Result<()> {
        // 2. 解压
        println!("🚀 正在解压数据...");
        let file = File::open(&self.zip_path)?;
        let mut archive = ZipArchive::new(file)?;

        for i in 0..archive.len() {
            let mut file = archive.by_index(i)?;
            
            // 处理Windows路径分隔符问题
            let file_name = file.mangled_name();
            let normalized_name = file_name.to_string_lossy().replace("\\", "/");
            let outpath = self.extract_path.join(Path::new(&normalized_name));
            
            println!("🚀 解压文件: {}", outpath.display());
            
            {
                let comment = file.comment();
                if !comment.is_empty() {
                    println!("File {i} comment: {comment}");
                }
            }

            if file.is_dir() {
                println!("Directory {} extracted to \"{}\"", i, outpath.display());
                fs::create_dir_all(&outpath)?;
            } else {
                println!(
                    "File {} extracted to \"{}\" ({} bytes)",
                    i,
                    outpath.display(),
                    file.size()
                );
                if let Some(p) = outpath.parent() {
                    if !p.exists() {
                        fs::create_dir_all(p)?;
                    }
                }
                let mut outfile = File::create(&outpath)?;
                io::copy(&mut file, &mut outfile)?;
            }

            // Get and Set permissions
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;

                if let Some(mode) = file.unix_mode() {
                    fs::set_permissions(&outpath, fs::Permissions::from_mode(mode))?;
                }
            }
        }
        
        println!("🚀 解压完成！");
        /// 3. 删除压缩包
        // fs::remove_file(&self.zip_path)?;
        Ok(())
    }

    /// 读取数据
    pub fn parse_day_file(&self, file_path: &Path) -> Result<Vec<DayRecord>> { 
        let mut file = File::open(file_path).context("无法打开文件")?;
        let mut buffer = [0u8; 32];
        let mut records = Vec::new();
        while file.read_exact(&mut buffer).is_ok() {
            records.push(DayRecord {
                // 使用 u32::from_le_bytes 将 4 字节切片转为小端序整数
                date: u32::from_le_bytes(buffer[0..4].try_into().unwrap()),
                open: u32::from_le_bytes(buffer[4..8].try_into().unwrap()),
                high: u32::from_le_bytes(buffer[8..12].try_into().unwrap()),
                low: u32::from_le_bytes(buffer[12..16].try_into().unwrap()),
                close: u32::from_le_bytes(buffer[16..20].try_into().unwrap()),
                // 注意金额是 f32
                amount: f32::from_le_bytes(buffer[20..24].try_into().unwrap()),
                vol: u32::from_le_bytes(buffer[24..28].try_into().unwrap()),
                reserved: u32::from_le_bytes(buffer[28..32].try_into().unwrap()),
            });            
        }
        
        println!("🚀 读取文件: {}", file_path.display());
        println!("🚀 读取记录数: {}", records.len());
        println!("🚀 读取记录: {:?}", &records[records.len() -1]);
        Ok(records)
        
    }
}

fn main() {
    let url = "http://tdx.gtimg.cn/fileftp/hq/list/v1/hsjday.zip";
    let workspace = "./tdx_data";
    let manager = TdxDataManager::new(url.to_string(), workspace);
    manager.download_data().unwrap();
    manager.unzip_data().unwrap();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_download_and_unzip() {
        let url = "https://data.tdx.com.cn/vipdoc/hsjday.zip";
        let workspace = "./tdx_data_test";
        let manager = TdxDataManager::new(url.to_string(), workspace);
        assert!(manager.download_data().is_ok());        
    }
    
    // 解压文件hsday.zip并读取其中的文件
    #[test]
    fn test_read_file_from_zip() {
        let url = "https://data.tdx.com.cn/vipdoc/hsjday.zip";
        let workspace = "./tdx_data_test";
        let manager = TdxDataManager::new(url.to_string(), workspace);
        manager.unzip_data().unwrap();
    }
    #[test]
    fn test_parse_day_file() {
        let url = "https://data.tdx.com.cn/vipdoc/hsjday.zip";
        let workspace = "./tdx_data_test";
        let manager = TdxDataManager::new(url.to_string(), workspace);
         
        let file_path = manager.extract_path.join("sh/lday/sh000001.day");
        let records = manager.parse_day_file(&file_path).unwrap();
        println!("Parsed {} records", records.len());
        assert!(!records.is_empty());
    }
}