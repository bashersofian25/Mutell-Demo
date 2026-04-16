"use client";

import { useState, useMemo } from "react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { format } from "date-fns";
import { useAuth } from "@/stores/auth-store";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Badge from "@/components/ui/badge/Badge";
import Button from "@/components/ui/button/Button";
import StatCard from "@/components/common/StatCard";
import StatusBadge from "@/components/common/StatusBadge";
import ScoreBar from "@/components/common/ScoreBar";
import ChartTab from "@/components/common/ChartTab";
import { useDashboardStats } from "@/hooks/useDashboard";
import { useSlotList } from "@/hooks/useSlots";
import { useAggregations } from "@/hooks/useAggregations";
import { formatNumber, formatPercent, formatRelativeTime } from "@/lib/format";
import { subDays } from "date-fns";

const ReactApexChart = dynamic(() => import("react-apexcharts"), { ssr: false });

type DateRange = "1d" | "7d" | "30d";

function dateRangeDays(r: DateRange) {
  return r === "1d" ? 1 : r === "7d" ? 7 : 30;
}

function scoreColor(score: number) {
  if (score >= 85) return "text-success-500";
  if (score >= 70) return "text-success-600";
  if (score >= 55) return "text-warning-500";
  return "text-error-500";
}

export default function DashboardPage() {
  const [range, setRange] = useState<DateRange>("7d");
  const { user } = useAuth();
  const router = useRouter();

  const days = dateRangeDays(range);
  const startDate = useMemo(() => subDays(new Date(), days), [days]);
  const endDate = useMemo(() => new Date(), []);

  const { data: statsData, isLoading: statsLoading } = useDashboardStats();
  const stats = statsData?.data;

  const { data: slotsData, isLoading: slotsLoading } = useSlotList({ per_page: 10 });

  const { data: aggData } = useAggregations({
    period_type: "day",
    period_start: startDate.toISOString(),
    period_end: endDate.toISOString(),
  });

  const aggItems = aggData?.items || [];

  const chartOptions: ApexCharts.ApexOptions = {
    chart: { fontFamily: "Outfit, sans-serif", type: "bar", toolbar: { show: false } },
    colors: ["#465fff"],
    plotOptions: {
      bar: { horizontal: false, columnWidth: "60%", borderRadius: 6, borderRadiusApplication: "end" },
    },
    dataLabels: { enabled: false },
    xaxis: {
      categories: aggItems.map((a) => format(new Date(a.period_start), "MMM dd")),
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    grid: { yaxis: { lines: { show: true } }, borderColor: "#f1f5f9" },
    tooltip: { x: { show: false } },
    yaxis: { max: 100, labels: { formatter: (v: number) => `${Math.round(v)}%` } },
  };

  const chartSeries = [{ name: "Avg Score", data: aggItems.map((a) => a.avg_overall ?? 0) }];

  const metricEntries = useMemo(() => {
    if (aggItems.length === 0) return [];
    const latest = aggItems[aggItems.length - 1];
    return [
      { key: "Sentiment", val: latest.avg_sentiment },
      { key: "Politeness", val: latest.avg_politeness },
      { key: "Compliance", val: latest.avg_compliance },
      { key: "Resolution", val: latest.avg_resolution },
      { key: "Upselling", val: latest.avg_upselling },
      { key: "Response Time", val: latest.avg_response_time },
      { key: "Honesty", val: latest.avg_honesty },
    ].filter((m) => m.val !== null);
  }, [aggItems]);

  return (
    <div>
      <PageBreadcrumb pageTitle="Dashboard" />

      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-heading-6 font-bold text-gray-900 dark:text-white">
            Welcome back{user?.full_name ? `, ${user.full_name.split(" ")[0]}` : ""}
          </h1>
          <p className="mt-1 text-gray-500 dark:text-gray-400 text-sm">
            Here&apos;s what&apos;s happening with your POS interactions today.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4 mb-6">
        <StatCard
          label="Slots Today"
          value={statsLoading ? "..." : formatNumber(stats?.slots_today ?? 0)}
          icon={<svg className="h-6 w-6 text-brand-500 dark:text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
        />
        <StatCard
          label="Evaluated Today"
          value={statsLoading ? "..." : formatNumber(stats?.evaluated_today ?? 0)}
          icon={<svg className="h-6 w-6 text-success-500 dark:text-success-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        />
        <StatCard
          label="Pending Evaluations"
          value={statsLoading ? "..." : formatNumber(stats?.pending_evaluations ?? 0)}
          icon={<svg className="h-6 w-6 text-warning-500 dark:text-warning-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        />
        <StatCard
          label="Avg Score (Week)"
          value={statsLoading ? "..." : stats?.avg_score_week !== null ? formatPercent(stats?.avg_score_week ?? 0) : "—"}
          icon={<svg className="h-6 w-6 text-brand-500 dark:text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>}
        />
      </div>

      <div className="grid grid-cols-12 gap-4 md:gap-6 mb-6">
        <div className="col-span-12 xl:col-span-8">
          <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
            <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
              <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Score Trend</h3>
              <ChartTab
                options={[
                  { key: "1d", label: "1D" },
                  { key: "7d", label: "7D" },
                  { key: "30d", label: "30D" },
                ]}
                defaultOption={range}
                onChange={(key) => setRange(key as DateRange)}
              />
            </div>
            <div className="p-4 sm:p-6">
              {aggItems.length > 0 ? (
                <div className="max-w-full overflow-x-auto custom-scrollbar">
                  <div className="min-w-[500px]">
                    <ReactApexChart options={chartOptions} series={chartSeries} type="bar" height={250} />
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-[250px] text-gray-400 dark:text-gray-500">
                  No data available for this period
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="col-span-12 xl:col-span-4">
          <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03] h-full">
            <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
              <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Quick Stats</h3>
            </div>
            <div className="p-4 sm:p-6 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Active Terminals</span>
                <span className="text-sm font-semibold text-gray-800 dark:text-white/90">{stats?.active_terminals ?? 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Failed Today</span>
                <span className="text-sm font-semibold text-error-500">{stats?.failed_today ?? 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Slots This Week</span>
                <span className="text-sm font-semibold text-gray-800 dark:text-white/90">{formatNumber(stats?.slots_week ?? 0)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Avg Score (Month)</span>
                <span className={`text-sm font-semibold ${scoreColor(stats?.avg_score_month ?? 0)}`}>
                  {stats?.avg_score_month !== null ? formatPercent(stats?.avg_score_month ?? 0) : "—"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {metricEntries.length > 0 && (
        <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03] mb-6">
          <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
            <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Metrics Breakdown</h3>
          </div>
          <div className="p-4 sm:p-6 grid gap-4 sm:grid-cols-2">
            {metricEntries.map(({ key, val }) => (
              <ScoreBar key={key} label={key} score={val} />
            ))}
          </div>
        </div>
      )}

      <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
          <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Recent Slots</h3>
          <Button variant="outline" size="sm" onClick={() => router.push("/slots")}>
            View All
          </Button>
        </div>
        <div className="p-4 sm:p-6">
          {slotsLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-14 rounded-lg bg-gray-100 dark:bg-gray-800 animate-pulse" />
              ))}
            </div>
          ) : !slotsData?.items?.length ? (
            <div className="flex flex-col items-center py-8 text-gray-400 dark:text-gray-500">
              <svg className="h-10 w-10 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              <p className="text-sm">No slots yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {slotsData.items.map((slot) => (
                <div
                  key={slot.id}
                  className="flex items-center justify-between rounded-xl border border-gray-100 p-4 hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-white/[0.03] cursor-pointer transition-colors"
                  onClick={() => router.push(`/slots/${slot.id}`)}
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 dark:bg-gray-800">
                      <svg className="h-5 w-5 text-gray-500 dark:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-800 dark:text-white/90">{slot.id.slice(0, 8)}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{formatRelativeTime(slot.created_at)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge status={slot.status} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
