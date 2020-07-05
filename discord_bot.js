
const Discord = require('discord.js');
const bot = new Discord.Client();
const bot_prefix = process.env.DISCORD_BOT_PREFIX || '!';

bot.on('ready', () => {
  console.log(`Logged in as ${bot.user.tag}!`);
  bot.user.setActivity(`${bot.user.username} is Deployed on Heroku!`, {type: 'PLAYING'});
});

bot.on('message', msg => {
	if (!msg.content.startsWith(bot_prefix))
		return;
  const command = msg.content.split(' ')[0].substr(bot_prefix.length);
  const args = msg.content.split(' ').slice(1).join(' ');
  if (command === 'ping') {
    msg.reply('Pong!');
  } else if (command === 'invite') {
  	msg.reply(process.env.DISCORD_BOT_INVITE);
  }
});

bot.login(process.env.DISCORD_BOT_TOKEN); //Bot Token
