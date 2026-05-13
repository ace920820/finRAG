
def test_documents_endpoint(client):
    response = client.get('/api/documents')
    assert response.status_code == 200
    payload = response.json()
    assert 'total' in payload
    assert 'documents' in payload
    assert payload['total'] == len(payload['documents'])
    assert payload['total'] >= 4

    required_fields = {'doc_id', 'title', 'doc_type', 'company', 'date', 'chunk_count'}
    companies = {item['company'] for item in payload['documents']}
    assert '贵州茅台' in companies
    assert '宁德时代' in companies
    for item in payload['documents']:
        assert required_fields.issubset(item.keys())
