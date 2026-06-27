import discord,logging,os,platform,sys,time,re,requests,json;
from discord import app_commands;
from discord.ext import commands;
from discord.ui import View, Select;
from discord.ext.commands import MemberConverter;
from datetime import datetime, timedelta;
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

log = logging.getLogger("SuperDuperBot")
bot_version="5.5.7";
def is_windows_terminal():
    return "WT_SESSION" in os.environ;  # Windows Terminal sets this environment variable
##end
if os.name=="nt":
    if not is_windows_terminal():
        import ctypes;
        kernel32 = ctypes.windll.kernel32;
        handle = kernel32.GetStdHandle(-11);  # STD_OUTPUT_HANDLE
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004;
        mode = ctypes.c_ulong();
        kernel32.GetConsoleMode(handle, ctypes.byref(mode));
        kernel32.SetConsoleMode(handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING);
    ##endif
##endif
token = os.environ.get("TOKEN");
if token is None:
    token=input("Enter bot auth pls: ");
##endif
#Bot User agent
user_agent=f"SuperDuperBot/{bot_version} ({platform.system()} {platform.release()}) Python/{platform.python_version()} Requests/{requests.__version__} (compatible: SuperDuperBot [{platform.machine()}])";
#Bot owner
owner_user=os.environ.get("OWNER");
if owner_user is None:
    owner_user=input("Enter the bot owner's username: ");
# trusteds
trusted_users=[];
# Event Webservice URL
webservice_url=os.environ.get("WEBSERVICE_URL");
# Event Webservice Auth token
sitoken=os.environ.get("SIWEB_AUTH");
if sitoken is None:
    sitoken=input("Provide a SIWeb Auth token (required for event functionality): ");
##endif
# Intents
intents = discord.Intents.default();
intents.message_content = True;
intent_cmd_prefix='!';
logs_dir = "logs";
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir);
##endif
def append_json_field(file_path, data):
    """Appends a new entry to a JSON file.""";
    if not os.path.exists(file_path):
        with open(file_path, "w") as file:
            json.dump([], file);
        ##endwith
    ##endif
    with open(file_path, "r") as file:
        try:
            json_content=json.load(file);
        except json.JSONDecodeError:
            json_content=[];
        ##endtry
    ##endwith
    # Append new data
    json_content.append(data);
    # Write back to the file
    with open(file_path, "w") as file:
        json.dump(json_content, file, indent=4);
    ##endwith
    return True;  # Confirm successful write
##end
def print_err(e):
    log.info(f"\033[1;31m[ ERROR ]: {e}\033[0m"); #red
##end
def print_warn(e):
    log.info(f"\033[1;33m[ WARNING ]: {e}\033[0m"); #yellow
##end
def print_debug2(e):
    log.info(f"\033[95m[ DEBUG ]: {e}\033[0m"); # purple2
##end
def print_debug(e):
    log.info(f"\033[35m[ DEBUG ]: {e}\033[0m"); # purple1
##end
def print_info2(e):
    log.info(f"\033[1;34m[ INFO ]: {e}\033[0m"); #blue
##end
def print_info(e):
    log.info(f"[ INFO ]: {e}"); #white
##end
def sendRequest(url,auth):
    heads={
        "User-Agent":user_agent,
        "Authorization":f"Bearer {auth}",
        "Content-Type":"application/json",
        "Accept":"application/json",
        "X-Request-Sent":str(time.time()),
    };
    try:
        response = requests.get(url,headers=heads);
        response.raise_for_status();
    except requests.exceptions.HTTPError as http_err:
        print_err(f"Request to {url} failed with response code {response.status_code} (HTTP: {http_err})");
        return None;
    except Exception as err:
        print_err(err);
        return None;
    else:
        print_info(f"Request to {url} succeeded with response code {response.status_code}")
        return response.json();
    ##endtry
##end
def sendPostRequest(url,auth,content):
    heads={
        "User-Agent":user_agent,
        "Authorization":f"Bearer {auth}",
        "Content-Type":"application/json",
        "Accept":"application/json",
        "X-Request-Sent":str(time.time()),
    };
    try:
        response=requests.post(url,headers=heads,json=content);
        response.raise_for_status(); 
    except requests.exceptions.HTTPError as http_err:
        print_err(f"Request to {url} failed with response code {response.status_code} (HTTP: {http_err})");
        return None;
    except Exception as err:
        print_err(err);
        return None;
    else:
        print_info(f"Request to {url} succeeded with response code {response.status_code}")
        return response.json();  # Assuming the response is in JSON format
    ##endtry
##end
def restart_bot():
    print_info2("Restarting Bot...");
    print_warn("User ID may change after restart! If this happens, reset the bot token IMMEDIATELY to avoid service disruption.");
    os.execv(sys.executable, ['python'] + sys.argv);  # Restart the bot
##end
# Bot setup
bot = commands.Bot(command_prefix=intent_cmd_prefix, intents=intents);
@bot.event
async def on_ready():
    print_warn(f'Logged in as {bot.user} (ID: {bot.user.id})');
    print_warn(f'Connected to {len(bot.guilds)} guild(s)');
    print_debug2(f"Bot User-Agent -> {user_agent}");
    print('------------------------------------');
    try:
        synced = await bot.tree.sync();
        print_info(f"Synced {len(synced)} commands");
    except Exception as e:
        print(f"Failed to sync commands: {e}");
    ##endtry
