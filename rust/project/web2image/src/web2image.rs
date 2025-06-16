use anyhow::{Error, Ok, Result};
use image::imageops::overlay;
use image::{load_from_memory_with_format, DynamicImage, ImageFormat, Luma};
use std::fs;
use std::time::Instant;
use headless_chrome::Browser;
use headless_chrome::protocol::cdp::Page;
use qrcode::QrCode;
fn url2image(url: &str) -> Result<DynamicImage, anyhow::Error> {
    
    let start = Instant::now();
    
    let browser = Browser::default()?;    
    let tab = browser.new_tab()?;

    // Navigate to wikipedia
    tab.navigate_to(url)?;
    tab.wait_for_element("input#searchInput")?.click()?;

   // Type in a query and press `Enter`
   tab.type_str("WebKit")?.press_key("Enter")?;

   // We should end up on the WebKit-page once navigated
   let elem = tab.wait_for_element("#firstHeading")?;
   assert!(tab.get_url().ends_with("WebKit"));

    /// Take a screenshot of the entire browser window
    let data = tab.capture_screenshot(
        Page::CaptureScreenshotFormatOption::Png,
        None,
        None,
        true)?;
    ;
    println!("time spent on url2image: {}",start.elapsed().as_millis());
    Ok(load_from_memory_with_format(&data, ImageFormat::Png)?)

    
}
pub fn web2image(url: &str,output: &str,ext:ImageFormat) -> Result<(), anyhow::Error> { 

    let mut bottom = url2image(url)?;
    let qrcode = gen_qrcode(url)?;
    do_overlay(&mut bottom, &qrcode);

    bottom.save_with_format(output, ext)?;
    
    Ok(())

}


// 生成二维码
fn gen_qrcode(url: &str) -> Result<DynamicImage, anyhow::Error> { 

    // Encode some data into bits.
    let code = QrCode::new(url).unwrap();

    // Render the bits into an image.
    let buff = code.render::<Luma<u8>>().build();

    Ok(DynamicImage::ImageLuma8(buff))
}

fn do_overlay(bottom: &mut DynamicImage, top: &DynamicImage){ 
    let x = (bottom.width() - top.width() -10) as i64;
    let y = (bottom.height() - top.height() -10) as i64;
    overlay(bottom, top, x, y);
    
}