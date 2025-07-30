import json
from metabase_migrator import MetabaseMigrator, MetabaseConfig

# Optionally enforce a specific join type for all joins
JOIN_TYPE_OVERRIDE = 'inner-join'  # Set to None to keep original

# Manual column name overrides: (column_name, table_id) -> field_id
COLUMN_NAME_TABLE_OVERRIDES = {
    ('VENDOR_ID', 91055): 756121,  # Example override
    # Add more overrides here as needed
}

def load_table_mapping():
    with open('migrations/migration_mapping.json', 'r') as f:
        mapping = json.load(f)
    # Try both table_mapping and exasol_to_starrocks if present
    table_mapping = mapping.get('table_mapping', {})
    # Lowercase keys for robustness
    return {k.lower(): v for k, v in table_mapping.items()}

def get_starrocks_table_id(m, exasol_table_id, exasol_table_name, table_mapping):
    # Try mapping by schema.table, just table, and upper/lower case
    candidates = []
    if exasol_table_name:
        # Try full schema.table
        candidates.append(exasol_table_name.lower())
        candidates.append(exasol_table_name.upper())
        # Try just table name (no schema)
        if '.' in exasol_table_name:
            table_only = exasol_table_name.split('.')[-1]
            candidates.append(table_only.lower())
            candidates.append(table_only.upper())
        else:
            candidates.append(exasol_table_name.lower())
            candidates.append(exasol_table_name.upper())
    if exasol_table_id:
        candidates.append(str(exasol_table_id))
    for key in candidates:
        sr_table_name = table_mapping.get(key)
        if sr_table_name:
            print(f"[DEBUG] Table mapping: Exasol '{exasol_table_name}' (candidates: {candidates}) → StarRocks '{sr_table_name}'")
            # Find the table ID in Metabase by name
            resp = m.session.get(f"https://metabase.mrcr.io/api/database/16/metadata", headers={"X-Metabase-Session": m.session_token})
            if resp.status_code == 200:
                for t in resp.json().get('tables', []):
                    if t.get('name') == sr_table_name:
                        print(f"[DEBUG] Found StarRocks table ID {t.get('id')} for '{sr_table_name}'")
                        return t.get('id')
    print(f"[WARNING] Could not map Exasol table '{exasol_table_name}' (candidates: {candidates}) to any StarRocks table.")
    return None

def extract_field_ids_with_table(obj, ids, join_tables=None, current_table=None, current_alias=None):
    if join_tables is None:
        join_tables = {}
    if isinstance(obj, list):
        if len(obj) > 1 and obj[0] == 'field' and isinstance(obj[1], int):
            ids.append((obj[1], current_table, current_alias))
        for x in obj:
            extract_field_ids_with_table(x, ids, join_tables, current_table, current_alias)
    elif isinstance(obj, dict):
        if 'source-table' in obj and 'alias' in obj:
            join_table_id = obj['source-table']
            join_alias = obj['alias']
            join_tables[join_alias] = join_table_id
            for v in obj.values():
                extract_field_ids_with_table(v, ids, join_tables, join_table_id, join_alias)
        else:
            for v in obj.values():
                extract_field_ids_with_table(v, ids, join_tables, current_table, current_alias)

def get_field_name(m, field_id):
    resp = m.session.get(f"https://metabase.mrcr.io/api/field/{field_id}", headers={"X-Metabase-Session": m.session_token})
    if resp.status_code == 200:
        return resp.json().get('name')
    return None

def get_starrocks_field_id(m, starrocks_table_id, column_name):
    override = COLUMN_NAME_TABLE_OVERRIDES.get((column_name, starrocks_table_id))
    if override is not None:
        return override
    resp = m.session.get(f"https://metabase.mrcr.io/api/table/{starrocks_table_id}/query_metadata", headers={"X-Metabase-Session": m.session_token})
    if resp.status_code == 200:
        fields = resp.json().get('fields', [])
        for f in fields:
            if f.get('name') == column_name:
                return f.get('id')
    return None

