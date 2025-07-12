import sqlite3
import requests
import time

DB = 'finops_assessment.db'
BASE_URL = 'http://localhost:5002/get_assessment_results/'

# Buscar todos os assessments completos
conn = sqlite3.connect(DB)
cursor = conn.cursor()
cursor.execute('SELECT id FROM assessments WHERE status = "completed"')
ids = [row[0] for row in cursor.fetchall()]
conn.close()

print(f'Forçando geração de recomendações para {len(ids)} assessments...')

for aid in ids:
    print(f' - Gerando para assessment {aid}...')
    try:
        r = requests.get(f'{BASE_URL}{aid}', timeout=60)
        if r.status_code == 200:
            print(f'   OK')
        else:
            print(f'   Falha HTTP {r.status_code}')
    except Exception as e:
        print(f'   Erro: {e}')
    time.sleep(2)  # Evita sobrecarga na API

print('Processo concluído!') 