fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::configure().
    out_dir(
        "src/pb", // Output directory for generated code
    ).
    compile_protos(&["proto/helloworld.proto"], &["proto"])?;
    Ok(())
}
