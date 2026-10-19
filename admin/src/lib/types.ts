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
