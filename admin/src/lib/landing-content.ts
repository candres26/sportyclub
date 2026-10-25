/**
 * Contenido editable de la landing (dominio raiz).
 *
 * Las secciones de precios y de clubes solo se muestran cuando tienen datos.
 * En desarrollo, mientras falte algo, la landing muestra un aviso indicando que
 * completar aqui; en produccion la seccion simplemente no aparece.
 */

/**
 * Numero de WhatsApp con codigo de pais, solo digitos. Ej.: "573001234567".
 * Vacio = no se muestra el boton de WhatsApp.
 */
export const WHATSAPP_NUMBER = "";

/** Mensaje con el que se abre el chat de WhatsApp. */
export const WHATSAPP_MESSAGE =
  "Hola, me interesa SportyClub para mi club. ¿Me pueden dar mas informacion?";

export type Plan = {
  name: string;
  /** Precio ya formateado, p. ej. "$80.000". */
  price: string;
  /** Periodo del cobro, p. ej. "/ mes". */
  period: string;
  description: string;
  features: string[];
  /** Resalta el plan recomendado. */
  highlighted?: boolean;
};

/**
 * Planes y precios. Vacio = no se muestra la seccion de precios.
 *
 * Ejemplo de un elemento:
 *   {
 *     name: "Club",
 *     price: "$80.000",
 *     period: "/ mes",
 *     description: "Para clubes de hasta 100 deportistas.",
 *     features: ["Deportistas y acudientes", "Ficha tecnica", "Soporte por WhatsApp"],
 *     highlighted: true,
 *   }
 */
export const PLANS: Plan[] = [];

export type TrustedClub = {
  name: string;
  /** Ruta del logo dentro de admin/public, p. ej. "/clubs/club-norte.png". */
  logo: string;
};

/**
 * Clubes que usan SportyClub (con su autorizacion para mostrar el logo).
 * Los logos van en admin/public/clubs/. Vacio = no se muestra el carrusel.
 */
export const TRUSTED_CLUBS: TrustedClub[] = [];
