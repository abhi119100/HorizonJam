import json, os

dir_path = 'HorizonJam-master/RAG/documents/music_rag_data'
files = [f for f in os.listdir(dir_path) if f.endswith('.json')]
total = 0
counts = {}
print('File counts:')
for f in files:
    with open(os.path.join(dir_path, f), encoding='utf-8') as fp:
        data = json.load(fp)
        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict):
            count = len(data.keys())
        else:
            count = 0
        counts[f] = count
        total += count
        print(f'{f}: {count}')
print(f'Total: {total}')