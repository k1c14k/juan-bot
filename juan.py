import os
from asyncio import sleep
from time import time

from tinydb import TinyDB, Query
import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands
from dotenv import load_dotenv


class BackgroundIntervalTask:
    def __init__(self, bot, interval):
        self.bot = bot
        self.interval = interval
        self.bot.loop.create_task(self.task())


    async def task(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self.coro()
            await sleep(self.interval)


    async def coro(self):
        pass


class DailyReminderTask(BackgroundIntervalTask):
    def __init__(self, bot, interval):
        super().__init__(bot, interval)

    async def coro(self):
        my_channel = config.get(Query().key == 'my-channel').get('value')
        channel = bot.get_channel(my_channel)
        reminders = daily_reminders.search(Query().next_reminder < time())
        for reminder in reminders:
            # send message "Hey @user, do you remember to do X?" to channel
            await channel.send(f'Hey <@{reminder["user_id"]}>, do you remember to do {reminder["what"]}?')
            # update next_reminder to next day
            daily_reminders.update({'next_reminder': time()+4000}, Query().id == int(reminder['id']))


if __name__ == '__main__':
    load_dotenv()
    db = TinyDB(os.getenv('DB_PATH'))
    tasks = db.table('tasks')
    users = db.table('users')
    config = db.table('config')
    daily_reminders = db.table('daily_reminders')

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

        # start the daily reminder task
        DailyReminderTask(bot, 60)  # check every minute


    # Command: respond to the !hello command
    @bot.slash_command(name="hello", description='Say hello to the bot', force_global=True)
    async def hello(interaction: Interaction):
        if interaction.permissions.administrator:
            await interaction.response.send_message('Hello, admin!', ephemeral=True)
        else:
            await interaction.response.send_message('Hello, user!', ephemeral=True)


    @bot.slash_command(name="setch", description='Set my_channel property in config', force_global=True)
    async def setch(interaction: Interaction, channel: nextcord.TextChannel):
        config.insert({'key': 'my-channel', 'value': channel.id})
        await interaction.response.send_message(f'my_channel set to {channel.name}', ephemeral=True)


    @bot.slash_command(name="getch", description='Get my_channel property from config', force_global=True)
    async def getch(interaction: Interaction):
        config_search = config.search(Query().key == 'my-channel')
        channel_id = config_search[0].get('value') if config_search else None
        if channel_id:
            channel = bot.get_channel(channel_id)
            if channel:
                await interaction.response.send_message(f'my_channel is {channel.name}', ephemeral=True)
            else:
                await interaction.response.send_message('my_channel is set but the channel was not found',
                                                        ephemeral=True)
        else:
            await interaction.response.send_message('my_channel is not set', ephemeral=True)


    @bot.slash_command(name="add_task", description='Add a new task', force_global=True)
    async def add_task(interaction: Interaction, when: str, what: str):
        my_channel = config.get(Query().key == 'my-channel').get('value')
        channel = bot.get_channel(my_channel)
        # check if user is in tasks
        user = users.get(Query().id == interaction.user.id)
        if user:
            msg = await channel.fetch_message(user['msg-id'])
            await msg.delete()
        tasks.insert({'user_id': interaction.user.id, 'when': when, 'what': what})
        user_tasks = tasks.search(Query().user_id == interaction.user.id)

        current_list = 'Twoje taski do wykonania:\n'
        for task in user_tasks:
            current_list += f'{task["when"]} - {task["what"]}\n'
        msg = await channel.send(current_list)
        user['msg-id'] = msg.id
        users.upsert(user, Query().id == interaction.user.id)
        await interaction.response.send_message('Task added', ephemeral=True)


    @bot.slash_command(name="daily_reminder", description='Set daily reminder list', force_global=True)
    async def daily_reminder(interaction: Interaction):
        pass


    @daily_reminder.subcommand(name="add", description='Add a new task to daily reminder list')
    async def daily_reminder_add(interaction: Interaction, when: int = SlashOption(description="When?"),
                                 what: str = SlashOption(description="What?")):
        last_id = daily_reminders.all()[-1].doc_id if daily_reminders.all() else 0
        daily_reminders.insert({'user_id': interaction.user.id, 'when': when, 'what': what, 'id': last_id + 1,
                                'next_reminder': time() - 1})
        await interaction.response.send_message('Task added to daily reminder list', ephemeral=True)


    @daily_reminder.subcommand(name="list", description='List daily reminder tasks')
    async def daily_reminder_list(interaction: Interaction):
        user_reminders = daily_reminders.search(Query().user_id == interaction.user.id)
        current_list = 'Twoje przypomnienia:\n'
        for reminder in user_reminders:
            current_list += f'#{reminder["id"]} {reminder["when"]} - {reminder["what"]}\n'
        await interaction.response.send_message(current_list, ephemeral=True)


    @daily_reminder.subcommand(name="remove", description='Remove a task from daily reminder list')
    async def daily_reminder_remove(interaction: Interaction, id: int = SlashOption(description="Id")):
        daily_reminders.remove(Query().id == id)
        await interaction.response.send_message('Task removed from daily reminder list', ephemeral=True)


    # Run the bot with the token from the Discord Developer Portal
    bot.run(os.getenv('DISCORD_TOKEN'))
