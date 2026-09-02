# Zahlungs-Timeout-Wiederherstellung, Zahlungs-Idempotenz und Schutz vor doppelten Zahlungen

Dies ist der deutschsprachige Discovery-Adapter für **Doability Intelligence (DI)** und die anbieterneutrale Demo zur Wiederherstellung einer mehrdeutigen Zahlung.

Eine Zahlungsplattform kann den finanziellen Effekt festschreiben, bevor die Antwort den Client erreicht. Geht die Bestätigung verloren, lautet der lokale Zustand `UNKNOWN`. Das bedeutet **nicht** `NOT_COMMITTED`.

Sicherer Ablauf:

```text
eine logische Operation
→ Bestätigung verloren
→ autoritativer Lookup
→ bestehender Effekt gefunden
→ ACCEPT_EXISTING_EFFECT
→ 1 Effekt, 0 Duplikate
```

Ein blinder Retry ohne Klärung des ersten Ergebnisses lässt `DUPLICATE_EFFECT_RISK` offen.

## Such- und Problembegriffe

- **Zahlungs-Timeout Wiederherstellung** — den autoritativen Transaktionszustand vor einer neuen Finanzaktion klären;
- **Zahlungs-Idempotenz** — eine logische Operation über Retries an eine Effekt-Identität binden;
- **doppelte Zahlung verhindern** — keine blinde Wiederholung bei unbekanntem Commit-Ergebnis;
- **KI-Agent-Zahlungen absichern** — Belege verlangen, bevor ein autonomer Agent erneut bezahlt.

## Entscheidungs- und Übergangsstack

```text
DIF → menschliche Absicht klären
DI  → Machbarkeit, Erlaubnis, Grenzen, Risiken und Unbekannte klären
DRP → Entscheidung und Begründung bewahren
TIP → Übergang begründen und beobachtetes Ergebnis prüfen
```

Die Projekte bleiben unabhängig. Die Demo ist ein externer Validierungsfall und keine Behauptung, dass ein Zahlungsanbieter DI einsetzt oder empfiehlt.

## Belege

Das deterministische Referenzergebnis ist `PASS`: ein festgeschriebener Effekt, null doppelte Effekte und `6 / 6` unsichere Mutationen abgelehnt.

- [Live-Demo auf Englisch](https://di-ambiguous-payment-recovery.lovable.app)
- [Kanonisches Repository](https://github.com/safal207/DI)
- [Evidence-Pack](https://github.com/safal207/DI/tree/main/evidence/ambiguous-payment-sandbox)
- [Fallstudie](https://github.com/safal207/DI/blob/main/docs/case-study-ambiguous-payment-recovery.md)
