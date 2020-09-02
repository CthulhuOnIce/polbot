import time
import feedparser
import markovify
import pickle
import re

ALLDROPS = "https://qalerts.app/data/rss/posts-all.rss"
STANDARDFEED = "https://qalerts.app/data/rss/posts.rss"
LINKREPLACEPATTERN = re.compile(r'<a href="([^\s]*)">([^\s]*)</a>')
IMAGEFINDPATTERN = re.compile(r'<img src=\'([^\s]*)\'>')
LASTDROP = None
DROPCACHE = []

def rss2markdown(rss):
	rss = rss.replace("<br />\n", "\n")
	rss = rss.replace("<strong>", "**")
	rss = rss.replace("</strong>", "**")
	rss = rss.replace("&#09;", "  ")
	rss = re.sub(LINKREPLACEPATTERN, r"[\2](\1)", rss)
	return rss

class QDrop:
	imageurl = None
	title = None
	body = None
	rss = None
	link = None
	pubDate = None
	def __init__(self, rss=None):
		if not rss:		return
		self.link = rss["link"]
		self.pubDate = rss["published"]
		text = rss2markdown(rss["summary"])
		# extract image, convert html links to markdown
		matches = re.findall(IMAGEFINDPATTERN, text)
		self.imageurl = matches[0] if len(matches) else None
		text = re.sub(IMAGEFINDPATTERN, r"", text)
		self.body = text
		self.title = rss2markdown(rss["title"])
		self.rss = rss


try:
	DROPCACHE = pickle.load(open("QAnonCache.p", "rb"))
except FileNotFoundError:
	print("QAnon cache non-existant, rebuilding...")
	DROPCACHENEW = feedparser.parse(ALLDROPS).entries
	for entry in DROPCACHENEW:	DROPCACHE.append(QDrop(entry))
	pickle.dump(DROPCACHE, open("QAnonCache.p", "wb"))
	print(f"QAnon cache rebuilt. {len(DROPCACHE)} Drops processed.")
LASTDROP = DROPCACHE[0]

def check_loop(botloop):
	global LASTDROP
	global DROPCACHE
	while True:
		time.sleep(5)
		feed = feedparser.parse(STANDARDFEED).entries
		if feed[0]["title"] == LASTDROP.rss["title"]:	continue
		new_drops = []
		for entry in feed:
			if entry["title"] == LASTDROP.rss["title"]:
				break
			new_drops.append(QDrop(entry))
		if len(new_drops) == len(feed):
			DROPCACHE = []
			DROPCACHENEW = feedparser.parse(ALLDROPS).entries
			for entry in DROPCACHENEW:	DROPCACHE.append(QDrop(entry))
			LASTDROP = DROPCACHE[0]
		else:
			DROPCACHE = new_drops + DROPCACHE
			LASTDROP = DROPCACHE[0]
		pickle.dump(DROPCACHE, open("QAnonCache.p", "wb"))


	
