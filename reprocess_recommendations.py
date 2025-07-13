import sqlite3
from app import generate_recommendations, DATABASE

if __name__ == '__main__':
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, scope_id, domain FROM assessments WHERE status = 'completed'")
    assessments = cursor.fetchall()
    print(f"Found {len(assessments)} completed assessments to reprocess.")
    updated = 0
    for aid, scope_id, domain in assessments:
        print(f"Reprocessing assessment {aid} (scope: {scope_id}, domain: {domain})...")
        try:
            cursor.execute('SELECT overall_percentage FROM assessments WHERE id = ?', (aid,))
            row = cursor.fetchone()
            overall_percentage = row[0] if row else 0
            # Dummy lens_scores for compatibility
            lens_scores = {}
            recs = generate_recommendations(aid, scope_id, domain, overall_percentage, lens_scores)
            cursor.execute('UPDATE assessments SET recommendations = ? WHERE id = ?', (recs, aid))
            conn.commit()
            updated += 1
        except Exception as e:
            print(f"Error reprocessing assessment {aid}: {e}")
    conn.close()
    print(f"Done. Updated recommendations for {updated} assessments.") 