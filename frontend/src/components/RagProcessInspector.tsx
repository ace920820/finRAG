import clsx from 'clsx';
import { Document, RetrievalSnapshot } from '../types';
import { CascadeStageName, MetadataRecord, RetrievalCascadeStage } from '../api/finrag';

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
  const evidenceStage = rerankStages.find(stage => stage.name === 'final_evidence');
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
            <KeyValue label="Filter Count" value={`${filterStage?.input_count ?? 0} → ${filterStage?.output_count ?? 0} (三路总和)`} />
            {filterStage?.degraded && <Badge label={filterStage.fallback_reason || 'filters relaxed'} tone="amber" />}
            {filterStage && <StageBreakdown stage={filterStage} />}
            <div className="text-[10px] font-medium text-slate-400">Applied filters</div>
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
                  <CountBadge stage={stage} />
                </div>
                {stage.degraded && <div className="mt-1 text-[10px] text-amber-700">{stage.fallback_reason || 'degraded'}</div>}
                <StageBreakdown stage={stage} />
              </li>
            ))}
          </ol>
        ) : (
          <EmptyState text="暂无 cascade trace。" />
        )}
      </InspectorSection>

      <InspectorSection title="Evidence Compression">
        {evidenceStage ? (
          <EvidenceCompression stage={evidenceStage} />
        ) : (
          <EmptyState text="暂无 evidence compression trace。" />
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
                <div className="flex items-center justify-between">
                  <div className="font-semibold">hierarchy_drill_down</div>
                  <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] text-emerald-800">
                    +{hierarchyStage.output_count} children
                  </span>
                </div>
                <div className="mt-0.5">
                  parents found: {(hierarchyStage.metadata.parent_candidates_found as number | undefined) ?? hierarchyStage.input_count}
                  {' · '}
                  children expanded: {hierarchyStage.output_count}
                </div>
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

function EvidenceCompression({ stage }: { stage: RetrievalCascadeStage }) {
  const metadata = stage.metadata;
  const originalChars = numberValue(metadata.original_char_count);
  const compactChars = numberValue(metadata.compact_char_count);
  const ratio = numberValue(metadata.compression_ratio);
  const savedPercent = ratio === undefined ? undefined : Math.max(0, Math.round((1 - ratio) * 100));

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-3 gap-1.5">
        <MetricTile label="Raw chars" value={formatNumber(originalChars)} />
        <MetricTile label="Compact chars" value={formatNumber(compactChars)} />
        <MetricTile label="Saved" value={savedPercent === undefined ? 'none' : `${savedPercent}%`} />
      </div>
      <div className="rounded bg-white px-2 py-1 text-[10px] text-slate-600">
        <div className="flex justify-between">
          <span className="text-slate-500">Evidence</span>
          <span className="text-slate-700">{stage.input_count} → {stage.output_count}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">Duplicates dropped</span>
          <span className="text-slate-700">{formatNumber(numberValue(metadata.dropped_duplicate_count))}</span>
        </div>
      </div>
      <div className="text-[10px] leading-relaxed text-slate-500">
        Final prompt evidence is deduped and compacted after rerank while preserving citation metadata.
      </div>
    </div>
  );
}

function MetricTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded border border-slate-200 bg-white px-2 py-1.5">
      <div className="break-words text-[9px] font-medium text-slate-400">{label}</div>
      <div className="mt-0.5 break-words text-[12px] font-semibold text-slate-700">{value}</div>
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

function CountBadge({ stage }: { stage: RetrievalCascadeStage }) {
  const isAugment = stage.kind === 'augment';
  const label = isAugment
    ? `+${stage.output_count} ${augmentLabelFor(stage.name)}`
    : `${stage.input_count} → ${stage.output_count}`;
  return (
    <span className={clsx(
      'shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium',
      isAugment ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600',
    )}>
      {label}
    </span>
  );
}

function augmentLabelFor(name: CascadeStageName): string {
  if (name === 'hierarchy_drill_down') return 'children';
  if (name === 'iterative_merge') return 'merged';
  return 'added';
}