##end

@bot.event
async def on_automod_action(action: discord.AutoModAction):
    """Responds dynamically to AutoMod triggers based on custom rules."""
    rule_name = action.rule_name.lower();
    await action.channel.send(f"🚨 **AutoMod triggered:** `{rule_name}` by {action.member.mention}.");
    """if rule_name in rules["rules"]:
        rule = rules["rules"][rule_name];
        if rule["action"] == "delete":
            await action.message.delete();
        ##endif
        if rule["notify"]:
            await action.channel.send(f"🚨 **AutoMod triggered:** `{rule_name}` by {action.member.mention}.");
        ##endif
        if rule["punishment"] == "timeout":
            await action.member.timeout(duration=rule["duration"]);
        ##endif
    ##endif
    """;
##end
@bot.event
async def on_message(message):
    if message.author.bot:
        return;  # Ignore bot messages
    ##endif
    try:
        if message.guild:
            log_entry = {
                "server": message.guild.id,
                "channel": message.channel.id,
                "author": message.author.id,
                "content": message.content,
                "timestamp": message.created_at.isoformat(),
            };
            # Append to a JSON file for logging
            append_json_field(f"{logs_dir}/{message.guild.id}_messages.json",log_entry);
        else:
            print_info2("DM detected, will not log messages");
        ##endif
    except Exception as e:
        print_err(f"Error writing log: {e}");
    ##endtry
    await bot.process_commands(message);  # Continue processing commands
##end
class AutoModConfigView(View):
    def __init__(self,interaction: discord.Interaction):
        super().__init__();
        self.interaction=interaction;
        self.opt=[];
    ##end
    async def initialize(self):
        rules=await self.getRules(self.interaction);
        if rules:
            for rule in rules:
                self.opt.append(discord.SelectOption(label=rule,value=rule));
            ##end
        else:
            self.opt=[discord.SelectOption(label="Default",value="def")];
        ##end
        self.select=Select(
            placeholder="Select Automod Flags",
            options=self.opt
        );
        self.select.callback = self.handle_selection;
        self.add_item(self.select);
        return None;
    ##end
    async def getRules(self,interaction):
        guild = interaction.guild;
        rules = await guild.fetch_auto_moderation_rules();
        return rules;
    ##end
    async def handle_selection(self,interaction: discord.Interaction):
        selected_flags = self.select.values;
        embed = discord.Embed(
            title="Automod Configuration Updated",
            description=f"Enabled flags: {', '.join(selected_flags)}",
            color=discord.Color.green()
        );
        await interaction.response.edit_message(embed=embed, view=None);
    ##end