def map_field_ids_by_name_with_table(obj, m, exasol_to_sr, join_tables=None, current_table=None, current_alias=None, exasol_id_to_name=None):
    if join_tables is None:
        join_tables = {}
    if isinstance(obj, list):
        if len(obj) > 1 and obj[0] == 'field' and isinstance(obj[1], int):
            old_id = obj[1]
            table_id = current_table
            alias = current_alias
            key = (old_id, table_id, alias)
            if key in exasol_to_sr:
                new_id = exasol_to_sr[key]
                if new_id is not None:
                    obj[1] = new_id
                else:
                    col_name = exasol_id_to_name.get(old_id, 'UNKNOWN')
                    print(f"[WARNING] Could not map field ID {old_id} (column '{col_name}') for table {table_id}, alias {alias}. Removing this field from MBQL.")
                    return None
            return [x for x in (map_field_ids_by_name_with_table(x, m, exasol_to_sr, join_tables, current_table, current_alias, exasol_id_to_name) for x in obj) if x is not None]
        return [x for x in (map_field_ids_by_name_with_table(x, m, exasol_to_sr, join_tables, current_table, current_alias, exasol_id_to_name) for x in obj) if x is not None]
    elif isinstance(obj, dict):
        if 'source-table' in obj and 'alias' in obj:
            join_table_id = obj['source-table']
            join_alias = obj['alias']
            join_tables[join_alias] = join_table_id
            if JOIN_TYPE_OVERRIDE is not None:
                obj['strategy'] = JOIN_TYPE_OVERRIDE
            for k, v in list(obj.items()):
                mapped = map_field_ids_by_name_with_table(v, m, exasol_to_sr, join_tables, join_table_id, join_alias, exasol_id_to_name)
                if mapped is None:
                    del obj[k]
                else:
                    obj[k] = mapped
            return obj
        else:
            for k, v in list(obj.items()):
                mapped = map_field_ids_by_name_with_table(v, m, exasol_to_sr, join_tables, current_table, current_alias, exasol_id_to_name)
                if mapped is None:
                    del obj[k]
                else:
                    obj[k] = mapped
            return obj
    else:
        return obj

def main():
    m = MetabaseMigrator(MetabaseConfig(
        base_url='https://metabase.mrcr.io',
        username='YOUR_USERNAME_HERE',
        password='***REMOVED***'
    ))
    m.authenticate()
    table_mapping = load_table_mapping()
    q = m.get_question_details(5292)
    mbql = q['dataset_query']['query']
    # Step 1: Extract all field IDs with their table and alias context
    ids = []
    join_tables = {}
    extract_field_ids_with_table(mbql, ids, join_tables, current_table=q['dataset_query']['query'].get('source-table'), current_alias=None)
    print('Old field IDs with table and alias context:', ids)
    # Step 2: Map Exasol field ID -> column name
    exasol_id_to_name = {fid: get_field_name(m, fid) for fid, _, _ in ids}
    print('Exasol field ID to column name:', exasol_id_to_name)
    # Step 3: Map Exasol table ID/name to StarRocks table ID
    # Get all table IDs/names used in MBQL
    all_tables = set([table_id for _, table_id, _ in ids])
    exasol_table_id_to_name = {}
    for table_id in all_tables:
        # Try to get table name from Metabase
        resp = m.session.get(f"https://metabase.mrcr.io/api/table/{table_id}", headers={"X-Metabase-Session": m.session_token})
        if resp.status_code == 200:
            exasol_table_id_to_name[table_id] = resp.json().get('name')
        else:
            exasol_table_id_to_name[table_id] = None
    sr_table_ids = {}
    for table_id, table_name in exasol_table_id_to_name.items():
        sr_table_ids[table_id] = get_starrocks_table_id(m, table_id, table_name, table_mapping)
    print('Exasol table ID to StarRocks table ID:', sr_table_ids)
    # Step 4: Map (Exasol field ID, table, alias) -> StarRocks field ID
    exasol_to_sr = {}
    for (fid, table_id, alias) in ids:
        col_name = exasol_id_to_name[fid]
        sr_table_id = sr_table_ids.get(table_id)
        sr_id = get_starrocks_field_id(m, sr_table_id, col_name) if sr_table_id else None
        exasol_to_sr[(fid, table_id, alias)] = sr_id
    print('Exasol (field ID, table, alias) to StarRocks field ID:', exasol_to_sr)
    # Step 5: Update MBQL structure
    new_mbql = map_field_ids_by_name_with_table(mbql, m, exasol_to_sr, join_tables, current_table=q['dataset_query']['query'].get('source-table'), current_alias=None, exasol_id_to_name=exasol_id_to_name)
    # Step 6: Update all source-table references in MBQL to StarRocks table IDs
    def update_source_tables(obj):
        if isinstance(obj, dict):
            if 'source-table' in obj:
                exasol_table_id = obj['source-table']
                sr_table_id = sr_table_ids.get(exasol_table_id)
                if sr_table_id:
                    obj['source-table'] = sr_table_id
            for v in obj.values():
                update_source_tables(v)
        elif isinstance(obj, list):
            for x in obj:
                update_source_tables(x)
    update_source_tables(new_mbql)
    # Set root database_id and table_id to the first StarRocks table found
    sr_main_table = list(sr_table_ids.values())[0] if sr_table_ids else None
    q['dataset_query']['database'] = 16
    q['dataset_query']['query'] = new_mbql
    if sr_main_table:
        q['database_id'] = 16
        q['table_id'] = sr_main_table
    print('New MBQL structure with mapped field IDs:')
    print(json.dumps(new_mbql, indent=2))
    return q

if __name__ == '__main__':
    main() 