import requests
import sumy

BLACKLISTEDSECTIONS = ["how to draw", "gallery", "animations"]

def get_article_json(name):
	name = name.title().replace(" ", "_")
	djson = requests.get(f"https://polcompball.fandom.com/api/v1/Articles/Details?titles={name}").json()
	if not len(djson["items"]):
		return
	identity = list(djson["items"].keys())[0] # get the id of the article
	djson = djson["items"][identity]
	j = requests.get(f"https://polcompball.fandom.com/api/v1/Articles/AsSimpleJson?id={identity}").json()
	j["thumbnail"] = djson["thumbnail"]
	j["title"] = djson["title"]
	j["url"] = f"https://polcompball.fandom.com/wiki/{name}"
	return j

def trim_article_json(articlejson):
	if not articlejson:
		return
	sections = articlejson["sections"]
	for article in sections:
		if article["title"].lower() in BLACKLISTEDSECTIONS:
			sections.remove(article)
	return articlejson