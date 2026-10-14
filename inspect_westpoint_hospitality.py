import urllib.request
from lxml import html

headers = {"User-Agent": "Mozilla/5.0"}
url = "https://www.westpointhospitality.com/products"
text = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30).read().decode("utf-8", "ignore")
tree = html.fromstring(text)
seen = set()
for a in tree.xpath("//a[contains(@href, '/collections/')]"):
    href = a.get("href") or ""
    title = " ".join(" ".join(a.xpath(".//text()")).split())
    key = (href, title)
    if key in seen:
        continue
    seen.add(key)
    print(href, "|", title)
