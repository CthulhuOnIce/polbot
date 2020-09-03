import requests

def factcheck(query, key):
	if not key:		return
	return requests.get("https://factchecktools.googleapis.com/v1alpha1/claims:search", params={"query": query, "key": key, "pageSize": 50, "languageCode": "en-US"}).json()