##end
""" BEGIN COMMMANDS """
@bot.tree.command(name="hello", description="Says hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message('Hello!');
##end
""" BEGIN DEV COMMANDS """
@bot.command(help="Restarts the bot")
async def restart(ctx):
    if str(ctx.author) == owner_user:
        await ctx.reply("Restarting bot...");
        restart_bot();
    else:
        await ctx.reply("Only the bot owner can restart the bot");
    ##endif
##end
@bot.command()
async def funny_help(ctx):
    """Opens the Python interactive help utility in the bot's console.""";
    if str(ctx.author) == owner_user or str(ctx.author) in trusted_users:
        await ctx.reply("Python help utility opened in the bot's console!");
        os.system("python -c help()");
    else:
        await ctx.reply("You do not have permission to use this command.");
    ##endif
##end
@bot.command()
async def create_command_log(ctx):
    """Generates a command log for this server (Owner-only).""";
    if str(ctx.author) == owner_user or str(ctx.author) in trusted_users:
        command_log = {"server": ctx.guild.id, "commands": []};
        async for message in ctx.channel.history(limit=100):  # Logs recent commands
            if message.content.startswith(intent_cmd_prefix):
                command_log["commands"].append(message.content);
            ##endif
        ##end
        with open(f"{logs_dir}/{ctx.guild.id}_command_log.json", "w") as file:
            json.dump(command_log, file, indent=4);
        ##endwith
        print_debug2("Generating command log...");
        await ctx.reply("Command log created! Check the bot’s logs folder.");
    else:
        await ctx.reply("You do not have permission to create a command log.");
    ##endif
##end
@bot.tree.command(name="restart", description="Restarts the bot")
async def restart_slash(interaction: discord.Interaction):
    if str(interaction.user)==owner_user:
        await interaction.response.send_message("Restarting bot...");
        restart_bot();
    else:
        await interaction.response.send_message("Only the bot owner can restart the bot");
    ##endif
##end
""" END DEV COMMANDS """
@bot.command()
async def logs(ctx, amount: int = 100):
    """Saves the last [amount] messages to a temporary log file and sends it to moderators."""
    try:
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.reply(f"Command cannot be run outside of a server `--logs 002--`")
            return;
        ##endif
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.reply("You do not have permission to retrieve logs. `--logs 003--`");
            return;
        ##endif
        file_path = f"{logs_dir}/logs.json"
        messages = [];
        async for message in ctx.channel.history(limit=amount):
            messages.append({
                "author": message.author.name,
                "content": message.content,
                "timestamp": message.created_at.isoformat()
            });
        ##end
        with open(file_path, "w") as file:
            json.dump(messages, file, indent=4);
        ##endwith
        await ctx.reply("Here's your requested logs:",file=discord.File(file_path));  # Sends file
        os.remove(file_path);  # Deletes temp file after sending
    except Exception as e:
        print_err(e);
        await ctx.reply(f"An error occured while running the command `--logs 003--`");
    ##endtry
##end
@bot.tree.command(name="logs", description="Sends the last X messages in a temporary JSON file (Moderator-only).")
async def logs_slash(interaction: discord.Interaction, amount: int = 100):
    """Retrieves message logs for moderation purposes."""
    try:
        if isinstance(interaction.channel, discord.DMChannel):
            await interaction.response.send_message(f"Command cannot be run outside of a server `--logs 002--`", ephemeral=True);
            return;
        ##endif
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You do not have permission to retrieve logs. `--logs 001--`", ephemeral=True);
            return;
        ##endif
        file_path = f"{logs_dir}/logs.json";
        messages = [];
        async for message in interaction.channel.history(limit=amount):
            messages.append({
                "author": message.author.name,
                "content": message.content,
                "timestamp": message.created_at.isoformat()
            });
        ##end
        with open(file_path, "w") as file:
            json.dump(messages, file, indent=4);
        ##endwith
        await interaction.response.send_message("Here's your requested logs:", ephemeral=True,file=discord.File(file_path));  # Follow-up for file attachment
        os.remove(file_path);  # Deletes temp file after sending
    except discord.errors.NotFound as e:
        print_err(f"Interaction failed: {e}");
        await interaction.channel.send("Interaction failed");
    except Exception as e:
        print_err(e);
        await interaction.response.send_message(f"An error occured while running the command `--logs 003--`");
    ##endtry
##end
@bot.command(help="Recoding? Seriously?")
async def test(ctx):
    try:
        await ctx.reply('RECODING? SERIOUSLY?');
    except Exception as e:
        await ctx.reply('An error occured while running the the command `--test 003--`');
    ##endtry
##end
@bot.tree.command(name="test", description="Recoding? Seriously?")
async def test_slash(interaction: discord.Interaction):
    try:
        await interaction.response.send_message('RECODING? SERIOUSLY?');
    except discord.errors.NotFound as e:
        print_err(f"Interaction failed: {e}");
        await interaction.channel.send("Interaction failed");
    except Exception as e:
        print_err(e);
        await interaction.response.send_message('An error occured while running the command `--test 003--`');
    ##endtry
##end
"""@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Commands", description="Here are the available commands:", color=0x00ff00)
    for command in bot.tree.walk_commands():
        embed.add_field(name=command.name, value=command.description, inline=False)
    ##end
    await ctx.send(embed=embed);
##end"""
@bot.tree.command(name="help", description="Shows all commands and their parameters")
async def help_slash(interaction: discord.Interaction):
    try:
        embed = discord.Embed(title="Commands", description="Here are the available commands:", color=0x00ff00);
        for command in bot.tree.walk_commands():
            embed.add_field(name=command.name, value=command.description, inline=False)
        ##end
        await interaction.response.send_message(embed=embed);
    except discord.errors.NotFound as e:
        print_err(f"Interaction failed: {e}");
        await interaction.channel.send("Interaction failed");
    except Exception as e:
        print_err(e);
        await interaction.response.send_message('An error occured while running the command `--help 003--`');
    ##endtry
##end
@commands.has_permissions(manage_guild=True)
@bot.command(help="Says whatever you give it as an argument")
async def echo(ctx, message: str):
    try:
        message = re.sub(r"\$\{?[A-Za-z0-9_]+}?|\%[A-Za-z0-9_]+\%", "** **",message);
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.reply("You Cannot use echo outside of a server");
        else:
            if ctx.author.guild_permissions.manage_guild:
                await ctx.reply(message);
            else:
                await ctx.reply("You do not have permission to run this command");
            ##endif
        ##endif
    except Exception as e:
        print_err(e);
        await ctx.reply(f"An error occured while running the command `--echo 003--`");
    ##endtry
##end
@commands.has_permissions(manage_guild=True)
@bot.tree.command(name="echo", description="Says whatever you give it as an argument")
async def echo_slash(interaction: discord.Interaction, message: str):
    try:
        message = re.sub(r"\$\{?[A-Za-z0-9_]+}?|\%[A-Za-z0-9_]+\%", "* *",message);
        if isinstance(interaction.channel, discord.DMChannel):
            await interaction.response.send_message(message);
        else:
            if interaction.user.guild_permissions.manage_guild:
                await interaction.response.send_message(message);
            else:
                await interaction.response.send_message("You do not have permission to run this command");
            ##endif
        ##endif
    except discord.errors.NotFound as e:  # Handles the "Unknown interaction" error
        print_err(f"Interaction failed: {e}");
        await interaction.channel.send("Interaction failed");
    except Exception as e:
        print_err(e);
        await interaction.response.send_message(f"An error occured while running the command `--echo 003--`");
    ##endtry
##end
@bot.tree.command(name="van", description="bruh why did u van?")
async def van_slash(interaction: discord.Interaction, username:discord.User=None):
    try:
        if not username:
            await interaction.response.send_message(f"bro I cant van nothing :x:");
            return;
        ##endif
        if isinstance(interaction.channel, discord.DMChannel):
            await interaction.response.send_message(f"You tried to van {username.mention}, but vanning is only for servers. Nice try! <:trollgod:1330974448911913072>");
        else:
            van_log_file = f"{logs_dir}/{interaction.guild.id}_van_stats.json";
            # Load current count
            try:
                with open(van_log_file, "r") as file:
                    van_data = json.load(file);
                ##endwith
            except FileNotFoundError:
                van_data = {"count": 0};
            ##end
            # Increment and save
            van_data["count"] += 1;
            with open(van_log_file, "w") as file:
                json.dump(van_data, file, indent=4);
            ##endwith
            await interaction.response.send_message(f"{username.mention} has been vanned <:trollgod:1330974448911913072>");
        ##endif
    except discord.errors.NotFound as e:
        print_err(f"Interaction failed: {e}");
        await interaction.channel.send("Interaction failed");
    except Exception as e:
        print_err(e);
        await interaction.response.send_message('An error occured while running the command `--van 003--`');
    ##endtry
##end
@bot.command(help="bruh why did u van?")
async def van(ctx, username: discord.User=None):
    if not username:
        await ctx.reply(f"bro I cant van nothing :x:");
        return;
    ##endif
    try:
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.reply(f"You tried to van {username.mention}, but vanning is only for servers. Nice try! <:trollgod:1330974448911913072>");
        else:
            van_log_file = f"{logs_dir}/{ctx.guild.id}_van_stats.json";
            # Load current count
            try:
                with open(van_log_file, "r") as file:
                    van_data = json.load(file);
                ##endwith
            except FileNotFoundError:
                van_data = {"count": 0};
            ##endtry
            # Increment and save
            van_data["count"] += 1;
            with open(van_log_file, "w") as file:
                json.dump(van_data, file, indent=4);
            ##endwith
            await ctx.reply(f"{username.mention} has been vanned <:trollgod:1330974448911913072>");
        ##endif
    except discord.ext.commands.errors.UserNotFound as e:
        await ctx.reply(f"bro I cant van nothing :x:");
    ##endtry
##end
@bot.tree.command(name="config_automod", description="Configures automod settings for this server (requires manage-server)")
async def config_automod_slash(interaction: discord.Interaction):
    """Configures automod settings for this server (requires manage-server)"""
    try:
        if isinstance(interaction.channel, discord.DMChannel):
            await interaction.response.send_message(f"Command cannot be run outside of a server `--config_automod 002--`", ephemeral=True);
            return;
        ##endif
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("You do not have permission to run this command. `--config_automod 001--`", ephemeral=True);
            return;
        ##endif
        view = AutoModConfigView(interaction);
        await view.initialize();
        embed = discord.Embed(
            title="Automod Configuration",
            description="Select the flags you want to enable for this server:",
            color=discord.Color.blue()
        );
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True);
    except discord.errors.NotFound as e:  # Handles the "Unknown interaction" error
        print_err(f"Interaction failed: {e}");
        await interaction.channel.send("Interaction failed");
    except Exception as e:
        print_err(e);
        await interaction.response.send_message(f"An error occured while running the command `--config_automod 003--`");
    ##endtry
