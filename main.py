import discord
from discord.ext import commands
import yaml
import pickle
from threading import Thread
import asyncio
import polcompball as pol
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice

C = {}

def CRASH(message):
	print(f"FATAL: {message}")
	input("Press enter to continue")
	exit()

def wrap(s, w): # s = source, w = length
    return [s[i:i + w] for i in range(0, len(s), w)]

def generate_body_from_section(section):
	body = ""
	for content in section["content"]:
		if content["type"] == "paragraph":
			body += f"{content['text']}\n"
		if content["type"] == "list":
			for element in content["elements"]:
				body += f" - {element['text']}\n"
	return body

def add_body_to_embed(embed, body, firsttitle):
	splitbody = wrap(body, 1024)
	for i in range(len(splitbody)):
		embed.add_field(name=(firsttitle if i == 0 else "\u200b"), value=splitbody[i], inline=False)
	return embed
			

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
	global C
	if message.content.startswith(f"{C['prefix']}reloadconfig") and message.author.id in C["owners"]:  # hidden from help command
		try:
			with open("config.yml", "r") as r:
				C = yaml.load(r.read(), Loader=yaml.FullLoader)
		except FileNotFoundError:
			CRASH("No config.yml, please copy and rename config-example.yml and fill in the appropriate values.")
		await message.channel.send("Reloaded.")
		return
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
	embeds = []

	for section in article_json["sections"]:
		embed=discord.Embed(title=section["title"], url=article_json["url"], description="\u200b")
		if article_json["thumbnail"]:
			embed.set_thumbnail(url=article_json["thumbnail"])
		if section["level"] == 1: # title page
			bod = generate_body_from_section(section)
			add_body_to_embed(embed, bod, section["title"])
		else: # section header or small paragraph
			if(len(section["content"])):
				bod = generate_body_from_section(section)
				add_body_to_embed(embed, bod, section["title"])
			else:
				bodylength = 0
				found = False
				for section2 in article_json["sections"][:]:
					if bodylength > 5500:
						break
					if found:
						if section2["level"] <= section["level"]:
							break
						bod = generate_body_from_section(section2)
						bodylength += len(bod)
						add_body_to_embed(embed, bod, section2["title"])
						article_json["sections"].remove(section2)
					elif section2 == section:
						found = True
		embeds.append(embed)
	paginator = BotEmbedPaginator(ctx, embeds)
	await paginator.run()

bot.run(C["token"])  # Where 'TOKEN' is your bot token
