import { address } from "@solana/kit";
import { createClient } from "./client";

tutorial();
async function tutorial(){
    const client = createClient();
    const account = address("AEav14XC2m11X5F6iBRrmK7cu8L2GhD9A2QGzGUDfLYD")
    const  {value:balance} = await client.rpc.getTokenAccountBalance(account).send();

    console.log(`Balance: ${balance} lamports.`);
}