##end
@commands.has_permissions(moderate_members=True)
@bot.command(help="Check how many times /van has been used in this server")
async def van_stats(ctx):
    try:
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.reply(f"Command cannot be run outside of a server `--van_stats 002--`")
            return;
        ##endif
        if not ctx.author.guild_permissions.moderate_members:
            await ctx.reply(f"You do not have permission to use that command`--van_stats 001--`")
            return;
        ##endif
        van_log_file = f"{logs_dir}/{ctx.guild.id}_van_stats.json";
        # Load current count
        try:
            with open(van_log_file, "r") as file:
                van_data = json.load(file);
            ##endwith
            count = van_data.get("count", 0);
        except FileNotFoundError:
            count = 0;
        ##endtry
        await ctx.reply(f"The `van` command has been used **{count}** times in this server! 🚀🔥");
    except Exception as e:
        print_err(e);
        await ctx.reply(f"An error occurred while running the command `--van_stats 003--`");
    ##endtry
##end
@bot.tree.command(name="van_stats", description="Check how many times /van has been used in this server (requires moderate_members)")
@commands.has_permissions(moderate_members=True)
async def van_stats_slash(interaction: discord.Interaction):
    try:
        if isinstance(interaction.channel, discord.DMChannel):
            await interaction.response.send_message(f"Command cannot be run outside of a server `--van_stats 002--`")
            return;
        ##endif
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(f"You do not have permission to use that command`--van_stats 001--`")
            return;
        ##endif
        van_log_file = f"{logs_dir}/{interaction.guild.id}_van_stats.json";
        # Load current count
        try:
            with open(van_log_file, "r") as file:
                van_data = json.load(file);
            ##endwith
            count = van_data.get("count", 0);
        except FileNotFoundError:
            count = 0;
        ##endtry
        await interaction.response.send_message(f"The `van` command has been used **{count}** times in this server! 🚀🔥");
    except discord.errors.NotFound as e:  # Handles the "Unknown interaction" error
        print_err(f"Interaction failed: {e}");
        await interaction.channel.send("Interaction failed");
    except Exception as e:
        print_err(e);
        await interaction.response.send_message(f"An error occured while running the command `--van_stats 003--`");
    ##endtry
