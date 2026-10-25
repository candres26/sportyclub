import type { Person } from "@/lib/types";

export const DOCUMENT_TYPES = [
  { value: "RC", label: "Registro civil" },
  { value: "TI", label: "Tarjeta de identidad" },
  { value: "CC", label: "Cedula de ciudadania" },
  { value: "CE", label: "Cedula de extranjeria" },
  { value: "PA", label: "Pasaporte" },
];

export const RELATIONS = ["padre", "madre", "tutor", "abuelo(a)", "tio(a)", "hermano(a)", "otro"];

export function fullName(person: Pick<Person, "first_name" | "last_name">): string {
  return `${person.first_name} ${person.last_name}`;
}

/** "2026-03-10" -> "10/03/2026" sin conversion de zona horaria. */
export function formatDate(value: string | null): string {
  if (!value) return "-";
  const [year, month, day] = value.slice(0, 10).split("-");
  return `${day}/${month}/${year}`;
}

/** Quita las claves vacias para no enviar "" a la API. */
export function compact<T extends Record<string, string>>(values: T): Partial<T> {
  return Object.fromEntries(
    Object.entries(values).filter(([, value]) => value.trim() !== ""),
  ) as Partial<T>;
}
