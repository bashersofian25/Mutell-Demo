"use client";

import { useState, useMemo } from "react";
import dynamic from "next/dynamic";
import { subDays } from "date-fns";
import { useAnalyticsSummary } from "@/hooks/useAnalyticsSummary";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import StatCard from "@/components/common/StatCard";
import ChartTab from "@/components/common/ChartTab";
import EmptyState from "@/components/common/EmptyState";
import TagBadge from "@/components/common/TagBadge";
import { formatNumber, formatPercent } from "@/lib/format";

const ReactApexChart = dynamic(() => import("react-apexcharts"), { ssr: false });

type DateRange = 7 | 14 | 30 | 90;

export default function AnalyticsPage() {
  const [days, setDays] = useState<DateRange>(30);

  const startDate = useMemo(() => subDays(new Date(), days).toISOString(), [days]);
  const endDate = useMemo(() => new Date().toISOString(), []);

  const { data, isLoading } = useAnalyticsSummary({
    date_from: startDate,
    date_to: endDate,
  });

  const d = data;
  const scores = d?.avg_scores;

  const scoreTrendOptions: ApexCharts.ApexOptions = {
    chart: { fontFamily: "Outfit, sans-serif", type: "line", toolbar: { show: false } },
    colors: ["#465fff", "#10b981", "#f59e0b", "#ef4444"],
    stroke: { curve: "smooth", width: 3 },
    dataLabels: { enabled: false },
    xaxis: {
      categories: d?.score_trend.map((t) => t.period.slice(5)) || [],
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    grid: { borderColor: "#f1f5f9" },
    tooltip: { x: { show: false } },
    yaxis: { max: 100, labels: { formatter: (v: number) => `${Math.round(v)}%` } },
    legend: { position: "top", horizontalAlign: "left", fontFamily: "Outfit" },
  };

  const scoreTrendSeries = [
    { name: "Overall", data: d?.score_trend.map((t) => t.overall ?? 0) || [] },
    { name: "Sentiment", data: d?.score_trend.map((t) => t.sentiment ?? 0) || [] },
    { name: "Politeness", data: d?.score_trend.map((t) => t.politeness ?? 0) || [] },
    { name: "Compliance", data: d?.score_trend.map((t) => t.compliance ?? 0) || [] },
  ];

  const radarOptions: ApexCharts.ApexOptions = {
    chart: { fontFamily: "Outfit, sans-serif", type: "radar", toolbar: { show: false } },
    colors: ["#465fff"],
    xaxis: {
      categories: ["Overall", "Sentiment", "Politeness", "Compliance", "Resolution", "Upselling", "Response", "Honesty"],
    },
    yaxis: { max: 100, tickAmount: 5 },
    plotOptions: {
      radar: {
        polygons: { strokeColors: "#e2e8f0", connectorColors: "#e2e8f0" },
      },
    },
    dataLabels: { enabled: true, formatter: (v: number) => `${Math.round(v)}` },
    stroke: { width: 2 },
    fill: { opacity: 0.15 },
  };

  const radarSeries = [
    {
      name: "Avg Score",
      data: scores
        ? [
            scores.overall ?? 0,
            scores.sentiment ?? 0,
            scores.politeness ?? 0,
            scores.compliance ?? 0,
            scores.resolution ?? 0,
            scores.upselling ?? 0,
            scores.response_time ?? 0,
            scores.honesty ?? 0,
          ]
        : [],
    },
  ];

  const tagBarOptions: ApexCharts.ApexOptions = {
    chart: { fontFamily: "Outfit, sans-serif", type: "bar", toolbar: { show: false } },
    colors: ["#ef4444"],
    plotOptions: {
      bar: { horizontal: true, columnWidth: "60%", borderRadius: 4, borderRadiusApplication: "end" },
    },
    dataLabels: { enabled: true, formatter: (v: number) => `${v}`, style: { fontSize: "12px" } },
    xaxis: {
      categories: d?.tag_stats.map((t) => t.label) || [],
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    grid: { yaxis: { lines: { show: false } }, borderColor: "#f1f5f9" },
    tooltip: { x: { show: false } },
  };

  const tagBarSeries = [{ name: "Incidents", data: d?.tag_stats.map((t) => t.count) || [] }];

  const langKeys = Object.keys(d?.language_distribution || {});
  const langVals = Object.values(d?.language_distribution || []);
  const donutOptions: ApexCharts.ApexOptions = {
    chart: { fontFamily: "Outfit, sans-serif", type: "donut" },
    labels: langKeys.map((k) => k.toUpperCase()),
    colors: ["#465fff", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"],
    legend: { position: "bottom", fontFamily: "Outfit" },
    dataLabels: { enabled: true, formatter: (v: number) => `${Math.round(v)}%` },
  };

  const statusData = d?.status_distribution || {};

  return (
    <div>
      <PageBreadcrumb pageTitle="Analytics" />

      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <ChartTab
          options={[
            { key: "7", label: "7 Days" },
            { key: "14", label: "14 Days" },
            { key: "30", label: "30 Days" },
            { key: "90", label: "90 Days" },
          ]}
          defaultOption={String(days)}
          onChange={(k) => setDays(Number(k) as DateRange)}
        />
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-[100px] rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />
          ))}
        </div>
      ) : !d || d.total_slots === 0 ? (
        <EmptyState title="No data" description="No evaluation data available for the selected period." />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
            <StatCard
              label="Total Slots"
              value={formatNumber(d.total_slots)}
              icon={
                <svg className="h-6 w-6 text-brand-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              }
            />
            <StatCard
              label="Avg Score"
              value={scores?.overall != null ? formatPercent(scores.overall) : "—"}
              icon={
                <svg className="h-6 w-6 text-success-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              }
            />
            <StatCard
              label="Evaluated"
              value={formatNumber(d.evaluated_slots)}
              icon={
                <svg className="h-6 w-6 text-warning-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
            />
            <StatCard
              label="Failed"
              value={formatNumber(d.failed_slots)}
              icon={
                <svg className="h-6 w-6 text-error-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
            />
          </div>

          <div className="grid grid-cols-1 gap-6 mb-6 xl:grid-cols-12">
            <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03] xl:col-span-8">
              <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
                <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Score Trend</h3>
              </div>
              <div className="p-4 sm:p-6">
                {d.score_trend.length > 0 ? (
                  <div className="max-w-full overflow-x-auto custom-scrollbar">
                    <div className="min-w-[500px]">
                      <ReactApexChart options={scoreTrendOptions} series={scoreTrendSeries} type="line" height={320} />
                    </div>
                  </div>
                ) : (
                  <EmptyState title="No trend data" description="Aggregated data not yet available." />
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03] xl:col-span-4">
              <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
                <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Score Breakdown</h3>
              </div>
              <div className="p-4 sm:p-6">
                <ReactApexChart options={radarOptions} series={radarSeries} type="radar" height={320} />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 mb-6 xl:grid-cols-12">
            <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03] xl:col-span-7">
              <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
                <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Tag Distribution</h3>
              </div>
              <div className="p-4 sm:p-6">
                {d.tag_stats.length > 0 ? (
                  <ReactApexChart options={tagBarOptions} series={tagBarSeries} type="bar" height={Math.max(200, d.tag_stats.length * 40)} />
                ) : (
                  <EmptyState title="No tags" description="No behavioral tags detected in this period." />
                )}
              </div>
            </div>

            <div className="xl:col-span-5 space-y-6">
              <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
                <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
                  <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Language Distribution</h3>
                </div>
                <div className="p-4 sm:p-6">
                  {langKeys.length > 0 ? (
                    <ReactApexChart options={donutOptions} series={langVals} type="donut" height={250} />
                  ) : (
                    <EmptyState title="No data" />
                  )}
                </div>
              </div>

              <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
                <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
                  <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Status Distribution</h3>
                </div>
                <div className="p-4 sm:p-6">
                  <div className="space-y-3">
                    {Object.entries(statusData).map(([status, count]) => (
                      <div key={status} className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">{status.replace("_", " ")}</span>
                        <div className="flex items-center gap-3">
                          <div className="w-32 h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full bg-brand-500"
                              style={{ width: `${Math.min(100, (count / d.total_slots) * 100)}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium text-gray-800 dark:text-white/90 w-8 text-right">{count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 mb-6 sm:grid-cols-3">
            <div className="rounded-2xl border border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950/30 p-5 sm:p-6">
              <p className="text-sm font-medium text-red-600 dark:text-red-400">Swearing Incidents</p>
              <p className="mt-2 text-3xl font-bold text-red-700 dark:text-red-300">{d.total_swearing_incidents}</p>
              <p className="mt-1 text-xs text-red-500 dark:text-red-400">
                across {d.evaluated_slots} evaluations
              </p>
            </div>
            <div className="rounded-2xl border border-purple-200 bg-purple-50 dark:border-purple-900 dark:bg-purple-950/30 p-5 sm:p-6">
              <p className="text-sm font-medium text-purple-600 dark:text-purple-400">Off-Topic Segments</p>
              <p className="mt-2 text-3xl font-bold text-purple-700 dark:text-purple-300">{d.total_off_topic_incidents}</p>
              <p className="mt-1 text-xs text-purple-500 dark:text-purple-400">
                across {d.evaluated_slots} evaluations
              </p>
            </div>
            <div className="rounded-2xl border border-orange-200 bg-orange-50 dark:border-orange-900 dark:bg-orange-950/30 p-5 sm:p-6">
              <p className="text-sm font-medium text-orange-600 dark:text-orange-400">Unavailable Items</p>
              <p className="mt-2 text-3xl font-bold text-orange-700 dark:text-orange-300">{d.total_unavailable_items}</p>
              <p className="mt-1 text-xs text-orange-500 dark:text-orange-400">
                {Object.keys(d.unavailable_item_frequency).length} unique items
              </p>
            </div>
          </div>

          {Object.keys(d.unavailable_item_frequency).length > 0 && (
            <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03] mb-6">
              <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
                <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Unavailable Items</h3>
              </div>
              <div className="max-w-full overflow-x-auto">
                <table className="min-w-full">
                  <thead className="border-b border-gray-100 dark:border-white/[0.05]">
                    <tr>
                      <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Item</th>
                      <th className="px-5 py-3 font-medium text-gray-500 text-start text-theme-xs dark:text-gray-400">Occurrences</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-white/[0.05]">
                    {Object.entries(d.unavailable_item_frequency).map(([item, count]) => (
                      <tr key={item}>
                        <td className="px-5 py-4 text-sm text-gray-800 dark:text-white/90">{item}</td>
                        <td className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">{count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {d.tag_stats.length > 0 && (
            <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
              <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
                <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Tags Overview</h3>
              </div>
              <div className="p-5 sm:p-6">
                <div className="flex flex-wrap gap-2">
                  {d.tag_stats.map((t) => (
                    <div key={t.tag} className="flex items-center gap-1.5">
                      <TagBadge tag={t.tag} />
                      <span className="text-xs text-gray-500 dark:text-gray-400">({t.count})</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
