export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="rounded-lg border border-dashed border-[var(--border-strong)] py-12 text-center">
      <p className="text-sm font-medium text-[var(--text-secondary)]">{title}</p>
      {description && <p className="mt-1 text-xs text-[var(--text-muted)]">{description}</p>}
    </div>
  );
}