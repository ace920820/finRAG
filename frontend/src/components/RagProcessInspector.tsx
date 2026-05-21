import clsx from 'clsx';
import { Document, RetrievalSnapshot } from '../types';
import { MetadataRecord, RetrievalCascadeStage } from '../api/finrag';

interface RagProcessInspectorProps {
  snapshot: RetrievalSnapshot;
}

export function RagProcessInspector({ snapshot }: RagProcessInspectorProps) {
  const retrievalStages = snapshot.retrievalCascade ?? [];
  const rerankStages = snapshot.rerankCascade ?? [];
  const allStages = [...retrievalStages, ...rerankStages];
  const routeStage = retrievalStages.find(stage => stage.name === 'query_plan');
  const filterStage = retrievalStages.find(stage => stage.name === 'metadata_filter');
  const hierarchyStage = retrievalStages.find(stage => stage.name === 'hierarchy_drill_down');
  const hierarchyEvidence = hierarchyMetadata(snapshot.rerankDocs);

  return (
    <div className="space-y-3">
      <InspectorSection title="Query Plan">
        {snapshot.queryPlan ? (
          <div className="space-y-2">
            <div className="flex flex-wrap gap-1.5">
              <Badge label={snapshot.queryPlan.intent} tone="blue" />
              <Badge label={snapshot.queryPlan.task_type} tone="slate" />
              <Badge label={snapshot.queryPlan.retrieval_strategy} tone="emerald" />
            </div>
            <KeyValue label="Entities" value={snapshot.queryPlan.entities.map(entity => entity.canonical).join(', ') || 'none'} />
            <KeyValue label="Metrics" value={snapshot.queryPlan.metrics.map(metric => metric.canonical).join(', ') || 'none'} />
            <KeyValue label="Doc Types" value={snapshot.queryPlan.preferred_doc_types.join(', ') || 'none'} />
            <KeyValue label="Time" value={formatMetadata(snapshot.queryPlan.time_range as MetadataRecord | null | undefined)} />
            <TagList title="Expanded" items={snapshot.expandedTerms ?? []} />
            <TagList title="Sub queries" items={snapshot.subQueries ?? []} />
          </div>
        ) : (
          <EmptyState text="当前回答还没有 query plan 数据。" />
        )}
      </InspectorSection>

      <InspectorSection title="Route & Filters">
        {routeStage || filterStage ? (
          <div className="space-y-2">
            <KeyValue label="Route" value={stringValue(routeStage?.metadata.route) || routeStage?.method || 'unknown'} />
            <KeyValue label="Reason" value={stringValue(routeStage?.metadata.route_reason) || 'none'} />
            <KeyValue label="Filter Count" value={`${filterStage?.input_count ?? 0} -> ${filterStage?.output_count ?? 0}`} />
            {filterStage?.degraded && <Badge label={filterStage.fallback_reason || 'filters relaxed'} tone="amber" />}
            <MetadataBlock metadata={(filterStage?.metadata.applied_filters as MetadataRecord | undefined) ?? {}} />
          </div>
        ) : (
          <EmptyState text="暂无 route/filter trace。" />
        )}
      </InspectorSection>

      <InspectorSection title="Cascade">
        {allStages.length ? (
          <ol className="space-y-2">
            {allStages.map((stage, index) => (
              <li key={`${stage.name}-${index}`} className="rounded-md border border-slate-200 bg-white p-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="break-words text-[11px] font-semibold text-slate-700">{stage.name}</div>
                    <div className="break-words text-[10px] text-slate-500">{stage.method}</div>
                  </div>
                  <span className="shrink-0 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-600">
                    {stage.input_count} {'->'} {stage.output_count}
                  </span>
                </div>
                {stage.degraded && <div className="mt-1 text-[10px] text-amber-700">{stage.fallback_reason || 'degraded'}</div>}
              </li>
            ))}
          </ol>
        ) : (
          <EmptyState text="暂无 cascade trace。" />
        )}
      </InspectorSection>

      <InspectorSection title="Iterative Steps">
        {snapshot.iterativeTrace?.enabled && snapshot.iterativeTrace.steps.length ? (
          <div className="space-y-2">
            {snapshot.iterativeTrace.steps.map(step => (
              <div key={step.index} className="rounded-md border border-slate-200 bg-white p-2">
                <div className="flex items-center justify-between gap-2">
                  <Badge label={`${step.index}. ${step.purpose}`} tone="blue" />
                  {step.degraded && <Badge label={step.fallback_reason || 'degraded'} tone="amber" />}
                </div>
                <div className="mt-1 break-words text-[11px] text-slate-700">{step.retrieval_query}</div>
                <KeyValue label="Route" value={step.route || 'unknown'} />
                <TagList title="Evidence" items={step.selected_evidence_ids} />
              </div>
            ))}
          </div>
        ) : (
          <EmptyState text="当前查询为 single-pass，未启用 iterative retrieval。" />
        )}
      </InspectorSection>

      <InspectorSection title="Hierarchy & Drill-down">
        {hierarchyStage || hierarchyEvidence.length ? (
          <div className="space-y-2">
            {hierarchyStage && (
              <div className="rounded-md border border-emerald-200 bg-emerald-50 p-2 text-[11px] text-emerald-800">
                <div className="font-semibold">hierarchy_drill_down</div>
                <div>{hierarchyStage.input_count} parents/candidates {'->'} {hierarchyStage.output_count} child evidence</div>
              </div>
            )}
            {hierarchyEvidence.map(item => (
              <div key={item.id} className="rounded-md border border-slate-200 bg-white p-2">
                <div className="break-words text-[11px] font-semibold text-slate-700">{item.title}</div>
                <MetadataBlock metadata={item.metadata} compact />
              </div>
            ))}
          </div>
        ) : (
          <EmptyState text="当前证据没有 hierarchy metadata；如需全量展示，请先 reimport/reindex 已有语料。" />
        )}
      </InspectorSection>
    </div>
  );
}

function InspectorSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <h3 className="mb-2 text-[11px] font-bold uppercase tracking-normal text-slate-500">{title}</h3>
      {children}
    </section>
  );
}

function KeyValue({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="grid grid-cols-[72px_minmax(0,1fr)] gap-2 text-[11px] leading-relaxed">
      <span className="text-slate-400">{label}</span>
      <span className="break-words text-slate-700">{value || 'none'}</span>
    </div>
  );
}

function TagList({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div className="space-y-1">
      <div className="text-[10px] font-medium text-slate-400">{title}</div>
      <div className="flex flex-wrap gap-1">
        {items.slice(0, 8).map(item => <Badge key={item} label={item} tone="slate" />)}
      </div>
    </div>
  );
}

function Badge({ label, tone }: { label: string; tone: 'blue' | 'emerald' | 'amber' | 'slate' }) {
  return (
    <span className={clsx(
      'max-w-full break-words rounded px-1.5 py-0.5 text-[10px] font-medium',
      tone === 'blue' && 'bg-blue-50 text-blue-700',
      tone === 'emerald' && 'bg-emerald-50 text-emerald-700',
      tone === 'amber' && 'bg-amber-50 text-amber-700',
      tone === 'slate' && 'bg-slate-100 text-slate-600',
    )}>
      {label}
    </span>
  );
}

function EmptyState({ text }: { text: string }) {
  return <div className="rounded border border-dashed border-slate-200 bg-white p-2 text-[11px] leading-relaxed text-slate-400">{text}</div>;
}

function MetadataBlock({ metadata, compact = false }: { metadata: MetadataRecord; compact?: boolean }) {
  const entries = Object.entries(metadata).filter(([key, value]) => value !== null && value !== undefined && key !== 'source_path' && key !== 'table_json_path' && key !== 'table_csv_path');
  if (!entries.length) return <EmptyState text="无 metadata" />;
  return (
    <div className={clsx('grid gap-1', compact ? 'mt-1' : '')}>
      {entries.slice(0, compact ? 6 : 10).map(([key, value]) => (
        <KeyValue key={key} label={key} value={formatMetadata(value)} />
      ))}
    </div>
  );
}

function hierarchyMetadata(docs: Document[]): Array<{ id: string; title: string; metadata: MetadataRecord }> {
  return docs
    .filter(doc => {
      const metadata = doc.metadata ?? {};
      return Boolean(metadata.chunk_level || metadata.parent_id || metadata.child_ids || metadata.section_path || metadata.section_title);
    })
    .map(doc => ({ id: doc.id, title: doc.title, metadata: doc.metadata ?? {} }));
}

function formatMetadata(value: MetadataRecord | MetadataRecord[keyof MetadataRecord] | null | undefined): string {
  if (value === null || value === undefined) return '';
  if (Array.isArray(value)) return value.map(item => formatMetadata(item)).filter(Boolean).join(' / ');
  if (typeof value === 'object') return Object.entries(value).map(([key, item]) => `${key}: ${formatMetadata(item)}`).join(', ');
  return String(value);
}

function stringValue(value: MetadataRecord[keyof MetadataRecord] | undefined): string {
  if (typeof value === 'string') return value;
  if (value === null || value === undefined) return '';
  return formatMetadata(value);
}
