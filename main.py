import discord
from discord.ext import commands
import yaml
import pickle
from threading import Thread
import asyncio
import polcompball as pol

C = {}

def CRASH(message):
	print(f"FATAL: {message}")
	input("Press enter to continue")
	exit()

def wrap(s, w): # s = source, w = length
    return [s[i:i + w] for i in range(0, len(s), w)]

try:
	with open("config.yml", "r") as r:
		C = yaml.load(r.read(), Loader=yaml.FullLoader)
except FileNotFoundError:
	CRASH("No config.yml, please copy and rename config-example.yml and fill in the appropriate values.")


bot = commands.Bot(command_prefix=C["prefix"])

@bot.event
async def on_ready():
    print("Ready to go.")

@bot.event
async def on_message(message):
	if message.startswith(f"{C['prefix']}reloadconfig") and message.author.id in owners:  # hidden from help command
		try:
			with open("config.yml", "r") as r:
				C = yaml.load(r.read(), Loader=yaml.FullLoader)
		except FileNotFoundError:
			CRASH("No config.yml, please copy and rename config-example.yml and fill in the appropriate values.")
	await bot.process_commands(message)

@bot.command(brief="Bot info")
async def info(ctx):
	embed = discord.Embed(title=C["name"], description=C["description"])
	embed.add_field(name="Guilds", value=len(bot.guilds))
	if "donate" in C and C["donate"]: # looks weird, basically checks if there is a donate value, and its not blank
		embed.add_field(name="Donate", value=f"[Click me!]({C['donate']})")
	await ctx.send(embed=embed)

@bot.command(brief="Tells you info about a political ideology", description="Uses polcompball wiki to give you information about poliical ideologies.")
async def whatis(ctx, *, ideology:str):
	article_json = pol.trim_article_json(pol.get_article_json(ideology))
	if not article_json:
		await ctx.send("Couldn't find that ideology!")
		return
	embed = discord.Embed(title=article_json["title"], description="\u200b", url=article_json["url"])
	if(article_json["thumbnail"]):
		embed.set_thumbnail(url=article_json["thumbnail"])
	for section in article_json["sections"]:
		if not len(section["content"]):
			embed.add_field(name=section["title"], value="-----------------------")
		else:
			body = ""
			for p in section["content"]:
				if p["type"] == "paragraph":
					body += f"{p['text']}\n"
				if p["type"] == "list":
					for element in p["elements"]:
						body += f" - {element['text']}\n"
			if len(body) > 1024: # cut off
				wrapped = wrap(body, 1024)
				for i in range(len(wrapped)):
					if i == 0:
						embed.add_field(name=section["title"], value=wrapped[i], inline=False)
					else:
						embed.add_field(name='\u200b', value=wrapped[i], inline=False)
			else:
				embed.add_field(name=section["title"], value=body, inline=False)
	embed.set_footer(text=f"Requested by {ctx.author.name}#{ctx.author.discriminator}")
	await ctx.send(embed=embed)

bot.run(C["token"])  # Where 'TOKEN' is your bot token
