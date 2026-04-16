"use client";

import { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { format } from "date-fns";
import toast from "react-hot-toast";
import PageBreadcrumb from "@/components/common/PageBreadCrumb";
import Button from "@/components/ui/button/Button";
import TextArea from "@/components/form/input/TextArea";
import StatusBadge from "@/components/common/StatusBadge";
import ScoreBar from "@/components/common/ScoreBar";
import StatCard from "@/components/common/StatCard";
import ConfirmDialog from "@/components/common/ConfirmDialog";
import { useSlotDetail, useReEvaluate } from "@/hooks/useSlots";
import { useNotesList, useCreateNote, useUpdateNote, useDeleteNote } from "@/hooks/useNotes";
import { useIsTenantAdmin, useCanCreateNotes } from "@/lib/hooks";
import { formatPercent, formatDuration, formatRelativeTime, truncate } from "@/lib/format";
import TagBadge from "@/components/common/TagBadge";
import { Note } from "@/types/note";

export default function SlotDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [noteText, setNoteText] = useState("");
  const [editingNote, setEditingNote] = useState<Note | null>(null);
  const [editText, setEditText] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const isAdmin = useIsTenantAdmin();
  const canNote = useCanCreateNotes();

  const { data: slot, isLoading } = useSlotDetail(id);
  const { data: notesData, isLoading: notesLoading } = useNotesList({ slot_id: id });
  const createNote = useCreateNote();
  const updateNote = useUpdateNote();
  const deleteNote = useDeleteNote();
  const reEvaluate = useReEvaluate();

  if (isLoading) {
    return (
      <div>
        <PageBreadcrumb pageTitle="Loading..." />
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-40 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!slot) {
    return (
      <div>
        <PageBreadcrumb pageTitle="Not Found" />
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400 mb-4">Slot not found</p>
          <Button variant="outline" onClick={() => router.push("/slots")}>Go back</Button>
        </div>
      </div>
    );
  }

  const ev = slot.evaluation;

  const handleAddNote = () => {
    if (!noteText.trim()) return;
    createNote.mutate(
      { slot_id: id, content: noteText },
      { onSuccess: () => setNoteText("") }
    );
  };

  const handleUpdateNote = () => {
    if (!editingNote || !editText.trim()) return;
    updateNote.mutate(
      { id: editingNote.id, data: { content: editText } },
      { onSuccess: () => { setEditingNote(null); setEditText(""); } }
    );
  };

  const handleDeleteNote = () => {
    if (!deleteTarget) return;
    deleteNote.mutate(deleteTarget, { onSuccess: () => setDeleteTarget(null) });
  };

  return (
    <div>
      <PageBreadcrumb pageTitle={`Slot ${truncate(id, 8)}`} />

      <div className="flex items-center gap-2 mb-6">
        <Button variant="outline" size="sm" onClick={() => router.push("/slots")}>
          <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
          Back
        </Button>
        {isAdmin && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => reEvaluate.mutate(id)}
            disabled={reEvaluate.isPending}
          >
            {reEvaluate.isPending ? "Re-evaluating..." : "Re-evaluate"}
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 mb-6">
        <StatCard
          label="Overall Score"
          value={ev?.score_overall != null ? formatPercent(ev.score_overall) : "—"}
          icon={<svg className="h-6 w-6 text-brand-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>}
        />
        <StatCard
          label="Duration"
          value={slot.duration_secs ? formatDuration(slot.duration_secs) : "—"}
          icon={<svg className="h-6 w-6 text-success-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        />
        <StatCard
          label="Status"
          value=""
          icon={<svg className="h-6 w-6 text-warning-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
          className="relative"
        />
      </div>

      <div className="flex items-center gap-3 mb-6 flex-wrap">
        <StatusBadge status={slot.status} />
        <span className="text-sm text-gray-500 dark:text-gray-400">{format(new Date(slot.created_at), "PPpp")}</span>
        {(slot.tags || []).map((tag) => (
          <TagBadge key={tag} tag={tag} />
        ))}
        {slot.metadata && Object.keys(slot.metadata).length > 0 && (
          <span className="text-xs text-gray-400 dark:text-gray-500">
            {Object.entries(slot.metadata).map(([k, v]) => `${k}: ${v}`).join(" · ")}
          </span>
        )}
      </div>

      {ev && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mb-6">
          <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
            <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
              <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Score Breakdown</h3>
              {ev.ai_provider && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  via {ev.ai_provider} {ev.ai_model ? `(${ev.ai_model})` : ""}
                </p>
              )}
            </div>
            <div className="p-4 sm:p-6 space-y-3">
              <ScoreBar label="Overall" score={ev.score_overall} />
              <ScoreBar label="Sentiment" score={ev.score_sentiment} />
              <ScoreBar label="Politeness" score={ev.score_politeness} />
              <ScoreBar label="Compliance" score={ev.score_compliance} />
              <ScoreBar label="Resolution" score={ev.score_resolution} />
              <ScoreBar label="Upselling" score={ev.score_upselling} />
              <ScoreBar label="Response Time" score={ev.score_response_time} />
              <ScoreBar label="Honesty" score={ev.score_honesty} />
            </div>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
            <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
              <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Evaluation Details</h3>
            </div>
            <div className="p-4 sm:p-6 space-y-5 max-h-[600px] overflow-y-auto">
              {ev.summary && (
                <div>
                  <h4 className="text-sm font-medium text-gray-800 dark:text-white/90 mb-1">Summary</h4>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{ev.summary}</p>
                </div>
              )}
              {ev.strengths && ev.strengths.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-800 dark:text-white/90 mb-2 flex items-center gap-1.5">
                    <svg className="w-4 h-4 text-success-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    Strengths
                  </h4>
                  <ul className="space-y-1">{ev.strengths.map((s, i) => <li key={i} className="text-sm text-gray-500 dark:text-gray-400 pl-5 relative before:content-['•'] before:absolute before:left-1 before:text-gray-400">{s}</li>)}</ul>
                </div>
              )}
              {ev.weaknesses && ev.weaknesses.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-800 dark:text-white/90 mb-2 flex items-center gap-1.5">
                    <svg className="w-4 h-4 text-error-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    Weaknesses
                  </h4>
                  <ul className="space-y-1">{ev.weaknesses.map((w, i) => <li key={i} className="text-sm text-gray-500 dark:text-gray-400 pl-5 relative before:content-['•'] before:absolute before:left-1 before:text-gray-400">{w}</li>)}</ul>
                </div>
              )}
              {ev.recommendations && ev.recommendations.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-800 dark:text-white/90 mb-2 flex items-center gap-1.5">
                    <svg className="w-4 h-4 text-warning-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
                    Recommendations
                  </h4>
                  <ul className="space-y-1">{ev.recommendations.map((r, i) => <li key={i} className="text-sm text-gray-500 dark:text-gray-400 pl-5 relative before:content-['•'] before:absolute before:left-1 before:text-gray-400">{r}</li>)}</ul>
                </div>
              )}
              {ev.flags && ev.flags.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-800 dark:text-white/90 mb-2 flex items-center gap-1.5">
                    <svg className="w-4 h-4 text-warning-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" /></svg>
                    Flags
                  </h4>
                  <ul className="space-y-1">{ev.flags.map((f, i) => <li key={i} className="text-sm text-gray-500 dark:text-gray-400 pl-5 relative before:content-['•'] before:absolute before:left-1 before:text-gray-400">{f}</li>)}</ul>
                </div>
              )}
              {ev.unavailable_items && ev.unavailable_items.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-800 dark:text-white/90 mb-2 flex items-center gap-1.5">
                    <svg className="w-4 h-4 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                    Unavailable Items ({ev.unavailable_items.length})
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {ev.unavailable_items.map((item, i) => (
                      <span key={i} className="inline-flex items-center rounded-full bg-orange-50 px-2.5 py-0.5 text-xs font-medium text-orange-700 dark:bg-orange-500/15 dark:text-orange-400">{item}</span>
                    ))}
                  </div>
                </div>
              )}
              {ev.swearing_count != null && ev.swearing_count > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-800 dark:text-white/90 mb-2 flex items-center gap-1.5">
                    <svg className="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" /></svg>
                    Swearing ({ev.swearing_count} occurrence{ev.swearing_count !== 1 ? "s" : ""})
                  </h4>
                  <ul className="space-y-1">{(ev.swearing_instances || []).map((s, i) => <li key={i} className="text-sm text-gray-500 dark:text-gray-400 pl-5 relative before:content-['•'] before:absolute before:left-1 before:text-red-400">{s}</li>)}</ul>
                </div>
              )}
              {ev.off_topic_count != null && ev.off_topic_count > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-800 dark:text-white/90 mb-2 flex items-center gap-1.5">
                    <svg className="w-4 h-4 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
                    Off-Topic Talk ({ev.off_topic_count} segment{ev.off_topic_count !== 1 ? "s" : ""})
                  </h4>
                  <ul className="space-y-1">{(ev.off_topic_segments || []).map((s, i) => <li key={i} className="text-sm text-gray-500 dark:text-gray-400 pl-5 relative before:content-['•'] before:absolute before:left-1 before:text-purple-400">{s}</li>)}</ul>
                </div>
              )}
              {ev.speaker_segments && ev.speaker_segments.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-800 dark:text-white/90 mb-2 flex items-center gap-1.5">
                    <svg className="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                    Speaker Segments
                  </h4>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {ev.speaker_segments.map((seg, i) => (
                      <div key={i} className="flex items-start gap-2">
                        <span className={`shrink-0 text-xs font-semibold px-1.5 py-0.5 rounded ${
                          seg.speaker === "employee" ? "bg-blue-50 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400" :
                          seg.speaker === "customer" ? "bg-green-50 text-green-700 dark:bg-green-500/15 dark:text-green-400" :
                          "bg-gray-50 text-gray-700 dark:bg-gray-500/15 dark:text-gray-400"
                        }`}>{seg.speaker}</span>
                        <p className="text-sm text-gray-500 dark:text-gray-400">{seg.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {slot.raw_text && (
        <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03] mb-6">
          <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
            <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Transcript</h3>
          </div>
          <div className="p-4 sm:p-6">
            <pre className="whitespace-pre-wrap text-sm text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-900 rounded-xl p-4 max-h-96 overflow-y-auto font-sans">
              {slot.raw_text}
            </pre>
          </div>
        </div>
      )}

      <div className="rounded-2xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-white/[0.03]">
        <div className="px-6 py-5 border-b border-gray-100 dark:border-gray-800">
          <h3 className="text-base font-medium text-gray-800 dark:text-white/90">Notes</h3>
        </div>
        <div className="p-4 sm:p-6 space-y-4">
          {canNote && (
            <div className="flex gap-3">
              <TextArea
                placeholder="Add a note..."
                value={noteText}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNoteText(e.target.value)}
                className="flex-1"
                rows={2}
              />
              <Button
                onClick={handleAddNote}
                disabled={!noteText.trim() || createNote.isPending}
              >
                {createNote.isPending ? "Adding..." : "Add"}
              </Button>
            </div>
          )}
          {notesLoading ? (
            <div className="space-y-3">{[1, 2].map((i) => <div key={i} className="h-16 rounded-lg bg-gray-100 dark:bg-gray-800 animate-pulse" />)}</div>
          ) : !notesData?.items?.length ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">No notes yet</p>
          ) : (
            <div className="space-y-3">
              {notesData.items.map((note) => (
                <div key={note.id} className="rounded-xl border border-gray-100 dark:border-gray-800 p-4">
                  {editingNote?.id === note.id ? (
                    <div className="space-y-3">
                      <TextArea
                        value={editText}
                        onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setEditText(e.target.value)}
                        rows={2}
                      />
                      <div className="flex gap-2">
                        <Button size="sm" onClick={handleUpdateNote} disabled={updateNote.isPending}>
                          {updateNote.isPending ? "Saving..." : "Save"}
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setEditingNote(null)}>Cancel</Button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <p className="text-sm text-gray-800 dark:text-white/90">{note.content}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">{formatRelativeTime(note.created_at)}</p>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <button
                          onClick={() => { setEditingNote(note); setEditText(note.content); }}
                          className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                        </button>
                        <button
                          onClick={() => setDeleteTarget(note.id)}
                          className="p-1.5 rounded-lg hover:bg-error-50 dark:hover:bg-error-500/10 text-gray-400 hover:text-error-500 transition-colors"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDeleteNote}
        title="Delete Note"
        message="Are you sure you want to delete this note? This action cannot be undone."
        confirmLabel="Delete"
        variant="danger"
        isLoading={deleteNote.isPending}
      />
    </div>
  );
}
