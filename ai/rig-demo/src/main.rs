use rig::client::{AgentClientExt, CompletionClient, ProviderClient};
use rig::completion::Prompt;
use rig::providers::openai;

#[tokio::main]
async fn main() -> Result<(), anyhow::Error> {
    // Create the OpenAI client from the OPENAI_API_KEY environment variable.
    let client = openai::Client::from_env()?;

    // Build an agent: a model plus a system prompt (the "preamble").
    let agent = client
        .agent("qwen3.7-max-2026-06-08")
        // .agent("gpt-5.5")
        .preamble("You are a helpful assistant.")
        .build();

    // Send a prompt and await the model's reply.
    let response = agent
        .prompt("What is the Rust programming language?")
        .await?;

    println!("{response}");

    Ok(())
}
