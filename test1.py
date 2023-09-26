import discord
from discord.ext import commands, tasks
import asyncio
import json

channel_count=0


intents = discord.Intents.all()
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='%', intents=intents)

msg_count = {}  # Use a dictionary to store message counts for each user

# Load the guild-specific data
def load_guild_data():
    try:
        with open('storage.json', 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        return {}

# Save the guild-specific data
def save_guild_data(data):
    with open('storage.json', 'w') as file:
        json.dump(data, file, indent=4)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')

    for guild in bot.guilds:
        print(f"- {guild.name} (ID: {guild.id})")

    async def update_presence():
        while True:
            server_count = len(bot.guilds)
            await bot.change_presence(activity=discord.Game(name=f'Protecting {server_count} servers'))
            await asyncio.sleep(5)
            await bot.change_presence(activity=discord.Game(name='Run %init to set up the bot'))
            await asyncio.sleep(5)

    bot.loop.create_task(update_presence())

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Sorry, that command doesn't exist.")



@bot.command()
async def invite(ctx):
    await ctx.send('You can protect more servers with me!: https://discord.com/api/oauth2/authorize?client_id=1146227673690025997&permissions=8&scope=bot')

@bot.command()
async def debug(ctx):
    await ctx.send(f'Bot is in ` {len(bot.guilds)} servers `')
    await ctx.send(f'Latency is ` {round(bot.latency * 1000)}ms `')
    await ctx.send(f"Running on discord.py version: ` {discord.__version__} `")

    
@bot.command()
async def run(ctx):
    await ctx.send("There are currently no experiments")
# Lets handle errors if something fails

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please pass in all required arguments")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("I don't have permission to use this command")
    else:
        await ctx.send(f"An error occurred: `{str(error)}`") 

@bot.command()
async def kick(ctx, member: discord.Member, *, reason=None):
    print(f'Kicking {member} for reason: {reason}')  # Debug print
    if member == ctx.author:
        await ctx.send("You can't kick yourself")
        return
    if not ctx.author.guild_permissions.kick_members:
        await ctx.send("You don't have permission to kick members")
        return
    await member.kick(reason=reason)
    await ctx.send(f'{member} has been kicked')

@bot.command()
async def ban(ctx, member: discord.Member, *, reason=None):
    print(f'Banning {member} for reason: {reason}')  # Debug print
    if member == ctx.author:
        await ctx.send("You can't ban yourself")
        return
    if not ctx.author.guild_permissions.ban_members:
        await ctx.send("You don't have permission to ban members")
        return
    await member.ban(reason=reason)
    await ctx.send(f'{member} has been banned')
    
# Lets make it so when the bot is kicked it will wipe the data
@bot.event
async def on_guild_remove(guild):
    guild_data = load_guild_data()
    guild_id = guild.id

    if str(guild_id) in guild_data:
        del guild_data[str(guild_id)]
        save_guild_data(guild_data)

@bot.command()
async def init(ctx):
    # Load the guild-specific data
    guild_data = load_guild_data()

    # Get the guild ID
    guild_id = ctx.guild.id

    # Check if the bot has already been initialized for this guild
    if str(guild_id) not in guild_data:
        # Store the ID of the user who initialized the bot
        guild_data[str(guild_id)] = {
            "lockdown": False,
            "link_blocker": False,
            "spam_blocker": False,
            "raid_blocker": False,
            "chat_filter": False,
            "blacklist": [],
            "initiator_id": [ctx.author.id]  # Store the ID of the user who initialized the bot
        }

        # Save the updated data back to storage.json
        save_guild_data(guild_data)

        await ctx.send("Initialization complete. Values set to default. You can now use the =menu")
    else:
        await ctx.send("Guild data already exists. You don't need to initialize it again.")

@bot.command()
async def menu(ctx):
    guild_data = load_guild_data()
    guild_id = ctx.guild.id

    if str(guild_id) not in guild_data:
        await ctx.send("You are not in storage. Please set up with %init")
        return
    # Lets update it to have if its active or not
    embed = discord.Embed(
        title=f"Protection Menu",
        description=f"""
        Anti Spam - Blocks spam:
        --Toggle: %spam
        --Status: {("Active ✅ " if guild_data[str(guild_id)]["spam_blocker"] else "Inactive 🚫")}

        Anti Link - Blocks links :
        --Toggle: %link 
        --Status: {("Active ✅ " if guild_data[str(guild_id)]["link_blocker"] else "Inactive 🚫")}

        Anti Raid - Kicks members who join during a raid:
        --Toggle: %raid
        --Status: {("Active✅ " if guild_data[str(guild_id)]["raid_blocker"] else "Inactive 🚫")}

        Anti Nuke - Prevent your server from being nuked:
        --Toggle: %nuke
        --Status: {("Active ✅ " if guild_data[str(guild_id)]["lockdown"] else "Inactive 🚫")}

        Anti Nuke Featueres:
        --Detects if a user/bot is getting dangerous permissions 
        --Detects if a user is likly nuking
        --Removes spam messages

        Chat Filter - Prevents members from saying swear words:
        --Toggle: %chat
        --Status: {("Active ✅ " if guild_data[str(guild_id)]["chat_filter"] else "Inactive 🚫")}

        Blacklisted Terms:
        --Add: %addblacklist
        --Remove: %removeblacklist

        Initiator -- Lets you add more people who can use the bot protection tools:
        --Add: %addinitiator

        Use the commands to toggle the protection on and off.
        """,
        color=discord.Color.blue()
    )

    # Send the embed to the channel
    await ctx.send(embed=embed)

# Lets rewrite the is_initiator function to check if the user is in the list of initiators

def is_initiator(ctx):
    # Lets check if the user is in the list of initiators
    guild_data = load_guild_data()
    guild_id = ctx.guild.id

    # Lets check with a for loop
    for initiator_id in guild_data[str(guild_id)]["initiator_id"]:
        if ctx.author.id == initiator_id:
            return True
    

@bot.command()
@commands.check(is_initiator)
async def spam(ctx):
    guild_data = load_guild_data()
    guild_id = ctx.guild.id

    if str(guild_id) not in guild_data:
        await ctx.send("You are not in storage. Please set up with %init")
        return

    # Set initial values or update existing ones
    if guild_data[str(guild_id)]["spam_blocker"]:
        guild_data[str(guild_id)]["spam_blocker"] = False
        await ctx.send("Spam blocker disabled")
    else:
        guild_data[str(guild_id)]["spam_blocker"] = True
        await ctx.send("Spam blocker enabled")

    # Save the updated data back to storage.json
    save_guild_data(guild_data)


@bot.command()
@commands.check(is_initiator)
async def chat(ctx):
    guild_data = load_guild_data()
    guild_id = ctx.guild.id

    if str(guild_id) not in guild_data:
        await ctx.send("You are not in storage. Please set up with %init")
        return

    # Set initial values or update existing ones
    if guild_data[str(guild_id)]["chat_filter"]:
        guild_data[str(guild_id)]["chat_filter"] = False
        await ctx.send("Chat filter disabled")
    else:
        guild_data[str(guild_id)]["chat_filter"] = True
        await ctx.send("Chat filter enabled")

    # Save the updated data back to storage.json
    save_guild_data(guild_data)

@bot.command()
@commands.check(is_initiator)
async def link(ctx):
    guild_data = load_guild_data()
    guild_id = ctx.guild.id

    if str(guild_id) not in guild_data:
        await ctx.send("You are not in storage. Please set up with %init")
        return

    # Set initial values or update existing ones
    if guild_data[str(guild_id)]["link_blocker"]:
        guild_data[str(guild_id)]["link_blocker"] = False
        await ctx.send("Link blocker disabled")
    else:
        guild_data[str(guild_id)]["link_blocker"] = True
        await ctx.send("Link blocker enabled")

    # Save the updated data back to storage.json
    save_guild_data(guild_data)

#Lets make it so the initiator can add more people who can use the bot
@bot.command()
@commands.check(is_initiator)
async def addinitiator(ctx, member: discord.Member):
    guild_data = load_guild_data()
    guild_id = ctx.guild.id

    if str(guild_id) not in guild_data:
        await ctx.send("You are not in storage. Please set up with %init")
        return
        
    # Lets check if the member is already in the list of initiators 
    for initiator_id in guild_data[str(guild_id)]["initiator_id"]:
        if member.id == initiator_id:
            await ctx.send("This member is already in the list of initiators")
            return

    # Add the member to the list of initiators
    guild_data[str(guild_id)]["initiator_id"].append(member.id)

    # Save the updated data back to storage.json
    save_guild_data(guild_data)

    await ctx.send(f"Added {member} to the list of initiators")

@bot.command()
async def credits(ctx):
    embed = discord.Embed(title="Credits", description="Created by Infdev \n Help from gon \n Lolbot for suggesting features that were already implemented or were being implemented", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command()
@commands.check(is_initiator)
async def raid(ctx):
    guild_data = load_guild_data()
    guild_id = ctx.guild.id

    if str(guild_id) not in guild_data:
        await ctx.send("You are not in storage. Please set up with %init")
        return

    # Set initial values or update existing ones
    if guild_data[str(guild_id)]["raid_blocker"]:
        guild_data[str(guild_id)]["raid_blocker"] = False
        await ctx.send("Raid blocker disabled")
    else:
        guild_data[str(guild_id)]["raid_blocker"] = True
        await ctx.send("Raid blocker enabled, join punishment of: Kick")

    # Save the updated data back to storage.json
    save_guild_data(guild_data)

@bot.command()
@commands.check(is_initiator)
async def nuke(ctx):
    guild_data = load_guild_data()
    guild_id = str(ctx.guild.id)

    if guild_id not in guild_data:
        await ctx.send("You are not in storage. Please set up with %init")
        return


    # Set initial values or update existing ones
    # Lets make it to that if the lockdown is on, it will turn off
    if guild_data[guild_id]["lockdown"] == True:
        guild_data[guild_id]["lockdown"] = False
        await ctx.send("Nuke protection disabled")
    else:
        guild_data[guild_id]["lockdown"] = True
        await ctx.send("Nuke protection enabled")


    # Save the updated data back to storage.json
    save_guild_data(guild_data)




@bot.event
async def on_member_join(member):
    # Let's check if anti-raid or lockdown is on
    guild_data = load_guild_data()
    guild_id = member.guild.id

    # Ensure the guild ID is in guild_data and that it has the necessary keys
    if str(guild_id) in guild_data:
        # Lets kick the user if their in the blacklist 

        

        raid_blocker_enabled = guild_data[str(guild_id)].get("raid_blocker", False)
        lockdown_enabled = guild_data[str(guild_id)].get("lockdown", False)

        if raid_blocker_enabled:
            await member.send("You were kicked for joining during a lockdown/anti raid. Please retry at a later date")
            await member.kick(reason="Auto kick during lockdown/anti raid")
            # Now let's DM the member to explain
    else:
       pass

@bot.command()
@commands.check(is_initiator)
async def addblacklist(ctx, *, word):
    guild_data = load_guild_data()
    guild_id = ctx.guild.id

    if str(guild_id) not in guild_data:
        await ctx.send("You are not in storage. Please set up with %init")
        return

    # Add the word to the blacklist
    guild_data[str(guild_id)]["blacklist"].append(word)

    # Save the updated data back to storage.json
    save_guild_data(guild_data)

    await ctx.send(f"Added {word} to the blacklist")


@bot.command()
@commands.check(is_initiator)
async def removeblacklist(ctx, *, word):
    guild_data = load_guild_data()
    guild_id = ctx.guild.id

    if str(guild_id) not in guild_data:
        await ctx.send("You are not in storage. Please set up with %init")
        return

    # Remove the word from the blacklist
    guild_data[str(guild_id)]["blacklist"].remove(word)

    # Save the updated data back to storage.json
    save_guild_data(guild_data)

    await ctx.send(f"Removed {word} from the blacklist")

# Lets check for if a channel is made

# Lets make the updater
@tasks.loop(seconds=5)
async def update_data():
    channel_count = 0
    channel_count_del = 0

@tasks.loop(seconds=2)
async def update_data_fast():
    ping_count = 0

# Lets make a event for if a channel is made and lets use asyncio to see if a channel is being created in this span (Channels created > 2 in 5 seconds)
@bot.event
async def on_guild_channel_create(channel):
    global channel_count
    # Lets implement the anti spam channel creation

    # Lets check if the anti nuke is on

    guild_data = load_guild_data()
    guild_id = channel.guild.id

    if guild_data.get(str(guild_id), {}).get("lockdown", False):
        return

    channel_count = channel_count + 1

    if channel_count > 2:
        # Lets kick the user immediately for spamming

      
        await channel.author.kick(reason=" Sec2 | Auto kick for spamming channel creation")

        anti_nuke_amount = anti_nuke_amount + 1
        save_stats()

        channel_count = 0
        

# Lets now check if a channels being deleted

@bot.event
async def on_guild_channel_delete(channel):
    if (channel.author == bot.user):
        return

    # If anti nuke is off, lets return
    
    guild_data = load_guild_data()

    guild_id = channel.guild.id

    if guild_data.get(str(guild_id), {}).get("lockdown", False):
        return
    
    verified_bot = message.author.public_flags.verified_bot

    if (verified_bot == True):
        return

    message.author.kick(reason="Unverified bot pinging")
    
    channel_count_del = channel_count_del + 1

    if (channel_count_del > 2):
        await channel.author.kick(reason="Sec2 | Auto kick for spamming channel deletion")

        anti_nuke_amount = anti_nuke_amount + 1
        save_stats()

        channel_count_del = 0

@bot.event
async def on_message(message):
    if (message.author == bot.user):
        return
    try:
        # Allow commands to be processed
        await bot.process_commands(message)
        
        guild_data = load_guild_data()
        guild_id = message.guild.id



        # Let's check if the bot is in anti nuke mode
        if guild_data.get(str(guild_id), {}).get("lockdown", False):
            # Lets see if the count of pings is greater than 5

            # Lets remake this but for onmessage is_verified_bot = bot_member.public_flags.verified_bo

            verified_bot = message.author.public_flags.verified_bot

            if (verified_bot == True):
                return

            message.author.kick(reason="Unverified bot pinging")
            
               

        # Lets check if the message contains any blacklisted words
        for word in guild_data.get(str(guild_id), {}).get("blacklist", []):
            if word in message.content.lower():
                await message.delete()
                await message.channel.send("You cannot say that word here")
                return

        # Lets check if the chat filter is on
        if guild_data.get(str(guild_id), {}).get("chat_filter", False):
            # Lets get a list of blacklisted words from a csv file
            with open("blacklist.txt") as file:
                blacklist = file.read().splitlines()
            # Now let's check if the message contains any blacklisted words
            for word in blacklist:
                if word in message.content.lower():
                    await message.delete()
                    await message.channel.send("You cannot say that word here")
                    return



        # Let's check for spam
        if guild_data.get(str(guild_id), {}).get("spam_blocker", False):
            author_id = str(message.author.id)
            msg_count[author_id] = msg_count.get(author_id, 0) + 1
            if msg_count[author_id] > 5:
                # Let's delete the spam messages
                await message.delete()
                await message.channel.send("Please stop spamming")
                return

        # Let's check for links
        if guild_data.get(str(guild_id), {}).get("link_blocker", False):
            if "http" in message.content:
                await message.delete()
                await message.channel.send("You cannot send links in this server")
                anti_link_amount = anti_link_amount + 1
                save_stats()
                return
    except Exception as e:
        print(f"An error occurred: {str(e)}")

anti_link_amount = 0
anti_nuke_amount = 0

stats_form = {
    "Stopped-nukes": (anti_nuke_amount),
    "Stopped-links": (anti_link_amount),
}
def save_stats(file_name='stats.json'):
    with open(file_name, 'w+') as f:
        # Lets write the stats to the file if its not already there
        json.dump(stats_form, f)
        


@bot.event
#Lets check if anyone is getting danerorus permissions
async def on_member_update(before, after):
    # Lets check if anti nuke is on
    guild_data = load_guild_data()
    guild_id = after.guild.id
    # Lets check if the server is in storage
    if str(guild_id) in guild_data:
        
       if guild_data.get(str(guild_id), {}).get("lockdown", False):
        # Lets check to see if the person responsible for the change is the owner
        if after.guild.owner == after:
            return
        # Lets check if the user is getting dangerous permissions
        if before.guild_permissions.administrator == False and after.guild_permissions.administrator == True:
            # Lets kick the user immediately for being a nuke
            await after.kick(reason="Auto kick for getting dangerous permissions")
            # Lets tell the guild owner that the user was kicked
            await after.guild.owner.send(f"{after} was kicked for getting dangerous permissions. This was done via the anti nuke feature")
            save_guild_data(type)
            
with open("config.js") as token_file:
    eval(token_file.read())
    # js file lol


bot.run(token)

