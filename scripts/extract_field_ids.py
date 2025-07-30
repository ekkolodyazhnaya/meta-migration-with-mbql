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
        username='e.kolodyazhnaya@mercuryo.io',
        password='***REMOVED***'
    ))
    m.authenticate()
    q = m.get_question_details(5280)
    ids = set()
    extract_field_ids(q['dataset_query']['query'], ids)
    print('Field IDs in MBQL:', sorted(ids))

if __name__ == '__main__':
    main() 