from metabase_migrator import MetabaseMigrator, MetabaseConfig

def extract_field_ids(obj, ids):
    if isinstance(obj, list):
        for x in obj:
            extract_field_ids(x, ids)
    elif isinstance(obj, dict):
        if 'field' in obj and isinstance(obj['field'], int):
            ids.add(obj['field'])
        for v in obj.values():
            extract_field_ids(v, ids)

def main():
    m = MetabaseMigrator(MetabaseConfig(
        base_url='https://metabase.mrcr.io',
        username='YOUR_USERNAME_HERE',
        password='***REMOVED***'
    ))
    m.authenticate()
    q = m.get_question_details(5280)
    ids = set()
    extract_field_ids(q['dataset_query']['query'], ids)
    print('Field IDs and column names in MBQL:')
    for field_id in sorted(ids):
        field_info = m.session.get(f"https://metabase.mrcr.io/api/field/{field_id}", headers={"X-Metabase-Session": m.session_token})
        if field_info.status_code == 200:
            name = field_info.json().get('name')
            table_id = field_info.json().get('table_id')
            print(f"Field ID: {field_id} | Column name: {name} | Table ID: {table_id}")
        else:
            print(f"Field ID: {field_id} | Column name: NOT FOUND")

if __name__ == '__main__':
    main() 