##end
@commands.has_permissions(manage_guild=True)
@bot.command(help="triggers an event (requires manage-server permission)")
async def trigger(ctx, event: str, delay: int=0):
    try:
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.reply(f"Command cannot be run outside of a server `--trigger 002--`")
            return;
        ##endif
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.reply(f"You do not have permission to use that command (Developer Only) `--trigger 001--`")
            return;
        ##endif
        json_content = sendRequest(webservice_url + f"/trigger_event?name={event}&delay={delay}", sitoken);
        if json_content is None:
            await ctx.reply(f"Failed to trigger event {event} :x:");
        else:
            await ctx.reply(f"Triggered event {event} :white_check_mark:");
        ##endif
    except Exception as e:
        print_err(e);
        await ctx.reply(f"An error occurred while running the command `--trigger 003--`");
    ##endtry
##end
@commands.has_permissions(manage_guild=True)
@bot.tree.command(name="trigger", description="triggers an event (requires manage-server permission)")
async def trigger(interaction: discord.Interaction, event: str, delay: int=0):
    await interaction.response.defer();
    msg = await interaction.original_response();
    try:
        if not isinstance(interaction.channel, discord.DMChannel):
            #dev_role = discord.utils.get(interaction.user.roles,name="Developer");
            if interaction.user.guild_permissions.manage_guild:
                json_content=sendRequest(webservice_url+f"/trigger_event?name={event}&delay={delay}",sitoken);
                if json_content is None:
                    await msg.edit(content=f"Failed to trigger event {event} :x:");
                else:
                    await msg.edit(content=f"Triggered event {event} :white_check_mark:");
                ##endif
            else:
                await msg.edit(content=f"You do not have permission to use that command (Developer Only) `--trigger 001--`");
            ##endif
        else:
            await msg.edit(content=f"Command cannot be run outside of a server `--trigger 002--`");
        ##endif
    except discord.errors.NotFound as e:  # Handles the "Unknown interaction" error
        print_err(f"Interaction failed: {e}");
        await interaction.channel.send("Interaction failed");
    except Exception as e:
        print_err(e);
        await msg.edit(content=f"An error occured while running the command `--trigger 003--`");
    ##endtry
##end
@commands.has_permissions(manage_guild=True)
@bot.command(help="adds an event to schedule (requires manage-server permission)")
async def event_add(ctx, event: str, delay: int=0):
    try:
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.reply("Command cannot be run outside of a server `--event add 002--`");
            return;
        ##endif
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.reply("You do not have permission to use that command (Developer Only) `--event add 001--`");
            return;
        ##endif
        json_ = {
            "name": event,
            "start_time": delay,
        };
        json_content = sendPostRequest(webservice_url + "/schedule/write?action=add", sitoken, json_);

        if json_content is None:
            await ctx.reply(f"Failed to add event {event} to schedule :x:");
        else:
            await ctx.reply(f"Added event {event} to schedule :white_check_mark:");
        ##endif
    except Exception as e:
        print_err(e);
        await ctx.reply("An error occurred while running the command `--event add 003--`");
    ##endtry
##end
@commands.has_permissions(manage_guild=True)
@bot.command(help="removes an event from schedule (requires manage-server permission)")
async def event_remove(ctx, event: str):
    try:
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.reply("Command cannot be run outside of a server `--event remove 002--`");
            return;
        ##endif
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.reply("You do not have permission to use that command (Developer Only) `--event remove 001--`");
            return;
        ##endif
        json_ = {
            "name": event,
        };
        json_content = sendPostRequest(webservice_url + "/schedule/write?action=remove", sitoken, json_);
        if json_content is None:
            await ctx.reply(f"Failed to remove event {event} from schedule :x:");
        else:
            await ctx.reply(f"Removed event {event} from schedule :white_check_mark:");
        ##endif
    except Exception as e:
        print_err(e);
        await ctx.reply("An error occurred while running the command `--event remove 003--`");
    ##endtry
##end
@commands.has_permissions(manage_guild=True)
@bot.tree.command(name="event_add", description="adds an event to schedule (requires manage-server permission)")
async def event_add_slash(interaction: discord.Interaction, event: str, delay: int=0):
    await interaction.response.defer();
    msg = await interaction.original_response();
    try:
        if not isinstance(interaction.channel, discord.DMChannel):
            #dev_role = discord.utils.get(interaction.user.roles,name="Developer");
            if interaction.user.guild_permissions.manage_guild:
                json_={
                    "name":event,
                    "start_time":delay,
                };
                json_content=sendPostRequest(webservice_url+f"/schedule/write?action=add",sitoken,json_);
                if json_content is None:
                    await msg.edit(content=f"Failed to add event {event} to schedule :x:");
                else:
                    await msg.edit(content=f"Added event {event} to schedule :white_check_mark:");
                ##endif
            else:
                await msg.edit(content=f"You do not have permission to use that command (Developer Only) `--event add 001--`");
            ##endif
        else:
            await msg.edit(content=f"Command cannot be run outside of a server `--event add 002--`");
        ##endif
    except discord.errors.NotFound as e:
        print_err(f"Interaction failed: {e}");
        await interaction.channel.send("Interaction failed");
    except Exception as e:
        print_err(e);
        await msg.edit(content=f"An error occured while running the command `--event add 003--`");
    ##endtry
