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
    await bot.process_commands(message)

@bot.command()
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
	await ctx.send(embed=embed)

bot.run(C["token"])  # Where 'TOKEN' is your bot token
