import "dotenv/config";
import fetch from "node-fetch";
import { Client, GatewayIntentBits } from "discord.js";

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

const webhookUrl = process.env.N8N_WEBHOOK_URL;

client.once("ready", () => {
  console.log(`Logged in as ${client.user.tag}`);
});

client.on("messageCreate", async (message) => {
  if (message.author.bot) return;
  if (message.channel.name !== "add-tasks") return;
  console.log(`Message from ${message.author.username}: ${message.content}`);
  try {
    await fetch(webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: message.content,
        author: {
          id: message.author.id,
          username: message.author.username,
        },
        channel_id: message.channel.id,
        guild_id: message.guild.id,
        timestamp: message.createdTimestamp,
      }),
    });
  } catch (error) {
    console.error("Webhook error:", error);
  }
});

client.login(process.env.DISCORD_TOKEN);

