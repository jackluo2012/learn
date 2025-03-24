use std::fs::{read, File, OpenOptions};
use std::io::{BufRead, BufReader, Seek, Write};
#[derive(Clone)]
pub struct Record {
    pub id: i32,
    pub content: String,
}
pub struct Database {
    pub file: File,
}
pub fn parse_record_line(line: &str) -> Record {
    let parts: Vec<&str> = line.split(',').collect();
    // 处理为空的情况 
    if parts.len() == 1 {
        return Record {
            id: 0,
            content: "".to_string(),
        };
    };
    let content = parts[1..].join(",");
    Record { id: parts[0].parse::<i32>().unwrap(), content }
}
impl Database {
    pub fn open(filename: &str) -> Database {
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .open(filename).unwrap();
        Database { file }
    }
    pub fn add_record(&mut self, record: &Record) {
        let line = format!("{},{}\n", record.id,record.content);
        writeln!(&mut self.file, "{}", line).unwrap();
        println!("📝 Item added: {}", record.content); 
    }
    pub fn read_records(&self) -> Vec<Record> {
        let reader: BufReader<&File> = BufReader::new(&self.file);
        //直接 返回 一个vec<Record>
        reader.lines()
            .filter_map(|line| line.ok())
            .filter(|line| !line.is_empty())
            .map(|line| parse_record_line(&line))
            .collect()
    }
    pub fn remove_record(&mut self, id: i32) {
        let records = self.read_records();
        let filtered_records: Vec<Record> = records.iter()
            .filter(|record| record.id != id)
            .cloned()
            .collect();
        
        // 检查记录是否被删除，若未删除则直接返回
        if filtered_records.len() == records.len() {
            return;
        }
        
        // 使用expect代替unwrap，并添加错误信息描述
        self.file.set_len(0).expect("Failed to truncate file");
        self.file.seek(std::io::SeekFrom::Start(0)).expect("Failed to seek to start of file");
        for record in filtered_records {
            self.add_record(&record);
        }
        
        // 仅当实际删除记录时才打印成功消息
        println!("🗑️ Item removed: {}", id);
    }
}