from fastapi.testclient import TestClient

from app.main import create_app


def test_debug_retrieval_endpoint_returns_retrieval_and_rerank_sections():
    client = TestClient(create_app())
    response = client.post('/api/debug/retrieval', json={'query': '宁德时代近期有哪些经营风险？'})
    assert response.status_code == 200
    payload = response.json()
    assert 'retrieval_complete' in payload
    assert 'rerank_complete' in payload
    assert payload['route'] == 'research_report_analysis'
    assert payload['route_reason']
    assert isinstance(payload['applied_filters'], dict)
    assert payload['filter_before_count'] is not None
    assert payload['filter_after_count'] is not None
    assert 'filters_relaxed' in payload
    assert payload['retrieval_complete']['bm25_results']
    assert payload['retrieval_complete']['vector_results'] or payload['retrieval_complete']['vector_error']
    assert payload['retrieval_complete']['fused_top20']
    assert payload['iterative_trace']['enabled'] is True
    assert payload['iterative_trace']['steps'][0]['purpose'] == 'background_facts'
    assert payload['iterative_trace']['steps'][0]['route'] == 'research_report_analysis'
    assert payload['retrieval_complete']['iterative_trace']['steps']
    assert payload['rerank_complete']['top5']
    assert [stage['name'] for stage in payload['cascade_trace']] == [
        'query_plan',
        'coarse_recall',
        'metadata_filter',
        'hierarchy_drill_down',
        'fusion',
        'iterative_merge',
        'rerank',
        'final_evidence',
    ]
    metadata_filter = next(stage for stage in payload['cascade_trace'] if stage['name'] == 'metadata_filter')
    assert metadata_filter['metadata']['applied_at'] == 'post_recall'
    assert 'per_channel' in metadata_filter['metadata']
    coarse_recall = next(stage for stage in payload['cascade_trace'] if stage['name'] == 'coarse_recall')
    assert 'per_channel' in coarse_recall['metadata']
    iterative_merge = next(stage for stage in payload['cascade_trace'] if stage['name'] == 'iterative_merge')
    assert iterative_merge['kind'] == 'augment'
    hierarchy = next(stage for stage in payload['cascade_trace'] if stage['name'] == 'hierarchy_drill_down')
    assert hierarchy['kind'] == 'augment'
    assert 'parent_candidates_found' in hierarchy['metadata']
    final_evidence = payload['cascade_trace'][-1]
    assert final_evidence['output_count'] <= final_evidence['input_count']
    assert 'dropped_duplicate_count' in final_evidence['metadata']
    assert payload['retrieval_complete']['cascade_trace']
    assert payload['rerank_complete']['cascade_trace']
    assert all('method' in stage and 'input_count' in stage and 'output_count' in stage for stage in payload['cascade_trace'])
