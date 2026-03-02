import json
import zipfile

with zipfile.ZipFile('d:/Thesis_Antigravity/Data/source/Sitzfertigung 2.4.simvsm') as z:
    data = json.loads(z.read('project.json'))

nodes = data['alternatives'][0]['model']['nodeDataArray']

count_by_type = {}
valid_nodes = []

for n in nodes:
    if n.get('class') == 'supplier':
        print(json.dumps(n, indent=2))
