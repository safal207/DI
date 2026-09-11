# Recuperación de pagos tras un timeout, idempotencia y prevención de pagos duplicados

Esta es la adaptación de descubrimiento en español de **Doability Intelligence (DI)** y de la demo neutral de recuperación de pagos ambiguos.

Una plataforma de pagos puede confirmar el efecto financiero antes de que la respuesta llegue al cliente. Si se pierde la confirmación, el estado local es `UNKNOWN`. Eso **no significa** `NOT_COMMITTED`.

Secuencia segura:

```text
una operación lógica
→ confirmación perdida
→ consulta autoritativa
→ efecto existente recuperado
→ ACCEPT_EXISTING_EFFECT
→ 1 efecto, 0 duplicados
```

Un reintento a ciegas sin resolver el primer resultado mantiene abierto `DUPLICATE_EFFECT_RISK`.

## Problemas que ayuda a describir

- **recuperación de pagos tras un timeout** — conocer el estado autoritativo antes de otra acción financiera;
- **idempotencia de pagos** — mantener una operación lógica ligada a una identidad de efecto;
- **evitar pagos duplicados** — bloquear reintentos mientras el commit anterior sea desconocido;
- **seguridad de pagos de agentes de IA** — exigir evidencia antes de que un agente autónomo vuelva a pagar.

## Stack de decisión y transición

```text
DIF → aclarar la intención humana
DI  → aclarar viabilidad, permiso, límites, riesgos e incógnitas
DRP → conservar la decisión y su razonamiento
TIP → razonar la transición y revisar el resultado observado
```

Los proyectos siguen siendo independientes. La demo es un caso externo de validación, no una afirmación de que un proveedor utilice o respalde DI.

## Evidencia

El resultado determinista de referencia es `PASS`: un efecto confirmado, cero efectos duplicados y `6 / 6` mutaciones inseguras rechazadas.

- [Demo en vivo en inglés](https://di-ambiguous-payment-recovery.lovable.app)
- [Repositorio canónico](https://github.com/safal207/DI)
- [Paquete de evidencia](https://github.com/safal207/DI/tree/main/evidence/ambiguous-payment-sandbox)
- [Caso de estudio](https://github.com/safal207/DI/blob/main/docs/case-study-ambiguous-payment-recovery.md)