##end
@commands.has_permissions(manage_guild=True)
@bot.tree.command(name="event_remove", description="removes an event from schedule (requires manage-server permission)")
async def event_remove_slash(interaction: discord.Interaction, event: str):
    await interaction.response.defer();
    msg = await interaction.original_response();
    try:
        if not isinstance(interaction.channel, discord.DMChannel):
            #dev_role = discord.utils.get(interaction.user.roles,name="Developer");
            if interaction.user.guild_permissions.manage_guild:
                json_={
                    "name":event,
                };
                json_content=sendPostRequest(webservice_url+f"/schedule/write?action=remove",sitoken,json_);
                if json_content is None:
                    await msg.edit(content=f"Failed to add event {event} to schedule :x:");
                else:
                    await msg.edit(content=f"Removed event {event} from schedule :white_check_mark:");
                ##endif
            else:
                await msg.edit(content=f"You do not have permission to use that command (Developer Only) `--event remove 001--`");
            ##endif
        else:
            await msg.edit(content=f"Command cannot be run outside of a server `--event remove 002--`");
        ##endif
    except discord.errors.NotFound as e:
        print_err(f"Interaction failed: {e}");
        await interaction.channel.send("Interaction failed");
    except Exception as e:
        print_err(e);
        await msg.edit(content=f"An error occured while running the command `--event remove 003--`");
    ##endtry
##end
@commands.has_permissions(manage_guild=True)
@bot.command(help="shows a list of events to be triggered")
async def schedule(ctx):
    try:
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.reply("Command cannot be run outside of a server `--schedule 002--`");
            return;
        ##endif
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.reply("You do not have permission to use that command (Developer Only) `--schedule 001--`");
            return;
        ##endif
        json_content = sendRequest(webservice_url + "/schedule", sitoken);
        if json_content is None:
            await ctx.reply("Failed to get schedule :x:");
        else:
            events = json_content["events"];
            embed = discord.Embed(title="Schedule", description="Scheduled Events", color=0x00ff00);
            for event in events:
                embed.add_field(name="Event Name", value=event["name"], inline=True);
                embed.add_field(name="Start Time", value=event["start_time"], inline=True);
            ##end
            await ctx.reply(embed=embed);
        ##endif
    except Exception as e:
        print_err(e);
        await ctx.reply("An error occurred while running the command `--schedule 003--`");
    ##endtry
##end
@commands.has_permissions(manage_guild=True)
@bot.tree.command(name="schedule", description="shows a list of events to be triggered")
async def schedule_slash(interaction: discord.Interaction):
    await interaction.response.defer();
    msg = await interaction.original_response();
    try:
        if not isinstance(interaction.channel, discord.DMChannel):
            #dev_role = discord.utils.get(interaction.user.roles,name="Developer");
            if interaction.user.guild_permissions.manage_guild:
                json_content=sendRequest(webservice_url+f"/schedule",sitoken);
                if json_content is None:
                    await msg.edit(content=f"Failed to get schedule :x:");
                else:
                    events=json_content['events'];
                    embed = discord.Embed(title="Schedule",description="Scheduled Events");
                    for event in events:
                        embed.add_field(name="Event Name", value=event["name"]);
                        embed.add_field(name="Start Time", value=event["start_time"]);
                    ##end
                    await msg.edit(embed=embed);
                ##endif
            else:
                await msg.edit(content=f"You do not have permission to use that command (Developer Only) `--schedule 001--`");
            ##endif
        else:
            await msg.edit(content=f"Command cannot be run outside of a server `--schedule 002--`");
        ##endif
    except discord.errors.NotFound as e:
        print_err(f"Interaction failed: {e}");
        await interaction.channel.send("Interaction failed");
    except Exception as e:
        print_err(e);
        await msg.edit(content=f"An error occured while running the command `--schedule 003--`");
    ##endtry
##end
@commands.has_permissions(moderate_members=True)
@bot.command(help="Times out a member for a specified duration with reason (requires moderate-members permission)")
async def mute(ctx, member: discord.Member, duration: int, unit: str, reason: str="No Reason provided"):
    try:
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.reply("Command cannot be run outside of a server `--mute 002--`");
            return;
        ##endif
        if not ctx.author.guild_permissions.moderate_members:
            await ctx.reply("You do not have permission to use that command `--mute 001--`", ephemeral=True);
            return;
        ##endif
        if not ctx.guild.me.guild_permissions.moderate_members:
            await ctx.reply("I do not have permission to mute members `--mute 004--`", ephemeral=True);
            return;
        ##endif
        if unit not in ['s', 'm', 'h', 'd']:
            await ctx.reply("Invalid time unit! Use 's' (seconds), 'm' (minutes), 'h' (hours), or 'd' (days).", ephemeral=True);
            return;
        ##endif
        # Calculate timeout duration
        time_map = {'s': timedelta(seconds=duration), 'm': timedelta(minutes=duration),
                    'h': timedelta(hours=duration), 'd': timedelta(days=duration)}
        delta = time_map[unit];
        # Apply the timeout
        timeout_end = discord.utils.utcnow() + delta;
        await member.timeout(timeout_end, reason=reason);
        await ctx.reply(f'{member.mention} has been muted for {duration} {unit}. Reason: {reason}');
    except Exception as e:
        print_err(e);
        await ctx.reply('An error occurred while running the command `--mute 003--`');
    ##endtry
