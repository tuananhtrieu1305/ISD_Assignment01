# GENERATED from tieuluanfinal/notebooks/04_Multi_Agent.ipynb
"""Review/metrics/plots from saved80 outputs only; no inference or tuning."""

from pathlib import Path

import json,math,statistics

def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))

def wilson_interval(successes,n):
    if not n:return None
    z=1.96;p=successes/n;den=1+z*z/n
    middle=(p+z*z/(2*n))/den
    radius=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0,middle-radius),min(1,middle+radius)]

def score_saved_reviews(root,review_file):
    root=Path(root);folder=root/'artifacts/llm_v2/phase2/evaluation'
    raw=[load(p) for p in sorted((folder/'results').glob('*.json'))]
    if len(raw)!=80:raise ValueError('Need all80 outputs, including failures, before final scoring')
    mapping={(r['question_id'],r['label']):r['variant'] for r in load(folder/'review_mapping.json')}
    reviews=load(review_file)['rows'];review_by_key={}
    for row in reviews:
        key=(row['question_id'],mapping[(row['question_id'],row['label'])])
        if key in review_by_key or not row.get('reviewer'):raise ValueError('Missing reviewer or duplicate review')
        values=[row['scores'][name] for name in ['focus','correctness','completeness','limits']]
        if not all(type(v) is int and 0<=v<=2 for v in values) or type(row.get('critical_error')) is not bool:raise ValueError('Incomplete rubric')
        review_by_key[key]=row
    if len(review_by_key)!=80:raise ValueError('Need80 reviewed outputs')
    references=[json.loads(line) for line in (root/'datasets/llm_v2/evaluation_v1/held_out_reference.jsonl').read_text().splitlines()]
    gold={r['id']:r for r in references};scored=[]
    for row in raw:
        key=(row['question_id'],row['variant']);review=review_by_key[key];result=row['result'];points=sum(review['scores'].values())
        success=points>=6 and review['scores']['correctness']==2 and not review['critical_error']
        qrels={cid for ref in gold[row['question_id']]['reference_evidence'] if ref['relevance']==2 for cid in ref['relevant_chunk_ids']}
        ranked=[e['chunk_id'] for e in result.get('evidence',[])[:6]]
        matches=[i for i,cid in enumerate(ranked,1) if cid in qrels]
        citation_reviews=review.get('citation_reviews',[])
        if row['variant']=='agentic_rag' and result.get('claims'):
            expected={c['id'] for c in result['claims']}
            if {r['claim_id'] for r in citation_reviews}!=expected:raise ValueError('Review every emitted medical claim separately')
        supported=sum(r['status']=='supported' for r in citation_reviews)
        live=[r for r in result.get('usage',[]) if r.get('cache_status')=='live']
        tokens=[r['usage']['total_tokens'] for r in live if r.get('usage') and r['usage'].get('total_tokens') is not None]
        scored.append({'question_id':row['question_id'],'variant':row['variant'],'rubric_total':points,'success':success,
          'critical_error':review['critical_error'],'reviewer':review['reviewer'],'status':result['status'],
          'recall_at6':len(set(ranked)&qrels)/len(qrels) if qrels and row['variant']=='agentic_rag' else None,
          'mrr_at6':1/matches[0] if matches else (0 if qrels and row['variant']=='agentic_rag' else None),
          'citation_supported':supported,'citation_reviewed':len(citation_reviews),
          'latency_seconds':result.get('latency_ms',0)/1000 if result.get('latency_ms') is not None else None,
          'live_sdk_calls':len(live),'provider_tokens_live':sum(tokens) if tokens else None,'missing_usage_calls':len(live)-len(tokens)})
    summary=[]
    for variant in ['llm_direct','agentic_rag']:
        rows=[r for r in scored if r['variant']==variant];n=len(rows);wins=sum(r['success'] for r in rows)
        latencies=[r['latency_seconds'] for r in rows if r['latency_seconds'] is not None]
        q=[r for r in rows if r['recall_at6'] is not None]
        support=sum(r['citation_supported'] for r in rows);claims=sum(r['citation_reviewed'] for r in rows)
        summary.append({'variant':variant,'n':n,'success_count':wins,'task_success':wins/n,'wilson95':wilson_interval(wins,n),
          'rubric_mean':statistics.mean(r['rubric_total'] for r in rows),'p50_seconds':statistics.median(latencies) if latencies else None,
          'latency_n':len(latencies),'citation_support':support/claims if claims else None,'citation_support_numerator':support,
          'citation_support_denominator':claims,'recall_at6':statistics.mean(r['recall_at6'] for r in q) if q else None,
          'retrieval_n':len(q),'live_sdk_calls':sum(r['live_sdk_calls'] for r in rows),'free_cost_configured_usd':0})
    pairs={qid:{r['variant']:r['rubric_total'] for r in scored if r['question_id']==qid} for qid in gold}
    paired={'rag_win':sum(r['agentic_rag']>r['llm_direct'] for r in pairs.values()),'tie':sum(r['agentic_rag']==r['llm_direct'] for r in pairs.values()),
            'direct_win':sum(r['agentic_rag']<r['llm_direct'] for r in pairs.values()),'n':40}
    report={'rows':scored,'summary':summary,'paired':paired,'review_scope':'reviewers as named, not presumed clinical experts',
            'qrels_complete':False,'historical_scores_reused':False,'cache_and_live_separated':True}
    output=folder/'scored_summary.json'
    if output.exists():raise ValueError('Scored report exists; use a versioned review revision')
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report

