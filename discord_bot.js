
const Discord = require('discord.js');
const client = new Discord.Client();

client.on('ready', () => {
  console.log(`Logged in as ${client.user.tag}!`);
  client.user.setActivity('Deployed on Heroku', {type: 'PLAYING'});
});

client.on('message', msg => {
	if (!msg.content.startsWith(process.env.DISCORD_BOT_PREFIX))
		return;
  const command = msg.content.split(' ')[0].substr(process.env.DISCORD_BOT_PREFIX.length);
  const args = msg.content.split(' ').slice(1).join(' ');
  if (command === 'ping') {
    msg.reply('Pong!');
  } else if (command === 'invite') {
  	msg.reply(process.env.DISCORD_BOT_INVITE);
  }
});

client.login(process.env.DISCORD_BOT_TOKEN); //Bot Token
