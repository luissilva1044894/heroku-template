
const tmi = require('tmi.js');

// Define configuration options
const opts = {
  identity: {
    username: process.env.TWITCH_BOT_USERNAME,
    password: process.env.TWITCH_BOT_OAUTH_TOKEN
  },
  channels: (process.env.TWITCH_BOT_INITIALS_CHANNELS || '').split(',')
};

const client = new tmi.client(opts);

client.on('message', onMessageHandler);
client.on('connected', onConnectedHandler);

function onMessageHandler() {

}

function onConnectedHandler(addr, port) {
  console.log(`* Connected to ${addr}:${port}`);
}

client.connect();
