import discord
from discord.ext import commands
import yaml
import pickle
from threading import Thread
import asyncio
import polcompball as pol
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice
import qanon as Q
import feedparser
import requests
import factcheck as fc

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

def rss2discord(message):
	message = message.replace("<br />", "\n")
	return message

def qdrop2embed(drop):
	embed=discord.Embed(title=drop.title, description="\u200b", color=0x1f4d00, url=drop.link)
	if drop.imageurl:
		embed.set_thumbnail(url=drop.imageurl) 
	add_body_to_embed(embed, drop.body, "\u200b")
	embed.set_footer(text=drop.pubDate)
	return embed

try:
	with open("config.yml", "r") as r:
		C = yaml.load(r.read(), Loader=yaml.FullLoader)
except FileNotFoundError:
	CRASH("No config.yml, please copy and rename config-example.yml and fill in the appropriate values.")


bot = commands.Bot(command_prefix=C["prefix"])

Thread(target=Q.check_loop, args=(bot.loop,)).start()  # handles new qanon "drops"

@bot.event
async def on_ready():
	await bot.change_presence(activity=discord.Game(name=f'{C["prefix"]}help'))
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
	embed.add_field(name="Guilds", value=len(bot.guilds), inline=False)
	if "donate" in C and C["donate"]: # looks weird, basically checks if there is a donate value, and its not blank
		embed.add_field(name="Donate", value=f"[Click me!]({C['donate']})", inline=False)
	if "source" in C and C["source"]:
		embed.add_field(name="Source Code", value=f"[Click me!]({C['source']})", inline=False)
	if "invite" in C and C["invite"]:
		embed.add_field(name="Invite me to your server", value=f"[Click me!]({C['invite']})", inline=False)
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
						
@bot.command(brief="Display last 10 updates from QAnon RSS feed")
async def qanon(ctx):
	embeds = []
	for i in range(10):
		drop = Q.DROPCACHE[i]
		embeds.append(qdrop2embed(drop))
	paginator = BotEmbedPaginator(ctx, embeds)
	await paginator.run()

@bot.command(brief="Retrieve specific Q 'drop'")
async def qdrop(ctx, dropnum:int):
	if dropnum <= 0 or dropnum >= len(Q.DROPCACHE)+1:
		await ctx.send(f"Number must be between 0 and {len(Q.DROPCACHE)}")
		return
	drop = Q.DROPCACHE[len(Q.DROPCACHE)-dropnum]
	await ctx.send(embed=qdrop2embed(drop))
				      
@bot.command(brief="Search QAnon 'Drops' for term")
async def qsearch(ctx, *, term:str):
	embeds = []
	term = term.lower()
	for drop in Q.DROPCACHE:
		if term in drop.title.lower() or term in drop.body.lower():
			embeds.append(qdrop2embed(drop))
	if len(embeds):
		paginator = BotEmbedPaginator(ctx, embeds)
		await paginator.run()
	else:
		await ctx.send("No drops found.")
				      
@bot.command(brief="Generate political compass")
async def polcompass(ctx, ec:float, soc:float):
	await ctx.send(f"https://www.politicalcompass.org/chart?ec={ec}&soc={soc}")	

@bot.command(brief="Fact check a claim via query")
async def factcheck(ctx, *, claim:str):
	if not "factcheckapikey" in C or not C["factcheckapikey"]:
		await ctx.send("Fact check API key not set.")
		return
	results = fc.factcheck(claim, C["factcheckapikey"])
	if results == {}:
		await ctx.send("No results found!")
		return
	embeds = []
	for claim in results["claims"]:
		embed = discord.Embed(title=claim["claiment"] if "claiment" in claim else "Claim:", description=claim["text"])
		if "claimDate" in claim:
			embed.set_footer(text=claim["claimDate"])
		for review in claim["claimReview"]:
			embed.add_field(name=f"Review: {review['publisher']['name'] if 'name' in review['publisher']['site'] else review['publisher']}", value=f"{review['textualRating']}\n*([Source]({review['url']}))*")
		embeds.append(embed)
	paginator = BotEmbedPaginator(ctx, embeds)
	await paginator.run()

bot.run(C["token"])  # Where 'TOKEN' is your bot token