function StageBreakdown({ stage }: { stage: RetrievalCascadeStage }) {
  const perChannel = stage.metadata.per_channel as Record<string, MetadataRecord> | undefined;
  const perStep = stage.metadata.per_step as MetadataRecord[] | undefined;
  const evidencePackMeta = stage.name === 'final_evidence' ? stage.metadata : undefined;

  if (perChannel) {
    return (
      <div className="mt-1.5 grid gap-0.5 rounded bg-slate-50 px-2 py-1 text-[10px] text-slate-600">
        <div className="mb-0.5 text-[9px] uppercase tracking-wide text-slate-400">三路明细</div>
        {Object.entries(perChannel).map(([channel, stats]) => {
          const before = (stats as MetadataRecord).before;
          const after = (stats as MetadataRecord).after;
          const count = (stats as MetadataRecord).count;
          const error = (stats as MetadataRecord).error;
          const value = before !== undefined && after !== undefined
            ? `${String(before)} → ${String(after)}`
            : String(count ?? 0);
          return (
            <div key={channel} className="flex justify-between">
              <span className="text-slate-500">{channel}</span>
              <span className="text-slate-700">
                {value}{error ? ' ⚠' : ''}
              </span>
            </div>
          );
        })}
      </div>
    );
  }

  if (perStep) {
    return (
      <div className="mt-1.5 grid gap-0.5 rounded bg-slate-50 px-2 py-1 text-[10px] text-slate-600">
        <div className="mb-0.5 text-[9px] uppercase tracking-wide text-slate-400">迭代步骤明细</div>
        {perStep.map((step, i) => (
          <div key={i} className="flex justify-between">
            <span className="text-slate-500">
              step {String(step.index ?? i + 1)} · {String(step.purpose ?? '')}
            </span>
            <span className="text-slate-700">{String(step.candidates ?? 0)} 候选</span>
          </div>
        ))}
        {stage.metadata.deduped_total !== undefined && (
          <div className="mt-0.5 flex justify-between border-t border-slate-200 pt-0.5">
            <span className="text-slate-500">合并去重后</span>
            <span className="font-medium text-slate-700">{String(stage.metadata.deduped_total)}</span>
          </div>
        )}
      </div>
    );
  }

  if (stage.name === 'hierarchy_drill_down') {
    const found = stage.metadata.parent_candidates_found as number | undefined;
    if (found !== undefined) {
      return (
        <div className="mt-1.5 rounded bg-slate-50 px-2 py-1 text-[10px] text-slate-600">
          <div className="flex justify-between">
            <span className="text-slate-500">父级候选数</span>
            <span className="text-slate-700">{found}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">扩展子证据</span>
            <span className="text-slate-700">+{stage.output_count}</span>
          </div>
        </div>
      );
    }
  }

  if (evidencePackMeta && evidencePackMeta.dropped_duplicate_count !== undefined) {
    return (
      <div className="mt-1.5 rounded bg-slate-50 px-2 py-1 text-[10px] text-slate-600">
        <div className="flex justify-between">
          <span className="text-slate-500">原始 top-k</span>
          <span className="text-slate-700">{String(evidencePackMeta.original_count ?? 0)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">压缩后</span>
          <span className="text-slate-700">{String(evidencePackMeta.compressed_count ?? 0)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">去重移除</span>
          <span className="text-slate-700">{String(evidencePackMeta.dropped_duplicate_count ?? 0)}</span>
        </div>
      </div>
    );
  }

  return null;
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

function numberValue(value: MetadataRecord[keyof MetadataRecord] | undefined): number | undefined {
  return typeof value === 'number' && Number.isFinite(value) ? value : undefined;
}

function formatNumber(value: number | undefined): string {
  return value === undefined ? 'none' : value.toLocaleString();
}

function stringValue(value: MetadataRecord[keyof MetadataRecord] | undefined): string {
  if (typeof value === 'string') return value;
  if (value === null || value === undefined) return '';
  return formatMetadata(value);
}
