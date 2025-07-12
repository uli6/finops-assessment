import sqlite3
import re

DB = 'finops_assessment.db'

# Link de fallback para exemplos reais
FALBACK_LINK = 'https://www.finops.org/case-studies/'

# Regex para encontrar Real Example sem link
real_example_pattern = re.compile(r'(Real Example:)([^\n\[]*)(\n|$)', re.IGNORECASE)

# Regex para detectar se já há link
url_pattern = re.compile(r'https?://')

def add_link_to_real_example(text):
    def replacer(match):
        prefix, content, ending = match.groups()
        # Se já houver link, não altera
        if url_pattern.search(content):
            return match.group(0)
        # Adiciona link de referência
        return f"{prefix}{content.strip()} ([read article]({FALBACK_LINK}))\n"
    return real_example_pattern.sub(replacer, text)

def main():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute('SELECT id, recommendations FROM assessments WHERE recommendations IS NOT NULL')
    updates = []
    for row in cursor.fetchall():
        aid, rec = row
        if not rec:
            continue
        new_rec = add_link_to_real_example(rec)
        if new_rec != rec:
            updates.append((new_rec, aid))
    print(f"Encontrados {len(updates)} assessments para atualizar.")
    for new_rec, aid in updates:
        cursor.execute('UPDATE assessments SET recommendations = ? WHERE id = ?', (new_rec, aid))
    conn.commit()
    conn.close()
    print("Atualização concluída!")

if __name__ == '__main__':
    main() 