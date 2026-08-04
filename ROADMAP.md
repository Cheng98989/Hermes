# Hermes v2 — Scheda di sviluppo

**Cos'è:** un'app che riconosce i gesti della mano dalla webcam e li usa per
impartire comandi al desktop (spostare finestre, chiudere, play/pausa, volume).

**Non è** un emulatore di mouse: il cursore è solo *uno* dei comandi, e il più
difficile.

**Target:** Windows 11 prima, Linux/X11 dopo.
(Wayland blocca l'input sintetico per motivi di sicurezza — lì non funzionerà
senza permessi speciali. Da dichiarare nel README.)

**Scadenza scolastica:** 27 agosto 2026 — repo GitHub + almeno 3 screenshot.

---

## ⚠️ Nota tecnica: MediaPipe 1.0

Versioni installate: Python 3.11.8, OpenCV 5.0.0, **MediaPipe 1.0.0**, pynput 1.8.2.

**MediaPipe 1.0 ha rimosso `mp.solutions`.** Quasi tutti i tutorial online usano
`mp.solutions.hands.Hands(...)`: con questa versione danno `AttributeError`.

Si usa l'API Tasks:

- `mediapipe.tasks.python.vision.HandLandmarker`
- il risultato ha `hand_landmarks` (non `multi_hand_landmarks`) e `handedness`
- serve un file modello esterno: `hand_landmarker.task` (~7,5 MB), non incluso
  nel pacchetto
- `running_mode=VIDEO` → `detect_for_video(img, timestamp_ms)`, con timestamp
  **strettamente crescente**, altrimenti solleva eccezione

Regola pratica: se un esempio comincia con `mp.solutions.`, è vecchio.

---

## Regole di sviluppo

1. **Prima far funzionare, poi estrarre i moduli.** Gli esperimenti vivono in
   `esperimenti/`, non fanno parte dell'app. Quando uno script funziona ed è
   chiaro, se ne estrae un modulo.
2. **Separare puro da I/O.** Le funzioni che trasformano dati in dati
   (`landmark -> gesto`, `gesto -> evento`) non devono toccare webcam né mouse:
   così si testano in mezzo secondo senza agitare la mano davanti allo schermo.
3. **Dipendenze in una direzione sola.** `main` conosce tutti, i moduli foglia
   non si conoscono tra loro. Nessun import circolare.
4. **Un milestone alla volta**, e ogni milestone deve essere *visibile*: se non
   puoi guardarlo funzionare, non è finito.

---

## Milestone

### M0 — Ambiente ✅
venv + `mediapipe`, `opencv-python`, `pynput`.

### M1 — Vedere la mano
Script usa-e-getta in `esperimenti/`.
- apre la webcam, mostra il frame ribaltato (effetto specchio)
- MediaPipe individua la mano, i 21 landmark vengono disegnati
- **FPS scritti a schermo** — servono da subito, sono il budget di tutto il resto

*Obiettivo vero:* capire che forma hanno i dati di MediaPipe. Il resto viene dopo.

Da misurare: FPS a 480p / 720p / 1080p, con e senza MediaPipe attivo.

#### Misure a 640x480, senza MediaPipe

```
FPS: 29.8 | lettura 19.2 ms | elab 0.1 ms | display 14.3 ms
FPS: 30.5 | lettura 20.2 ms | elab 0.1 ms | display 12.6 ms
FPS: 30.1 | lettura 24.2 ms | elab 0.1 ms | display  8.9 ms
```

Verifica: `19.2 + 0.1 + 14.3 = 33.6 ms` e `1000 / 29.8 = 33.6 ms`. Tutto il
tempo del giro e' spiegato.

**Conclusioni:**

- **La webcam e' il tetto.** 30 fps stabili: e' la camera a dettare il ritmo,
  non il codice.
