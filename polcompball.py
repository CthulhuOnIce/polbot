import requests
import sumy

BLACKLISTEDSECTIONS = ["gallery", "animations"]

def get_article_json(name):
	name = name.title()
	for name in [name.replace(" ", "_"), name.replace(" ", "-"), name.replace(" ", "")]:
		djson = requests.get(f"https://polcompball.fandom.com/api/v1/Articles/Details?titles={name}").json()
		if not len(djson["items"]):
			continue
		identity = list(djson["items"].keys())[0] # get the id of the article
		djson = djson["items"][identity]
		j = requests.get(f"https://polcompball.fandom.com/api/v1/Articles/AsSimpleJson?id={identity}").json()
		j["thumbnail"] = djson["thumbnail"]
		j["title"] = djson["title"]
		j["abstract"] = djson["abstract"]
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