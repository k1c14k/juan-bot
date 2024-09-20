import os

import nextcord
from nextcord import Interaction
from nextcord.ext import commands
from dotenv import load_dotenv

from util import read_config, save_config

if __name__ == '__main__':
    load_dotenv()
    config = read_config()
    tasks = {}

    # Set up the bot with a command prefix, e.g., "!"
    intents = nextcord.Intents(message_content=True, guilds=True)
    # intents.message_content = True
    bot = commands.Bot(command_prefix='!', intents=intents)


    # Event: when the bot is ready and connected to Discord
    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user}')
        try:
            synced = await bot.sync_application_commands()
            print(f'Synced commands: {synced}')
        except Exception as e:
            print(f'Error syncing commands: {e}')


    # Command: respond to the !hello command
    @bot.slash_command(name="hello", description='Say hello to the bot', force_global=True)
    async def hello(interaction: Interaction):
        if interaction.permissions.administrator:
            await interaction.response.send_message('Hello, admin!', ephemeral=True)
        else:
            await interaction.response.send_message('Hello, user!', ephemeral=True)


    @bot.slash_command(name="setch", description='Set my_channel property in config', force_global=True)
    async def setch(interaction: Interaction, channel: nextcord.TextChannel):
        config['my_channel'] = channel.id
        await interaction.response.send_message(f'my_channel set to {channel.name}', ephemeral=True)


    @bot.slash_command(name="getch", description='Get my_channel property from config', force_global=True)
    async def getch(interaction: Interaction):
        channel_id = config.get('my_channel')
        if channel_id:
            channel = bot.get_channel(channel_id)
            if channel:
                await interaction.response.send_message(f'my_channel is {channel.name}', ephemeral=True)
            else:
                await interaction.response.send_message('my_channel is set but the channel was not found',
                                                        ephemeral=True)
        else:
            await interaction.response.send_message('my_channel is not set', ephemeral=True)


    @bot.slash_command(name="save", description='Save the current config to file', force_global=True)
    async def save(interaction: Interaction):
        save_config(config)
        await interaction.response.send_message('Configuration saved', ephemeral=True)


    @bot.slash_command(name="add_task", description='Add a new task', force_global=True)
    async def add_task(interaction: Interaction, when: str, what: str):
        # check if user is in tasks
        if interaction.user.id not in tasks:
            tasks[interaction.user.id] = {}
        if 'msg-id' in tasks[interaction.user.id]:
            # remove previous message
            channel = bot.get_channel(config.get('my_channel'))
            msg = await channel.fetch_message(tasks[interaction.user.id]['msg-id'])
            await msg.delete()
        if 'tasks' not in tasks[interaction.user.id]:
            tasks[interaction.user.id]['tasks'] = []
        tasks[interaction.user.id]['tasks'].append({'when': when, 'what': what})

        current_list = 'Twoje taski do wykonania:\n'
        for idx, task in enumerate(tasks[interaction.user.id]['tasks']):
            current_list += f'{idx + 1}. {task["when"]} - {task["what"]}\n'
        channel = bot.get_channel(config.get('my_channel'))
        msg = await channel.send(current_list)
        tasks[interaction.user.id]['msg-id'] = msg.id
        await interaction.response.send_message('Task added', ephemeral=True)

# Run the bot with the token from the Discord Developer Portal
    bot.run(os.getenv('DISCORD_TOKEN'))