- **`cap.read()` non lavora, aspetta.** Nella terza riga il display cala di
  4 ms e la lettura cresce della stessa quantita': la lettura assorbe il tempo
  che avanza per arrivare al frame successivo.
- **Lavoro vero ~13 ms su 33 disponibili → ~20 ms liberi per frame.**
  MediaPipe (5-15 ms) ci entra senza far calare gli FPS.
- **La preview costa ~13 ms**, il 40% del lavoro vero. E' uno strumento di
  debug, non l'applicazione: quando servira' respiro, si toglie e si recupera
  tutto quel tempo.

### M2 — Prima struttura
Estrarre da M1 i moduli `camera.py` e `mano.py`. Un `main.py` che li cuce.
Stesso comportamento di M1, ma diviso. Nessuna funzionalità nuova.

### M3 — Primo riconoscimento
`gesti.py`, funzione **pura**: 21 landmark in ingresso, nome del gesto in uscita.
Partire dal più semplice: **quante dita sono alzate**.
- confronto tra la punta del dito e la nocca sottostante
- il pollice è un caso a parte (si muove lateralmente, non verticalmente)

Primo test in `tests/`: nessuna webcam coinvolta.

### M4 — Macchina a stati
`stato.py`, funzione **pura**. Stati `IDLE` / `ATTIVO`.
- dizionario `TRANSIZIONI` con chiavi `(stato, gesto)`
- **dwell time**: la posa vale solo se tenuta ~1 secondo → uccide i falsi positivi
- feedback visivo nella preview (bordo rosso = IDLE, verde = ATTIVO)

Senza il feedback non capisci mai perché non risponde. Non è un extra.

### M5 — Prima azione reale ⚠️
`azioni.py` con `pynput`. Cursore in mappatura assoluta:
`landmark.x * larghezza_schermo`.

> **VIA DI FUGA OBBLIGATORIA, PRIMA DI ESEGUIRLO.**
> Quando il programma muove il cursore, potresti non riuscire a rimettere il
> fuoco sulla finestra per fermarlo. Serve un modo per ucciderlo che non passi
> dal mouse: un listener globale su ESC, o un tempo massimo di esecuzione.
> Va scritto *prima* del codice che muove il cursore, non dopo.

Problemi noti che emergeranno qui:
- i bordi dell'inquadratura sono scomodi → mappare solo un rettangolo centrale
- il cursore trema → serve smoothing (media sugli ultimi N frame)

### M6 — Eventi discreti
Il loop gira a 30 fps: un gesto tenuto un secondo = 30 click.
Trasformare il flusso continuo di gesti in **eventi** (inizio / fine / ripetizione).
Poi il click.

### M7 — Comandi desktop
Tasti multimediali (volume, play/pausa) e scorciatoie. Qui sta il valore d'uso
reale del progetto: sono azioni discrete, molto più affidabili del cursore.

### M8 — Rifiniture e consegna
Configurazione esterna, README, i 3 screenshot per il prof, repo GitHub.

---

## Punti aperti (da decidere quando ci arriviamo)

- **Come si esce da ATTIVO?** Gesto esplicito o timeout a mano fuori campo?
- **Il cursore si muove sempre in ATTIVO**, o serve un ulteriore "modo cursore"?
- **Quale posa attiva?** Criterio: dev'essere scomoda da fare per sbaglio
  mentre si studia. Con il dwell time il vincolo si allenta parecchio.

---

## Nozioni della checklist del prof toccate dal progetto

| Argomento | Dove |
|---|---|
| dizionari | M4 transizioni, M5 mappa azioni, config |
| tuple | chiavi composte, coordinate |
| set | insieme delle dita alzate |
| liste | buffer per lo smoothing |
| funzioni e ambiti | ovunque — è la struttura del progetto |
| controllo di flusso | il loop principale |
| math | distanze e angoli tra landmark |
| strutture dati (coda) | buffer a finestra scorrevole per lo smoothing |
| algoritmi | smoothing, soglie, riconoscimento |
