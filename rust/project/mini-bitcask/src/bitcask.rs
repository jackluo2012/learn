use fs4::fs_std::FileExt;
use std::{
    collections::btree_map,
    io::{BufReader, BufWriter, Read, Seek, SeekFrom, Write},
    ops::Bound,
    path::PathBuf,
};

const KEY_VAL_HEADER_LEN: u32 = 4;
const MERGE_FILE_EXT: &str = "merge";

type KeyDir = std::collections::btree_map::BTreeMap<u64, u32>;

pub type Result<T> = std::result::Result<T,std::io::Error>;
pub struct MiniBitcask {
    log:Log,
    key_dir:KeyDir,
}




impl Drop for MiniBitcask  {
    fn drop(&mut self) {
        if let Err(e) = self.flush(){
            log::error!("failed to flush file: {:?}",e);
        }
    }
}

impl MiniBitcask  {
    
    pub fn new(path:PathBuf) -> Result<Self> {
       let mut log = Log::new(path)?;
       let keydir = log.lod_index()?;
       Ok(Self { log, key_dir: keydir })
    }
    
    
    pub fn flush(&mut self) -> Result<()> {
        Ok(self.log.file.sync_all()?)        
    }
    pub fn set(&mut self, key: &[u8], value: Vec<u8>) -> Result<()> {
        let (offset, len) = self.log.write_entry(key, Some(&value))?;
        let value_len = value.len() as u32;
        self.keydir.insert(
            key.to_vec(),
            (offset + len as u64 - value_len as u64, value_len),
        );
        Ok(())
    }

    pub fn get(&mut self, key: &[u8]) -> Result<Option<Vec<u8>>> {
        if let Some((value_pos, value_len)) = self.keydir.get(key) {
            let val = self.log.read_value(*value_pos, *value_len)?;
            Ok(Some(val))
        } else {
            Ok(None)
        }
    }

    pub fn delete(&mut self, key: &[u8]) -> Result<()> {
        self.log.write_entry(key, None)?;
        self.keydir.remove(key);
        Ok(())
    }

    fn flush(&mut self) -> Result<()> {
        Ok(self.log.file.sync_all()?)
    }

    pub fn scan(&mut self, range: impl std::ops::RangeBounds<Vec<u8>>) -> ScanIterator<'_> {
        ScanIterator {
            inner: self.keydir.range(range),
            log: &mut self.log,
        }
    }

    pub fn scan_prefix(&mut self, prefix: &[u8]) -> ScanIterator<'_> {
        let start = Bound::Included(prefix.to_vec());

        // 最后一位加一，例如原始前缀是 "aaaa"，变为 "aaab"
        let mut bound_prefix = prefix.to_vec().clone();
        if let Some(last) = bound_prefix.iter_mut().last() {
            *last += 1;
        };
        let end = Bound::Excluded(bound_prefix.to_vec());

        self.scan((start, end))
    }
}



struct Log {
    path: PathBuf,
    file:std::fs::File,    
}


impl Log  {
    pub fn new(path:PathBuf) -> Result<Self> {
        if let Some(dir) = path.parent() {
            std::fs::create_dir_all(dir)?;
        }
        let file = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(path.clone())?;
        // 并发安全的文件锁
        file.try_lock_exclusive()?;
        Ok(Self { path, file })
    }
    // 加载索引
    pub fn lod_index(&mut self) -> Result<KeyDir> {
        let mut len_buf = [0u8; KEY_VAL_HEADER_LEN as usize];
        let mut keydir = KeyDir::new();
        let file_len = self.file.metadata()?.len();
        let mut r = BufReader::new(&self.file);
        let mut pos:u64 = r.seek(SeekFrom::Start(0))?;
        while pos < file_len {
            let read_one = || -> Result<(Vec<u8>, u64, Option<u32>)> {
                // 读取 key 的长度
                r.read_exact(&mut len_buf)?;
                let key_len = u32::from_be_bytes(len_buf);
                // 读取 value 的长度
                r.read_exact(&mut len_buf)?;
                let value_lent_or_tombstone = match i32::from_be_bytes(len_buf) {
                    l if l >= 0 => Some(l as u32),
                    _ => None,
                };

                // value 的位置
                
                let value_pos = pos + c as u64 * 2 + key_len as u64;

                // 读取 key 的内容
                let mut key = vec![0; key_len as usize];
                r.read_exact(&mut key)?;

                // 跳过 value 的长度
                if let Some(value_len) = value_lent_or_tombstone {
                    r.seek_relative(value_len as i64)?;
                }

                Ok((key, value_pos, value_lent_or_tombstone))
            }();

            match read_one {
                Ok((key, value_pos, Some(value_len))) => {
                    keydir.insert(key, (value_pos, value_len));
                    pos = value_pos + value_len as u64;
                }
                Ok((key, value_pos, None)) => {
                    keydir.remove(&key);
                    pos = value_pos;
                }
                Err(err) => return Err(err.into()),
            }
        }

        Ok(keydir)
    }
    // 根据 value 的位置和长度获取 value 的值
    fn read_value(&mut self, value_pos: u64, value_len: u32) -> Result<Vec<u8>> {
        let mut value = vec![0; value_len as usize];
        self.file.seek(SeekFrom::Start(value_pos))?;
        self.file.read_exact(&mut value)?;
        Ok(value)
    }

    // +-------------+-------------+----------------+----------------+
    // | key len(4)    val len(4)     key(varint)       val(varint)  |
    // +-------------+-------------+----------------+----------------+
    fn write_entry(&mut self, key: &[u8], value: Option<&[u8]>) -> Result<(u64, u32)> {
        let key_len = key.len() as u32;
        let value_len = value.map_or(0, |v| v.len() as u32);
        let value_len_or_tomestone = value.map_or(-1, |v| v.len() as i32);

        // 总共占据的长度
        let len = KEY_VAL_HEADER_LEN * 2 + key_len + value_len;

        let offset = self.file.seek(SeekFrom::End(0))?;
        let mut w = BufWriter::with_capacity(len as usize, &mut self.file);
        w.write_all(&key_len.to_be_bytes())?;
        w.write_all(&value_len_or_tomestone.to_be_bytes())?;
        w.write_all(key)?;
        if let Some(value) = value {
            w.write_all(value)?;
        }
        w.flush()?;

        Ok((offset, len))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn it_works() {
        let result = add(2, 2);
        assert_eq!(result, 4);
    }
}
