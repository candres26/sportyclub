export type TenantSummary = {
  id: string;
  slug: string;
  name: string;
};

export type Me = {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
  tenant: TenantSummary;
};

export type User = {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  last_login_at: string | null;
  roles: string[];
};

export type Role = {
  id: string;
  name: string;
  description: string | null;
  is_system: boolean;
  permissions: string[];
};

export type Permission = {
  id: string;
  code: string;
  description: string | null;
};

export type Invitation = {
  id: string;
  email: string;
  role_id: string;
  role_name: string | null;
  expires_at: string;
  accepted_at: string | null;
  created_at: string;
};

export type Page<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};

export type PlatformMe = {
  id: string;
  email: string;
  full_name: string;
};

export type Club = {
  id: string;
  slug: string;
  name: string;
  is_active: boolean;
  created_at: string;
};

export type ClubCreated = Club & {
  invite_url: string | null;
};

export type PlatformAdmin = {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
};

export type Person = {
  id: string;
  first_name: string;
  last_name: string;
  document_type: string | null;
  document_number: string | null;
  birth_date: string | null;
  gender: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  age: number | null;
};

export type RelatedPerson = {
  relation: string;
  person: Person;
};

export type AthleteProfile = {
  person_id: string;
  blood_type: string | null;
  insurance: string | null;
  allergies: string | null;
  medical_notes: string | null;
  dominant_side: string | null;
  updated_at: string | null;
};

export type Metric = {
  id: string;
  name: string;
  unit: string;
  discipline_id: string | null;
  is_active: boolean;
};

export type Measurement = {
  id: string;
  metric_id: string;
  metric_name: string;
  unit: string;
  value: string;
  measured_at: string;
  recorded_by_user_id: string | null;
  created_at: string;
};
