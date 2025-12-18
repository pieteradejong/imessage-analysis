export type Summary = {
  table_count: number;
  total_messages: number;
  total_chats: number;
  tables: Record<string, number>;
  db_path?: string;
  use_memory?: boolean;
};

export type LatestMessage = {
  date: string;
  text: string | null;
  is_from_me: boolean;
  chat_identifier: string | null;
  display_name: string | null;
  handle_id: string | null;
};

export type TopChat = {
  chat_identifier: string;
  display_name: string | null;
  message_count: number;
};

export type Contact = {
  rowid: number;
  id: string;
  country: string | null;
  service: string;
  uncanonicalized_id: string | null;
  person_centric_id: string | null;
};

export type ContactStats = {
  handle_id: string;
  from_me: {
    message_count: number;
    character_count: number;
    first_message: string | null;
    last_message: string | null;
    percentage?: number;
  };
  from_them: {
    message_count: number;
    character_count: number;
    first_message: string | null;
    last_message: string | null;
    percentage?: number;
  };
  total_messages: number;
  total_characters: number;
};

export type ContactChat = {
  chat_identifier: string;
  display_name: string | null;
  message_count: number;
};

export type ContactDetail = {
  contact: Contact;
  statistics: ContactStats;
  chats: ContactChat[];
};

const defaultBaseUrl = "http://127.0.0.1:8000";

export function getApiBaseUrl(): string {
  return import.meta.env.VITE_API_BASE_URL ?? defaultBaseUrl;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${getApiBaseUrl()}${path}`);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} for ${path}: ${text}`);
  }
  return (await res.json()) as T;
}

export function fetchSummary(): Promise<Summary> {
  return getJson<Summary>("/summary");
}

export function fetchLatest(limit: number): Promise<LatestMessage[]> {
  return getJson<LatestMessage[]>(`/latest?limit=${encodeURIComponent(limit)}`);
}

export function fetchTopChats(limit: number): Promise<TopChat[]> {
  return getJson<TopChat[]>(`/top-chats?limit=${encodeURIComponent(limit)}`);
}

export function fetchContacts(): Promise<Contact[]> {
  return getJson<Contact[]>("/contacts");
}

export function fetchContactDetail(handleId: string): Promise<ContactDetail> {
  return getJson<ContactDetail>(`/contacts/${encodeURIComponent(handleId)}`);
}

