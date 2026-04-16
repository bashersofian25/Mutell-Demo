export interface Note {
  id: string;
  tenant_id: string;
  user_id: string;
  slot_id: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface NoteCreateRequest {
  slot_id: string;
  content: string;
}

export interface NoteUpdateRequest {
  content: string;
}
