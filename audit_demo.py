import re
import json
import os
from html.parser import HTMLParser

repo_dir = r"C:/Users/Samer/Samer-Elhamy.github.io"
demo_path = os.path.join(repo_dir, "demo.html")

with open(demo_path, "r", encoding="utf-8") as f:
    html = f.read()

print(f"Loaded demo.html: {len(html)} chars")

# 1. JSON-LD Audit
print("\n--- 1. JSON-LD Schema Audit ---")
json_ld_matches = re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
print(f"Total JSON-LD blocks: {len(json_ld_matches)}")

graph_nodes = []
for idx, block in enumerate(json_ld_matches):
    try:
        data = json.loads(block.strip())
        if "@graph" in data:
            nodes = data["@graph"]
            print(f"Block {idx} (@graph): {len(nodes)} nodes")
            graph_nodes.extend(nodes)
            for n_idx, node in enumerate(nodes):
                print(f"  [{n_idx+1}] @type: {node.get('@type')}, @id: {node.get('@id')}, name: {node.get('name')}")
        else:
            print(f"Block {idx} (single): @type: {data.get('@type')}")
    except Exception as e:
        print(f"Block {idx} Error parsing JSON: {e}")

print(f"Total @graph nodes found: {len(graph_nodes)}")

# 2. NAP & Geo Audit
print("\n--- 2. NAP & Geo Verification ---")
phone_match = re.findall(r'\+31\s*6\s*14\s*73\s*35\s*74|\+31614733574', html)
print(f"E.164 phone occurrences: {len(phone_match)}")

has_address = "Eerste van der Helststraat 42" in html
has_postal = "1072 NV" in html
has_city = "Amsterdam" in html
has_lat = "52.356" in html
has_lon = "4.891" in html
print(f"NAP Checks: Address: {has_address}, Postal: {has_postal}, City: {has_city}, Lat: {has_lat}, Lon: {has_lon}")

# 3. HTML Structure & Tag Audit & Asset Links
print("\n--- 3. HTML Structure & Asset Links Audit ---")
class ComprehensiveParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.void_tags = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
        self.tag_errors = []
        self.assets = []
        self.headings = []
        self.buttons = []
        self.inputs = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        tag_lower = tag.lower()

        # check void tag
        if tag_lower not in self.void_tags:
            self.stack.append((tag_lower, self.getpos()))

        # Check assets
        for attr in ['src', 'href']:
            val = attr_dict.get(attr)
            if val and not val.startswith(('http://', 'https://', '#', 'data:', 'mailto:', 'tel:', 'javascript:')):
                self.assets.append((tag_lower, attr, val))

        # Check accessibility items
        if tag_lower in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.headings.append((tag_lower, attr_dict))
        elif tag_lower == 'button':
            self.buttons.append(attr_dict)
        elif tag_lower == 'input':
            self.inputs.append(attr_dict)
        elif tag_lower == 'img':
            self.images.append(attr_dict)

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in self.void_tags:
            return
        if not self.stack:
            self.tag_errors.append(f"Unexpected closing tag </{tag_lower}> at line {self.getpos()[0]}")
            return
        if self.stack[-1][0] == tag_lower:
            self.stack.pop()
        else:
            open_tags = [t[0] for t in self.stack]
            if tag_lower in open_tags:
                idx = len(open_tags) - 1 - open_tags[::-1].index(tag_lower)
                unclosed = self.stack[idx+1:]
                for u in unclosed:
                    self.tag_errors.append(f"Unclosed tag <{u[0]}> opened at line {u[1][0]} before closing </{tag_lower}> at line {self.getpos()[0]}")
                self.stack = self.stack[:idx]
            else:
                self.tag_errors.append(f"Stray closing tag </{tag_lower}> at line {self.getpos()[0]}")

parser = ComprehensiveParser()
parser.feed(html)

print(f"Tag errors found: {len(parser.tag_errors)}")
for err in parser.tag_errors[:15]:
    print("  ", err)
if parser.stack:
    print(f"Unclosed tags remaining: {len(parser.stack)}")
    for s in parser.stack:
        print(f"  <{s[0]}> at line {s[1][0]}")

# Missing assets
missing = []
for tag_name, attr, path in parser.assets:
    clean_path = path.split('?')[0].split('#')[0]
    if clean_path.startswith('/'):
        clean_path = clean_path.lstrip('/')
    full_path = os.path.join(repo_dir, clean_path.replace('/', os.sep))
    if not os.path.exists(full_path):
        missing.append((tag_name, attr, path, full_path))

print(f"\nLocal assets referenced: {len(parser.assets)}")
print(f"Missing local assets: {len(missing)}")
for m in missing:
    print(f"  Missing: <{m[0]} {m[1]}='{m[2]}'> (expected at {m[3]})")

# Images without alt
images_no_alt = [img for img in parser.images if 'alt' not in img or not img['alt'].strip()]
print(f"\nImages checked: {len(parser.images)}, Images missing alt attribute: {len(images_no_alt)}")

# Mirror files check
print("\n--- 4. Mirror paths check ---")
mirror_files = [
    os.path.join(repo_dir, "demo", "index.html"),
    os.path.join(repo_dir, "apple", "index.html"),
    os.path.join(repo_dir, "preview", "index.html"),
    os.path.join(repo_dir, "apple-design-demo.html"),
    os.path.join(repo_dir, "angelo-apple-theme-demo.html"),
]
for mf in mirror_files:
    exists = os.path.exists(mf)
    size = os.path.getsize(mf) if exists else 0
    differs = "N/A"
    if exists:
        with open(mf, "r", encoding="utf-8") as f:
            content = f.read()
        differs = "IDENTICAL" if content == html else f"DIFFERENT (len {len(content)} vs {len(html)})"
    print(f"Mirror: {os.path.relpath(mf, repo_dir)} - Exists: {exists} - {differs}")
