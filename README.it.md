# Hermes

*Controlla il desktop in un modo diverso dal solito.*

[🇬🇧 English](README.md) · [🇮🇹 Italiano](README.it.md)

## Indice
- [Cos'è Hermes](#cosè-hermes)
- [Avviso sulla privacy](#avviso-sulla-privacy)
- [Avvio rapido](#avvio-rapido)
- [Come si usa](#come-si-usa)
- [Stati e gesti](#stati-e-gesti)
- [Impostazioni](#impostazioni)
- [Disinstallazione](#disinstallazione)
- [Compilare il codice sorgente](#compilare-il-codice-sorgente)
- [Licenza](#licenza)
- [Sviluppo e note dell'autore](#sviluppo-e-note-dellautore)
- [Contatti](#contatti)

## Cos'è Hermes

Ti è mai capitato di mangiare davanti al PC con le mani sporche e voler comunque cambiare scheda, alzare il volume o mettere in pausa un video, senza dover prima pulirti le mani per toccare mouse e tastiera? Oppure hai una scrivania piccola, e mentre studi o lavori mouse e tastiera finiscono in un angolo scomodo?

Hermes nasce per questi casi: usa la fotocamera per riconoscere i gesti della mano e ti permette di controllare il cursore e alcune funzioni del desktop a gesti, senza toccare nulla.

## Avviso sulla privacy

**Hermes non raccoglie né invia immagini della webcam a Internet.** Tutta l'elaborazione avviene in locale, sul tuo computer.

## Avvio rapido

Al momento Hermes è stato testato solo su **Windows 11**. Ti serve solo una webcam funzionante.

Non è previsto un installer:
1. Scarica lo `.zip`.
2. Estrai il contenuto in una cartella a tua scelta.
3. Avvia `Hermes.exe`.

Al primo avvio Hermes crea automaticamente il file di configurazione con i valori predefiniti.

## Come si usa

All'avvio si apre un terminale — **deve restare aperto**: se lo chiudi, l'app si chiude con esso — e dopo qualche istante la finestra di anteprima con lo streaming della fotocamera. Se Hermes non trova nessuna webcam, l'anteprima mostra un messaggio d'errore. Chiudere la finestra di anteprima non chiude Hermes: l'app continua a girare in background.

Fai clic sull'icona di Hermes nella tray di sistema per aprire il menu a tendina, con tre voci:
- **Preview** — mostra o nasconde la finestra di anteprima.
- **Settings** — apre il pannello delle impostazioni.
- **Quit** — chiude davvero l'applicazione.

> **Attenzione:** in caso di riconoscimenti errati che potrebbero causare problemi, il tasto **Esc** della tastiera è sempre in ascolto e chiude l'app anche quando è in background.

## Stati e gesti

Hermes funziona come una macchina a stati: in ogni momento ti trovi in uno stato preciso, e solo certi gesti — tenuti per un certo numero di secondi — ti fanno passare a quello successivo.

| Stato | Cosa fa | Come entrarci |
|---|---|---|
| **Idle** | Stato di riposo: Hermes osserva ma non interagisce con il desktop. | Stato di partenza. |
| **Active** | Riconosce i gesti per alzare/abbassare il volume e play/pausa (vedi tabella sotto). | Dall'Idle, mano aperta tenuta per 1 s. |
| **Cursor** | Il cursore del mouse segue la mano; il pinch (pollice e indice) fa clic e trascina. | Dall'Active, solo indice teso per 0,5 s. |
| **Scroll** | Scorri la pagina muovendo la mano sopra o sotto una riga di riferimento. | Dal Cursor, indice e medio tesi e uniti, per 0,3 s. |
| **Unknown** | Stato che, salvo bug, non dovrebbe mai comparire. | — |

Per tornare indietro:
- Da **Cursor** ad **Active**: mano aperta, 0,5 s.
- Da **Scroll** a **Cursor**: apri le dita (indice e medio separati) oppure solo indice teso, 0,2 s.
- Da **Scroll** ad **Active**: mano aperta, 0,5 s.
- Da **Active** a **Idle**: pugno chiuso (1 s).
- Da **Cursor**, **Active** o **Scroll** a **Idle**: mano non più rilevata per 3 s.

Nello stato **Active**, alcuni gesti attivano direttamente un'azione (non un cambio di stato):

| Gesto | Azione | Note |
|---|---|---|
| Indice e medio tesi e separati (*victory*) | Alza il volume | Tenuto 0,5 s, poi si ripete ogni 0,3 s finché il gesto resta |
| Indice, medio e anulare tesi (*three*) | Abbassa il volume | Tenuto 0,5 s, poi si ripete ogni 0,3 s |
| Indice e mignolo tesi (*rock*) | Play/pausa multimediale | Tenuto 0,5 s, azione singola senza ripetizione |

Nello stato **Cursor**, il puntatore segue la posizione media tra le nocche di medio, anulare e mignolo. Il pinch (avvicinare pollice e indice) avvia un trascinamento; separando di nuovo le dita il trascinamento termina (release). Consiglio dell'autore: per un riconoscimento del pinch più preciso, mostra la mano alla camera con un'angolazione leggermente obliqua, non frontale.

Nello stato **Scroll**, l'anteprima mostra una riga gialla all'altezza delle punte di indice e medio: sposta la mano sotto quella riga per scorrere verso il basso, sopra per scorrere verso l'alto.

Al momento i tempi di attesa e i gesti collegati a stati e azioni non sono configurabili dall'interfaccia: per modificarli bisogna intervenire sul codice sorgente.

## Impostazioni

Ogni parametro ha un tooltip (passa il cursore sopra la voce per leggerlo). Se un tooltip manca o non è chiaro, segnalalo pure.

| Parametro | Descrizione |
|---|---|
| Camera | Quale webcam usare, contando da zero. |
| Camera faces you | Specchia l'immagine; disattivalo se la fotocamera non è rivolta verso di te. |
| Hand | Quale mano segue Hermes; l'altra viene ignorata. |
| Active zone start / end | La porzione dell'inquadratura che corrisponde allo schermo; una zona più ampia dà un controllo più preciso ma richiede movimenti più ampi della mano. |
| Pointer steadiness | Pixel di movimento minimo prima che il puntatore inizi a seguire la mano. |
| Pinch to click | Quanto devono avvicinarsi pollice e indice per generare un clic. |
| Pinch to release | Quanto devono allontanarsi per rilasciare il clic; deve essere maggiore della soglia precedente. |
| Pinch delay | Secondi di attesa prima che il clic venga registrato. |
| Fingers together | Quanto devono essere vicini indice e medio per attivare lo scroll. |
| Fingers apart | Quanto devono essere distanti per interrompere lo scroll. |
| Scroll speed | Click di scroll al secondo, alla massima inclinazione. |
| Scroll range | Quanto inclinare la mano per raggiungere la velocità massima. |
| Scroll deadzone | Margine di tolleranza prima che lo scroll abbia effettivamente inizio. |
| Open preview at start | Mostra la finestra di anteprima all'avvio. |
| Draw the hand skeleton | Disegna lo scheletro della mano nell'anteprima. |
| Draw the debug lines | Mostra le informazioni di debug nell'anteprima. |
| Draw the active zone | Disegna la zona attiva nell'anteprima. |
| Detection confidence | Quanto Hermes deve essere sicuro prima di segnalare una mano rilevata. |
| Presence confidence | Quanto deve essere sicuro che la mano sia ancora presente. |
| Tracking confidence | Quanto deve essere sicuro per continuare a seguire la stessa mano. |
| Pointer smoothing | Valori più bassi rendono il puntatore più stabile da fermo, a costo di più ritardo. |
| Pointer responsiveness | Valori più alti seguono meglio i movimenti rapidi. |
| Recognition smoothing | Come sopra, ma per il riconoscimento dei gesti. |
| Recognition responsiveness | Beta scala con il segnale; qui l'unità è il metro. |

Per tornare ai valori predefiniti, al momento serve cancellare manualmente il file di configurazione:
1. Premi `Win + R`, digita (o copia) il seguente percorso e premi Invio:
   ```
   %appdata%
   ```
2. Entra nella cartella `Hermes` ed elimina `config.json`.
3. Riavvia Hermes: il file verrà ricreato con i valori di default.

## Disinstallazione

1. Elimina la cartella in cui hai estratto Hermes.
2. Se vuoi rimuovere anche i dati di configurazione, elimina anche la cartella `Hermes` dentro `%appdata%`.

## Compilare il codice sorgente

Clona la repository:
```
git clone https://github.com/Cheng98989/Hermes.git
cd Hermes
```

Crea/attiva l'ambiente Python (sviluppato con la 3.11.8) e installa le dipendenze necessarie, incluso `pyinstaller`. Poi compila:
```
pyinstaller Hermes.spec
```

Il risultato — tutto il necessario per l'esecuzione — sarà nella cartella `dist`.

## Licenza

Distribuito con licenza **GPL-3.0-or-later**. Testo completo nel file [LICENCE.txt](LICENCE.txt).

## Sviluppo e note dell'autore

Il progetto nasce per imparare a usare Python; è anche un progetto scolastico, quindi il proseguimento dello sviluppo dipende (anche) dalla mia disciplina — nessuna garanzia di manutenzione continua nel tempo.

Durante lo sviluppo ho usato l'IA come supporto, soprattutto a scopo didattico: niente vibecoding, l'IA è stata un confronto per discutere funzioni e risolvere problemi, non chi ha scritto il progetto al posto mio. L'IA è stata usata anche per la documentazione nel codice sorgente e nel README; il contenuto finale è comunque rivisto da me.

Realizzato con:
- Python 3.11.8
- PySide6
- MediaPipe
- OpenCV
- Pynput

## Contatti

Per segnalazioni, domande o proposte, apri una issue su GitHub.
