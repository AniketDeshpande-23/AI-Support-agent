import { useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { RefreshCw, ShieldCheck } from 'lucide-react';
import { useMetrics, type MetricsBundle } from '../hooks/useMetrics';
import { KpiCard } from '../components/KpiCard';
import { EmptyState, ErrorState, LoadingState } from '../components/States';
import { PRIORITY_COLORS, PRIORITY_ORDER, categoryColor, isUrgentRoute } from '../constants';
import type { Ticket } from '../types';

export function DashboardView() {
  const [auto, setAuto] = useState(false);
  const { data, loading, error, refresh } = useMetrics(auto ? 15000 : null);

  if (loading && !data) {
    return (
      <div className="mx-auto w-full max-w-[1280px]">
        <LoadingState label="Loading metrics…" />
      </div>
    );
  }
  if (error && !data) {
    return (
      <div className="mx-auto w-full max-w-[1280px]">
        <ErrorState error={error} onRetry={() => void refresh()} />
      </div>
    );
  }
  if (!data) return null;

  return <DashboardBody data={data} auto={auto} onToggleAuto={() => setAuto((a) => !a)} onRefresh={() => void refresh()} loading={loading} />;
}

function DashboardBody({
  data,
  auto,
  onToggleAuto,
  onRefresh,
  loading,
}: {
  data: MetricsBundle;
  auto: boolean;
  onToggleAuto: () => void;
  onRefresh: () => void;
  loading: boolean;
}) {
  const { metrics, tickets } = data;

  const groundingPct = useMemo(() => {
    if (tickets.length === 0) return null;
    const g = tickets.filter((t) => t.grounded).length;
    return Math.round((g / tickets.length) * 100);
  }, [tickets]);

  const highCrit = (metrics.by_priority.Critical ?? 0) + (metrics.by_priority.High ?? 0);

  const categoryData = useMemo(
    () =>
      Object.entries(metrics.by_category)
        .map(([name, value], i) => ({ name, value, color: categoryColor(name, i) }))
        .sort((a, b) => b.value - a.value),
    [metrics.by_category],
  );

  const priorityData = useMemo(
    () =>
      PRIORITY_ORDER.map((p) => ({
        name: p,
        value: metrics.by_priority[p] ?? 0,
        color: PRIORITY_COLORS[p],
      })).filter((d) => d.value > 0 || true),
    [metrics.by_priority],
  );

  const histogram = useMemo(() => bucketConfidence(tickets), [tickets]);
  const routes = useMemo(() => topRoutes(tickets), [tickets]);

  const hasCategory = categoryData.length > 0;

  return (
    <div className="mx-auto w-full max-w-[1280px] space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[18px] font-semibold tracking-tight text-text">Dashboard</h2>
          <p className="font-mono text-[11px] text-faint">
            {metrics.total} tickets analyzed · sample of {tickets.length} for derived metrics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onToggleAuto}
            className="rounded-md border border-hairline bg-card px-2.5 py-1.5 text-[12px] text-muted transition-colors duration-150 hover:border-accent hover:text-text"
            style={auto ? { borderColor: '#818cf8', color: '#818cf8' } : undefined}
          >
            Auto-refresh {auto ? 'on' : 'off'}
          </button>
          <button
            type="button"
            onClick={onRefresh}
            className="inline-flex items-center gap-1.5 rounded-md border border-hairline bg-card px-2.5 py-1.5 text-[12px] text-muted transition-colors duration-150 hover:border-accent hover:text-text"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : undefined} />
            Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard label="Total tickets" value={metrics.total} sub="all time" accent="#818cf8" />
        <KpiCard
          label="Avg confidence"
          value={`${Math.round(metrics.avg_confidence)}%`}
          sub="model self-report"
          accent="#34d399"
        />
        <KpiCard
          label="High + Critical"
          value={highCrit}
          sub={`${pct(highCrit, metrics.total)}% of total`}
          accent="#fb923c"
        />
        <KpiCard
          label="Grounding rate"
          value={groundingPct === null ? '—' : `${groundingPct}%`}
          sub={`from ${tickets.length} recent`}
          accent="#34d399"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard title="By category" right={hasCategory ? `${categoryData.length} types` : ''}>
          {hasCategory ? (
            <div className="flex items-center gap-4">
              <ResponsiveContainer width="55%" height={220}>
                <PieChart>
                  <Pie
                    data={categoryData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={58}
                    outerRadius={88}
                    paddingAngle={2}
                    stroke="#0f1117"
                    strokeWidth={2}
                  >
                    {categoryData.map((d) => (
                      <Cell key={d.name} fill={d.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<DarkTooltip suffix="tickets" />} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex-1">
                <div className="tnum mb-3 font-mono text-[26px] font-bold text-text">
                  {metrics.total}
                  <span className="ml-1 text-[12px] font-normal text-faint">total</span>
                </div>
                <ul className="space-y-1.5">
                  {categoryData.map((d) => (
                    <li key={d.name} className="flex items-center gap-2 text-[12px]">
                      <span
                        className="h-2 w-2 shrink-0 rounded-[2px]"
                        style={{ backgroundColor: d.color }}
                      />
                      <span className="flex-1 truncate text-muted">{d.name}</span>
                      <span className="tnum font-mono text-faint">{d.value}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <EmptyState title="No category data" hint="Analyze tickets to populate this chart." />
          )}
        </ChartCard>

        <ChartCard title="By priority">
          {priorityData.some((d) => d.value > 0) ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={priorityData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#9ca3af', fontSize: 11 }}
                  axisLine={{ stroke: '#262a36' }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#6b7280', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                />
                <Tooltip cursor={{ fill: 'rgba(129,140,248,0.06)' }} content={<DarkTooltip suffix="tickets" />} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={56}>
                  {priorityData.map((d) => (
                    <Cell key={d.name} fill={d.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState title="No priority data" />
          )}
        </ChartCard>

        <ChartCard title="Confidence distribution">
          {tickets.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={histogram} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <XAxis
                  dataKey="bucket"
                  tick={{ fill: '#9ca3af', fontSize: 10 }}
                  axisLine={{ stroke: '#262a36' }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#6b7280', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                />
                <Tooltip cursor={{ fill: 'rgba(129,140,248,0.06)' }} content={<DarkTooltip suffix="tickets" />} />
                <Bar dataKey="value" fill="#818cf8" radius={[4, 4, 0, 0]} maxBarSize={48} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState
              icon={<ShieldCheck size={24} />}
              title="No confidence data"
              hint="Derived from recent tickets."
            />
          )}
        </ChartCard>

        <ChartCard title="Top routes" right={routes.length ? `${routes.length}` : ''}>
          {routes.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart
                data={routes}
                layout="vertical"
                margin={{ top: 4, right: 16, left: 4, bottom: 0 }}
              >
                <XAxis type="number" hide allowDecimals={false} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={150}
                  tick={{ fill: '#9ca3af', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip cursor={{ fill: 'rgba(129,140,248,0.06)' }} content={<DarkTooltip suffix="tickets" />} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={22}>
                  {routes.map((r) => (
                    <Cell key={r.name} fill={r.urgent ? '#f87171' : '#818cf8'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState title="No routing data" hint="Routes are derived from recent tickets." />
          )}
        </ChartCard>
      </div>
    </div>
  );
}

function ChartCard({
  title,
  right,
  children,
}: {
  title: string;
  right?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-hairline bg-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <span className="label-eyebrow">{title}</span>
        {right && <span className="tnum font-mono text-[11px] text-faint">{right}</span>}
      </div>
      {children}
    </div>
  );
}

interface TooltipPayloadItem {
  name?: string | number;
  value?: string | number;
  payload?: { name?: string; bucket?: string };
}

function DarkTooltip({
  active,
  payload,
  suffix,
}: {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  suffix?: string;
}) {
  if (!active || !payload || payload.length === 0) return null;
  const item = payload[0];
  const label = item.payload?.name ?? item.payload?.bucket ?? item.name ?? '';
  return (
    <div className="rounded-md border border-hairline bg-[#0f1117] px-2.5 py-1.5 shadow-lg">
      <div className="text-[11px] text-muted">{String(label)}</div>
      <div className="tnum font-mono text-[13px] font-semibold text-text">
        {String(item.value)} {suffix}
      </div>
    </div>
  );
}

function bucketConfidence(tickets: Ticket[]) {
  const labels = ['0-20', '20-40', '40-60', '60-80', '80-100'];
  const counts = [0, 0, 0, 0, 0];
  for (const t of tickets) {
    const idx = Math.min(4, Math.floor(t.confidence / 20));
    counts[idx] += 1;
  }
  return labels.map((bucket, i) => ({ bucket, value: counts[i] }));
}

function topRoutes(tickets: Ticket[]) {
  const map = new Map<string, { value: number; urgent: boolean }>();
  for (const t of tickets) {
    const key = t.route_to || 'Unassigned';
    const prev = map.get(key) ?? { value: 0, urgent: isUrgentRoute(key) };
    prev.value += 1;
    map.set(key, prev);
  }
  return Array.from(map.entries())
    .map(([name, v]) => ({ name, value: v.value, urgent: v.urgent }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 6);
}

function pct(n: number, total: number): number {
  if (total <= 0) return 0;
  return Math.round((n / total) * 100);
}
