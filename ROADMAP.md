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

1. **Prima far funzionare, poi estrarre i moduli.** Si parte da uno script
   usa-e-getta che gira; quando funziona ed è chiaro, se ne estrae un modulo.
   Non si progetta l'astrazione di qualcosa che non si è ancora capito.
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

### M1 — Vedere la mano ✅
Script unico, usa-e-getta.
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

### M2 — Prima struttura ✅
Estratti da M1 quattro moduli, `main.py` che li cuce. Stesso comportamento,
nessuna funzionalità nuova.

- `camera.py` — apertura, verifica, risoluzione **vera** (non quella richiesta),
  flip a specchio, fallimenti di lettura consecutivi, chiusura
- `hand.py` — involucro su MediaPipe; espone `CONNECTIONS` come coppie di
  interi, così nessun altro modulo deve importare MediaPipe
- `overlay.py` — solo disegno
- `fps.py` — contatore a finestra scorrevole (`deque`)

Deciso qui: **lo stato costoso sta nell'oggetto, i dati di passaggio sono
parametri.** `Hand` teneva il frame (33 ms di vita) nel costruttore e il
landmarker (ore di vita) come variabile globale: era rovesciato.

### M3 — Primo riconoscimento ✅
`gestures.py`, modulo **puro**: importa solo `math`.

- `fingers_up()` → insieme delle dita distese. Un dito è disteso quando la
  punta è più lontana dal polso della nocca media
- il **pollice** ha una regola sua: stesso criterio ma misurato dalla nocca
  del mignolo. Dal polso non funziona, perché il polso è quasi sul perno
  attorno a cui il pollice ruota — e dal centro di una rotazione la distanza
  non cambia mai
- `GESTURES`: `frozenset` di dita → nome del gesto. Aggiungere un gesto è
  una riga
- nessuna soglia da tarare: ogni test confronta **due distanze**, quindi la
  dimensione della mano e la distanza dalla camera si semplificano

Scartato: normalizzare per la lunghezza del palmo. `palm_size` è una
proiezione 2D e collassa quando la mano si inclina verso la camera — misurati
rapporti fino a 34, fisicamente impossibili.

Test in `tests/test_gestures.py`, nessuna webcam coinvolta.

### M4 — Macchina a stati ✅
`state.py`, nessun import: né `cv2` né `time`.

- `GestureHold` — trasforma il flusso rumoroso di gesti in "quale gesto, e da
  quanto". Riceve l'istante da fuori invece di leggere l'orologio
- `TRANSITIONS` — dizionario `(stato, gesto) → (nuovo stato, secondi richiesti)`.
  Ogni regola porta con sé il proprio dwell time
- `StateMachine` — cerca la regola, controlla il tempo, cambia stato
- bordo colorato in `overlay.py`: rosso `IDLE`, verde `ACTIVE`

Il **timeout di sicurezza** è una sola riga della tabella:
`(ACTIVE, "none") → (IDLE, 3.0)`. Funziona perché "nessuna mano" è stata
trattata fin da subito come un gesto normale.

Deciso qui: **l'orologio è I/O.** `main.py` legge `perf_counter()` una volta
per giro e passa lo stesso istante a tutti. Tutti gli altri moduli restano
testabili con tempi finti — verificare "tenuto per 1,1 secondi" non richiede
di aspettare 1,1 secondi.

---

> ⚠️ **Ordine invertito rispetto alla versione precedente di questa scheda.**
> Il cursore era M5 ed è finito in fondo. Due motivi: è il pezzo tecnicamente
> più difficile, ed è l'unico che può rendere il computer inutilizzabile se
> qualcosa va storto. I comandi discreti sono più utili nell'uso reale, sono
> una riga ciascuno, e permettono di costruire lo strato delle azioni in
> sicurezza.

### M5 — Prima azione reale ⚠️
`actions.py` con `pynput`. **Un comando solo**: volume su.

> **VIA DI FUGA, PRIMA DI SCRIVERE QUALSIASI COSA CHE TOCCHI IL SISTEMA.**
> Serve un modo garantito di fermare Hermes che non dipenda da Hermes: un
> listener globale su ESC, o un tempo massimo di esecuzione. Con i tasti
> multimediali il rischio è basso, ma l'abitudine va presa adesso, non
> quando arriverà il cursore.

Il problema da risolvere qui: il loop gira a 30 fps, quindi un gesto tenuto
un secondo sono **trenta comandi**. Serve trasformare il flusso continuo in
eventi discreti — un comando all'ingresso nel gesto, non a ogni frame.

Dwell corto per i comandi (~0,3 s), diverso da quello degli stati (1 s).

### M6 — Il set di comandi
Volume giù, play/pausa, e la tabella `gesto → azione` in `ACTIVE`.
Qui sta il valore d'uso reale del progetto.

### M7 — Il cursore
Il pezzo difficile, per ultimo, quando tutto il resto è solido.
Mappatura assoluta: `landmark.x * larghezza_schermo`.

Problemi noti che emergeranno:
- i bordi dell'inquadratura sono scomodi → mappare solo un rettangolo centrale
- il cursore trema → smoothing su finestra scorrevole (la stessa `deque` di
  `fps.py`, ma su posizioni invece che durate)

### M8 — Rifiniture e consegna
Configurazione esterna, README aggiornato, i 3 screenshot per il prof, repo
GitHub.

---

## Decisioni prese

- **Attivazione:** palmo aperto tenuto 1 s. **Uscita:** pugno tenuto 1 s,
  più il timeout automatico a 3 s senza mano.
- **Dwell:** lungo (1 s) per i cambi di stato, corto (~0,3 s) per i comandi.
  Entrare deve essere deliberato; una volta dentro, hai già dichiarato che
  stai parlando a Hermes.
- **Sui due modi di sbagliare:** dimenticare di spegnere è pericoloso e non
  te ne accorgi; spegnersi troppo presto è solo fastidioso. Il sistema deve
  fallire dalla parte innocua → il timeout non è un extra.

## Punti ancora aperti

- **La zona.** Ascoltare solo se la mano è nella parte alta dell'inquadratura:
  sotto c'è la scrivania dove si scrive. Alzare la mano è già di per sé un
  gesto volontario.
- **Il feedback sonoro.** Il bordo colorato serve a chi sviluppa; chi studia
  guarda il libro, non la preview. Un bip all'ingresso e all'uscita da ACTIVE
  si sente senza alzare gli occhi.
- **Il cursore si muove sempre in ACTIVE**, o serve un ulteriore stato
  `CURSOR`?

---

## Nozioni della checklist del prof toccate dal progetto

| Argomento | Dove | |
|---|---|---|
| dizionari | `GESTURES`, `TRANSITIONS`, `STATE_COLORS`, `FINGERS` | ✅ |
| set / frozenset | insieme delle dita alzate, chiavi di `GESTURES` | ✅ |
| tuple | chiavi `(stato, gesto)`, valori `(tip, nocca)` | ✅ |
| funzioni e ambiti | la struttura stessa del progetto | ✅ |
| controllo di flusso | il loop principale | ✅ |
| math | `math.hypot` per le distanze | ✅ |
| strutture dati (coda) | `deque(maxlen=N)` in `fps.py` | ✅ |
| liste | landmark, `CONNECTIONS`, buffer | ✅ |
| algoritmi | media su finestra scorrevole, soglie, riconoscimento | ✅ |
| file I/O | non ancora toccato — arriverà con la configurazione (M8) | ⬜ |
| Date | `time` misura durate; `datetime` non serve finora | ⬜ |