def plot_saved_report(report,output_folder):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    folder=Path(output_folder);folder.mkdir(parents=True,exist_ok=True)
    rows=report['summary'];labels=['LLM trực tiếp','Đa agent + RAG'];colors=['#8796ad','#2857ed']
    fig,ax=plt.subplots(figsize=(7,4.5));ax.bar(labels,[r['rubric_mean'] for r in rows],color=colors);ax.set_ylim(0,8)
    ax.set_ylabel('Điểm rubric trung bình (0–8)');ax.set_title('Chất lượng trên40 câu hỏi cùng cặp')
    fig.tight_layout();fig.savefig(folder/'quality.png',dpi=180);plt.close(fig)
    rag=next(r for r in rows if r['variant']=='agentic_rag')
    fig,ax=plt.subplots(figsize=(7,4.5));names=['Claim có hỗ trợ','Recall@6 theo qrels'];values=[rag['citation_support'],rag['recall_at6']]
    for i,value in enumerate(values):
        if value is not None:ax.bar(i,value,color='#2857ed')
        else:ax.text(i,.05,'N/A',ha='center')
    ax.set_xticks(range(2),names);ax.set_ylim(0,1);ax.set_ylabel('Tỷ lệ (0–1)');ax.set_title('Chứng cứ của RAG · qrels chưa đầy đủ')
    fig.tight_layout();fig.savefig(folder/'evidence.png',dpi=180);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(9,4.5))
    axes[0].bar(labels,[r['p50_seconds'] or 0 for r in rows],color=colors);axes[0].set_ylabel('Giây');axes[0].set_title('Latency p50 toàn pipeline')
    axes[1].bar(labels,[r['live_sdk_calls'] for r in rows],color=colors);axes[1].set_ylabel('SDK calls mới');axes[1].set_title('Tổng overhead API')
    fig.tight_layout();fig.savefig(folder/'latency_calls.png',dpi=180);plt.close(fig)
    (folder/'FIGURE_GUIDE.md').write_text('''# Cách đọc ba hình

quality.png: trục ngang là hai nhánh, trục dọc điểm rubric trung bình0–8 trên cùng40 câu; điểm cao hơn chỉ phản ánh bộ benchmark nhỏ được review, không là độ chính xác lâm sàng.

evidence.png: chỉ dành cho RAG. Cột đầu là claim được người review xác nhận có evidence hỗ trợ / số claim đã review; cột sau là Recall@6 theo qrels có sẵn trên nhóm câu answerable. Qrels chưa exhaustive; N/A không được biến thành100%.

latency_calls.png: hình trái là p50 giây toàn pipeline, gồm chờ/retry trong phiên; thời gian chờ reset nhiều ngày ghi riêng ở raw result. Hình phải là tổng SDK call live của40 câu, cache tách riêng; không phải số HTTP request nếu SDK có hành vi mạng phụ. Free-tier cost cấu hình0USD, không là xác nhận hóa đơn.
''',encoding='utf-8')

