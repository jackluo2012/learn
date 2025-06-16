use anyhow::Result;
use clap::{ Parser};
use image::ImageFormat;
use std::path::Path;
use url::{Url};


// 声明  
mod web2image;
use web2image::web2image;
#[derive(Debug,Parser)]
#[command(name = "web2image")]
#[command(version = "1.0")]
#[command(about = "web cover image ", long_about = None)]
struct Cli {
    /// output file
    #[arg(short('o'),long,default_value = "./tmp/snapshot.png")]
    output: Option<String>,
    /// url to cpature
    #[arg(short('u'),long)]
    url: String,
}
//验证 后缀
fn get_image_format(path: &Path) -> Option<ImageFormat> {
    path.extension().and_then(|ext| {
        let ext = ext.to_str().unwrap().to_lowercase();
        match ext.as_str() {
            "jpg"=> Some(ImageFormat::Jpeg),
            "png"=> Some(ImageFormat::Png),
            "jpeg"=> Some(ImageFormat::Jpeg),
            _ => None,
        }
    })
}
// 验证url

fn validate_url(url: &str) -> bool {
    Url::parse(url).is_ok()
}



fn main() -> Result<(), anyhow::Error>{
    let cli = Cli::parse();
    println!("cli: {:?}", cli);
    let ouput = cli.output.unwrap();
    let path = Path::new(&ouput);
    let parent = path.parent().and_then(|p | p.is_dir().then(|| p));
    let ext = get_image_format(path);
    if parent.is_none() || ext.is_none() {
        println!("output dir not exists");
        return Err(anyhow::Error::msg("File path must be exists and file must be jpg  or png."))
    }
    if validate_url(&cli.url) == false {
        println!("url is invalid");
        return Err(anyhow::Error::msg("url is invalid"))
    }
    web2image::web2image(&cli.url, &ouput,ext.unwrap())?;

    Ok(())
    
}