##end
@commands.has_permissions(moderate_members=True)
@bot.tree.command(name="mute", description="Times out a member for a specified duration with reason (requires moderate-members permission)")
async def mute(interaction: discord.Interaction, member: discord.Member, duration: int, unit: str, reason: str="No Reason provided"):
    try:
        if not isinstance(interaction.channel, discord.DMChannel):
            if not interaction.user.guild_permissions.moderate_members:
                await interaction.response.send_message("You do not have permission to use that command`--mute 001--`", ephemeral=True);
                return;
            ##endif
            if not interaction.guild.me.guild_permissions.moderate_members:
                await interaction.response.send_message("I do not have permission to mute members `--mute 004--`", ephemeral=True);
                return;
            ##endif
            if unit not in ['s', 'm', 'h', 'd']:
                await interaction.response.send_message("Invalid time unit! Use 's' (seconds), 'm' (minutes), 'h' (hours), or 'd' (days).", ephemeral=True)
                return;
            ##endif
            # Calculate the timeout duration
            if unit == 's':
                delta = timedelta(seconds=duration);
            elif unit == 'm':
                delta = timedelta(minutes=duration);
            elif unit == 'h':
                delta = timedelta(hours=duration);
            elif unit == 'd':
                delta = timedelta(days=duration);
            ##endif

            # Apply the timeout
            timeout_end = discord.utils.utcnow() + delta;
            await member.timeout(timeout_end,reason=reason);
            await interaction.response.send_message(f'{member.mention} has been muted for {duration} {unit}. Reason: {reason}');
        else:
            await interaction.response.send_message(f"Command cannot be run outside of a server `--mute 002--`");
        ##endif
    except discord.errors.NotFound as e:
        print_err(f"Interaction failed: {e}");
        await interaction.channel.send("Interaction failed");
    except Exception as e:
        print_err(e);
        await interaction.response.send_message('An error occured while running the command `--mute 003--`');
    ##endtry
##end
@commands.has_permissions(ban_members=True)
@bot.command(help="Bans a member for a specified duration with reason (requires ban-members permission)")
async def ban(ctx, member: discord.User, duration: int, unit: str, reason: str = "No Reason provided"):
    try:
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.reply("Command cannot be run outside of a server `--ban 002--`");
            return;
        ##endif
        if not ctx.author.guild_permissions.ban_members:
            await ctx.reply("You do not have permission to use that command `--ban 001--`", ephemeral=True);
            return;
        ##endif
        if not ctx.guild.me.guild_permissions.ban_members:
            await ctx.reply("I do not have permission to ban members `--ban 004--`", ephemeral=True);
            return;
        ##endif
        if unit not in ['s', 'm', 'h', 'd']:
            await ctx.reply("Invalid time unit! Use 's' (seconds), 'm' (minutes), 'h' (hours), or 'd' (days). `--ban 005--`", ephemeral=True);
            return;
        ##endif
        # Calculate ban duration
        time_map = {'s': timedelta(seconds=duration), 'm': timedelta(minutes=duration),
                    'h': timedelta(hours=duration), 'd': timedelta(days=duration)};
        delta = time_map[unit];
        # Apply the ban
        await member.ban(reason=reason);
        await ctx.reply(f'{member.mention} has been banned for {duration} {unit}. Reason: {reason}');
    except Exception as e:
        print_err(e);
        await ctx.reply("An error occurred while running the command `--ban 003--`");
    ##endtry
##end
@commands.has_permissions(ban_members=True)
@bot.tree.command(name="ban", description="Bans a member for a specified duration with reason (requires ban-members permission)")
async def ban_slash(interaction: discord.Interaction, member: discord.User, duration: int, unit: str, reason: str="No Reason provided"):
    try:
        if not isinstance(interaction.channel, discord.DMChannel):
            if not interaction.user.guild_permissions.ban_members:
                await interaction.response.send_message("You do not have permission to use that command`--ban 001--`", ephemeral=True);
                return;
            ##endif
            if not interaction.guild.me.guild_permissions.ban_members:
                await interaction.response.send_message("I do not have permission to ban members `--ban 004--`", ephemeral=True);
                return;
            ##endif
            if unit not in ['s', 'm', 'h', 'd']:
                await interaction.response.send_message("Invalid time unit! Use 's' (seconds), 'm' (minutes), 'h' (hours), or 'd' (days). `--ban 005--`", ephemeral=True)
                return;
            ##endif
            # Calculate the ban duration
            if unit == 's':
                delta = timedelta(seconds=duration);
            elif unit == 'm':
                delta = timedelta(minutes=duration);
            elif unit == 'h':
                delta = timedelta(hours=duration);
            elif unit == 'd':
                delta = timedelta(days=duration);
            ##endif

            # Apply the ban
            timeout_end = discord.utils.utcnow() + delta;
            await member.ban(reason=reason);
            await interaction.response.send_message(f'{member.mention} has been banned for {duration}{unit}. Reason: {reason}');
        else:
            await interaction.response.send_message(f"Command cannot be run outside of a server `--ban 002--`");
        ##endif
    except discord.errors.NotFound as e:
        print_err(f"Interaction failed: {e}");
        await interaction.channel.send("Interaction failed");
    except Exception as e:
        print_err(e);
        await interaction.response.send_message('An error occured while running the command `--ban 003--`');
    ##endtry
##end
@commands.has_permissions(ban_members=True)
@bot.command(help="Removes ban from member (requires ban-members permission)")
async def unban(ctx, user_id: int, reason: str = "No Reason Provided"):
    try:
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.reply("Command cannot be run outside of a server `--unban 002--`");
            return;
        ##endif
        if not ctx.author.guild_permissions.ban_members:
            await ctx.reply("You do not have permission to use that command `--unban 001--`", ephemeral=True);
            return;
        ##endif
        if not ctx.guild.me.guild_permissions.ban_members:
            await ctx.reply("I do not have permission to unban members `--unban 004--`", ephemeral=True);
            return;
        ##endif
        user = await bot.fetch_user(user_id);  # Fetch user from Discord API
        await ctx.guild.unban(user, reason=reason);
        await ctx.reply(f'{user.mention} has been unbanned. Reason: {reason}');
    except Exception as e:
        print_err(e);
        await ctx.reply("An error occurred while running the command `--unban 003--`");
    ##endtry
##end
@commands.has_permissions(ban_members=True)
@bot.tree.command(name="unban", description="Removes ban from member (requires ban-members permission)")
async def unban(interaction: discord.Interaction, user_id:int, reason:str="No Reason Provided"):
    try:
        if not isinstance(interaction.channel, discord.DMChannel):
            if not interaction.user.guild_permissions.moderate_members:
                await interaction.response.send_message("You do not have permission to use that command`--unban 001--`", ephemeral=True);
                return;
            ##end
            if not interaction.guild.me.guild_permissions.moderate_members:
                await interaction.response.send_message("I do not have permission to unban members `--unban 004--`", ephemeral=True);
                return;
            ##endif
            user = await interaction.client.fetch_user(user_id);
            await interaction.guild.unban(user, reason=reason);
            await interaction.response.send_message(f'{user.mention} has been unmuted. Reason: {reason}');
        else:
            await interaction.response.send_message(f"Command cannot be run outside of a server `--unban 002--`");
        ##endif
    except discord.errors.NotFound as e:
        print_err(f"Interaction failed: {e}");
        await interaction.channel.send("Interaction failed");
    except Exception as e:
        print_err(e);
        await interaction.response.send_message('An error occured while running the command `--unban 003--`');
    ##endtry
##end
@commands.has_permissions(moderate_members=True)
@bot.command(help="Removes timeout from member (requires moderate-members permission)")
async def unmute(ctx, member: discord.Member,reason: str="No Reason provided"):
    try:
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.reply("Command cannot be run outside of a server `--unmute 002--`");
            return;
        ##endif
        if not ctx.author.guild_permissions.moderate_members:
            await ctx.reply("You do not have permission to use that command `--unmute 001--`", ephemeral=True);
            return;
        ##endif
        if not ctx.guild.me.guild_permissions.moderate_members:
            await ctx.reply("I do not have permission to unmute members `--unmute 004--`", ephemeral=True);
            return;
        ##endif
        # Calculate timeout duration
        await member.timeout(None);
        await ctx.reply(f'{member.mention} has been unmuted. Reason: {reason}');
    except discord.errors.NotFound as e:
        print_err(f"Interaction failed: {e}");
        await ctx.reply("Interaction failed");
    except Exception as e:
        print_err(e);
        await ctx.reply('An error occurred while running the command `--unmute 003--`');
    ##endtry
##end
@commands.has_permissions(moderate_members=True)
@bot.tree.command(name="unmute", description="Removes timeout from member (requires moderate-members permission)")
async def unmute_slash(interaction: discord.Interaction, member: discord.Member, reason:str="No Reason Provided"):
    try:
        if not isinstance(interaction.channel, discord.DMChannel):
            if not interaction.user.guild_permissions.moderate_members:
                await interaction.response.send_message("You do not have permission to use that command`--unmute 001--`", ephemeral=True);
                return;
            ##end
            if not interaction.guild.me.guild_permissions.moderate_members:
                await interaction.response.send_message("I do not have permission to mute members `--unmute 004--`", ephemeral=True);
                return;
            ##endif
            # Apply the timeout
            await member.timeout(None);
            await interaction.response.send_message(f'{member.mention} has been unmuted. Reason: {reason}');
        else:
            await interaction.response.send_message(f"Command cannot be run outside of a server `--unmute 002--`");
        ##endif
    except discord.errors.NotFound as e:
        print_err(f"Interaction failed: {e}");
        await interaction.channel.send("Interaction failed");
    except Exception as e:
        print_err(e);
        await interaction.response.send_message('An error occured while running the command `--unmute 003--`');
    ##endtry
##end
@bot.command(name="asset",help="get asset info")
async def asset(ctx, assetId:str):
    await ctx.reply("Asset Info:");
##end
def runbot(token):
    bot.run(token);
##end
if __name__=="__main__":
    runbot(token);
##endif
