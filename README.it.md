<p align="center">
  <img src="assets/icon-app.svg" alt="Iris" width="128">
</p>

# Iris

*Controlla il desktop in un modo diverso dal solito.*

[🇬🇧 English](README.md) · [🇮🇹 Italiano](README.it.md)

## Indice
- [Cos'è Iris](#cosè-iris)
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

## Cos'è Iris

Ti è mai capitato di mangiare davanti al PC con le mani sporche e voler comunque cambiare scheda, alzare il volume o mettere in pausa un video, senza dover prima pulirti le mani per toccare mouse e tastiera? Oppure hai una scrivania piccola, e mentre studi o lavori mouse e tastiera finiscono in un angolo scomodo?

Iris nasce per questi casi: usa la fotocamera per riconoscere i gesti della mano e ti permette di controllare il cursore e alcune funzioni del desktop a gesti, senza toccare nulla.

## Avviso sulla privacy

**Iris non raccoglie né invia immagini della webcam a Internet.** Tutta l'elaborazione avviene in locale, sul tuo computer.

## Avvio rapido

Al momento Iris è stato testato solo su **Windows 11**. Ti serve solo una webcam funzionante.

Non è previsto un installer:
1. Scarica lo `.zip` dall'ultima [release](https://github.com/Cheng98989/Iris/releases/latest).
2. Estrai il contenuto in una cartella a tua scelta.
3. Avvia `Iris.exe`.

> **Nota:** `Iris.exe` non è firmato digitalmente, quindi al primo avvio Windows può mostrare l'avviso "Windows ha protetto il PC". Per procedere: **Ulteriori informazioni** → **Esegui comunque**. Per lo stesso motivo qualche antivirus può mettere il file in quarantena.

Al primo avvio Iris crea automaticamente, dentro `%appdata%\Iris`, la cartella con i dati dell'app (vedi [Disinstallazione](#disinstallazione)).

## Come si usa

All'avvio, dopo qualche istante, appare la finestra di anteprima con lo streaming della fotocamera, se [Open preview at start](#par-show-preview) è attivo. Se Iris non trova nessuna webcam, l'anteprima mostra un messaggio d'errore. Chiudere la finestra di anteprima non chiude Iris: l'app continua a girare in background.

Fai clic sull'icona di Iris nella tray di sistema per aprire il menu a tendina, con quattro voci:
- **Preview** — mostra o nasconde la finestra di anteprima.
- **Settings** — apre il pannello delle [impostazioni](#impostazioni).
- **Restart** — riavvia l'applicazione.
- **Quit** — chiude davvero l'applicazione.

![Icona di Iris nella tray di sistema con il menu a tendina](doc/tray_icon.gif)
*L'icona di Iris nella tray di sistema, con il relativo menu a tendina.*

Con **F12** metti in pausa l'app: lo stato resta fisso su **[Idle](#stato-idle)**; landmark e gesti continuano comunque a essere riconosciuti, ma non eseguiti, proprio perché lo stato è Idle.

> **Attenzione:** in caso di riconoscimenti errati che potrebbero causare problemi, il tasto **Esc** della tastiera è sempre in ascolto e chiude l'app anche quando è in background.

## Stati e gesti

Iris funziona come una macchina a stati: in ogni momento ti trovi in uno stato preciso, e solo certi gesti — tenuti per un certo numero di secondi — ti fanno passare a quello successivo.

| Stato | Cosa fa | Colore del bordo | Suono |
| --- | --- | --- | --- |
| <a id="stato-idle"></a>**Idle** | Stato di riposo e stato di partenza: Iris osserva ma non interagisce con il desktop. | Rosso | `default_D#4vH.wav` |
| <a id="stato-active"></a>**Active** | Riconosce i [gesti](#active) per alzare/abbassare il volume e per il play/pausa. | Verde | `default_F#4vH.wav` |
| <a id="stato-cursor"></a>**Cursor** | Il cursore del mouse segue la mano; puoi fare clic sinistro e destro, anche con trascinamento, su più monitor (vedi i [gesti](#cursor)). | Blu | `default_A4vH.wav` |
| <a id="stato-scroll"></a>**Scroll** | Imitazione della rotellina del mouse (vedi i [gesti](#scroll)). | Giallo | `default_C5vH.wav` |
| <a id="stato-unknown"></a>**Unknown** | Stato che, salvo bug, non dovrebbe mai comparire. | — | — |

Colori e suoni si cambiano nelle [impostazioni](#impostazioni), rispettivamente nella scheda [Preview](#preview) e nella scheda [Audio](#audio).

### Transizioni

Ogni riga è un passaggio possibile: il gesto va tenuto per il tempo indicato. Le combinazioni che non compaiono non hanno un passaggio diretto.

| Da | A | Gesto | Tempo |
| --- | --- | --- | --- |
| [Idle](#stato-idle) | [Active](#stato-active) | [Open palm](#gesto-open-palm) | 1 s |
| [Active](#stato-active) | [Cursor](#stato-cursor) | [Point](#gesto-point) | 0,5 s |
| [Active](#stato-active) | [Idle](#stato-idle) | [Fist](#gesto-fist) | 1 s |
| [Cursor](#stato-cursor) | [Scroll](#stato-scroll) | [Victory closed](#gesto-victory-closed) | 0,3 s |
| [Cursor](#stato-cursor) | [Active](#stato-active) | [Open palm](#gesto-open-palm) | 0,5 s |
| [Scroll](#stato-scroll) | [Cursor](#stato-cursor) | [Point](#gesto-point) oppure [Victory](#gesto-victory) | 0,2 s |
| [Scroll](#stato-scroll) | [Active](#stato-active) | [Open palm](#gesto-open-palm) | 0,5 s |
| [Active](#stato-active), [Cursor](#stato-cursor) o [Scroll](#stato-scroll) | [Idle](#stato-idle) | mano non più rilevata | 2 s |

### Gesti per stato

#### Active

Gesti disponibili nello stato **[Active](#stato-active)**:

| Gesto | Azione | Note |
| --- | --- | --- |
| [Victory](#gesto-victory) | Alza il volume | Tenuto 0,5 s, poi si ripete ogni 0,3 s finché il gesto resta |
| [Victory closed](#gesto-victory-closed) | Abbassa il volume | Tenuto 0,5 s, poi si ripete ogni 0,3 s finché il gesto resta |
| [Three](#gesto-three) | Play/pausa multimediale | Tenuto 0,5 s, azione singola senza ripetizione |

![Controllo del volume e del play/pausa multimediale nello stato Active](doc/media_control.gif)
*Controllo multimediale nello stato Active: volume e play/pausa.*

#### Cursor

Gesti disponibili nello stato **[Cursor](#stato-cursor)**:

| Gesto | Azione | Note |
| --- | --- | --- |
| [Pinch indice](#gesto-pinch-indice) | Clic / Trascinamento / Rilascio, tasto sinistro | — |
| [Pinch mignolo](#gesto-pinch-mignolo) | Clic / Rilascio, azione singola, tasto destro | — |
| — | Movimento cursore | Fintanto che sei in [Cursor](#stato-cursor), il cursore segue la posizione media tra la nocca del medio e quella dell'anulare, per un movimento più stabile |

#### Scroll

Gesti disponibili nello stato **[Scroll](#stato-scroll)**:

| Gesto | Azione | Note |
| --- | --- | --- |
| [Victory closed](#gesto-victory-closed) | Scroll | Nella preview compare una riga, e lo scroll dipende dalla posizione della punta delle dita rispetto ad essa. Quando si entra in [Scroll](#stato-scroll) l'azione viene già riconosciuta. Per cambiare il riferimento della riga puoi rilasciare per un breve istante [Victory closed](#gesto-victory-closed) e spostare le dita: la riga si riposizionerà all'incirca tra la prima e la seconda falange |

![Movimento del cursore, clic e scroll negli stati Cursor e Scroll](doc/cursor_control.gif)
*Movimento del cursore, clic e scroll negli stati Cursor e Scroll.*

Al momento i tempi di attesa e i gesti collegati a stati e azioni non sono configurabili dall'interfaccia: per modificarli bisogna intervenire sul codice sorgente.

### Tabella dei gesti

Come si esegue ogni gesto. Il nome interno è quello usato nel codice sorgente e nella riga *Show the gesture* dell'anteprima; le soglie rimandano alla voce corrispondente nelle [impostazioni](#impostazioni).

| Gesto | Nome interno | Come si esegue |
| --- | --- | --- |
| <a id="gesto-open-palm"></a>**Open palm** | `open_palm` | Indice, medio, anulare e mignolo alzati; la distanza tra pollice e mignolo deve superare la soglia [Pinky pinch release](#par-pinky-pinch-open). |
| <a id="gesto-fist"></a>**Fist** | `fist` | Indice, medio, anulare e mignolo chiusi a pugno. |
| <a id="gesto-point"></a>**Point** | `point` | Solo indice alzato. |
| <a id="gesto-victory"></a>**Victory** | `victory` | Indice e medio alzati, con distanza tra le seconde falangi maggiore della soglia [Fingers apart](#par-fingers-apart). |
| <a id="gesto-victory-closed"></a>**Victory closed** | `victory_closed` | Indice e medio alzati, con distanza tra le seconde falangi minore della soglia [Fingers together](#par-fingers-joined). |
| <a id="gesto-three"></a>**Three** | `three` | Indice, medio e anulare alzati. |
| <a id="gesto-pinch-indice"></a>**Pinch indice** | — | Con medio, anulare e mignolo alzati oppure tutti e tre abbassati, avvicina la punta dell'indice a quella del pollice fino a una distanza minore di [Pinch to click](#par-pinch-close); il rilascio scatta quando la distanza supera [Pinch to release](#par-pinch-open). Non è una posa a sé: conta solo la distanza tra le due punte. |
| <a id="gesto-pinch-mignolo"></a>**Pinch mignolo** | `pinky_pinch` | Mano quasi a [Open palm](#gesto-open-palm), ma con la distanza tra pollice e mignolo già sotto la soglia [Right click ready](#par-pinky-ready-close) (questo mantiene lo stato [Cursor](#stato-cursor)). Avvicinando ancora la punta del pollice a quella del mignolo, entro [Pinky pinch to right click](#par-pinky-pinch-close) scatta il clic; il rilascio avviene oltre [Pinky pinch release](#par-pinky-pinch-open). |

![Come eseguire ciascun gesto riconosciuto da Iris](doc/gestures.gif)
*Come eseguire i gesti riconosciuti da Iris.*

## Impostazioni

Il pannello si apre dalla voce **Settings** del menu della tray ed è diviso in quattro schede: [Basics](#basics), [Preview](#preview), [Audio](#audio) e [Advanced](#advanced). La barra di ricerca in alto filtra per parole chiave presenti nel nome visualizzato, nel tooltip o nel nome interno usato nel codice; il numero accanto a ogni scheda dice quante voci sono rimaste visibili.

Ogni parametro ha un tooltip (passa il cursore sopra la voce per leggerlo). Se un tooltip manca o non è chiaro, segnalalo pure.

Accanto a un parametro che non è più al suo valore di default compare un pulsante per riportarlo indietro; **Restore Defaults**, in fondo alla finestra, li riporta indietro tutti insieme. Alcune impostazioni hanno effetto solo dopo un riavvio: al salvataggio verrà chiesta conferma, poi l'app verrà riavviata.

![Pannello delle impostazioni di Iris](doc/settings.gif)
*Il pannello delle impostazioni di Iris.*

### Basics

| Parametro | Descrizione |
| --- | --- |
| Camera | Quale webcam usare, contando da zero. |
| Camera faces you | Specchia l'immagine; disattivalo se la fotocamera non è rivolta verso di te. |
| Screen | Su quale monitor si estende la zona attiva: `Primary` per quello principale, `All` per l'intero desktop, oppure uno dei monitor rilevati, elencato con risoluzione e posizione. |
| Hand | Quale mano segue Iris; l'altra viene ignorata. |
| Active zone start / end | La porzione dell'inquadratura che corrisponde allo schermo; una zona più ampia dà un controllo più preciso ma richiede movimenti più ampi della mano. |
| Pointer steadiness | Pixel di movimento minimo prima che il puntatore inizi a seguire la mano. |
| <a id="par-pinch-close"></a>Pinch to click | Quanto devono avvicinarsi pollice e indice per generare un clic. |
| <a id="par-pinch-open"></a>Pinch to release | Quanto devono allontanarsi per rilasciare il clic; deve essere maggiore della soglia precedente. |
| Pinch delay | Secondi di attesa prima che il clic venga registrato. |
| <a id="par-pinky-pinch-close"></a>Pinky pinch to right click | Quanto devono avvicinarsi pollice e mignolo per generare un clic destro. |
| <a id="par-pinky-pinch-open"></a>Pinky pinch release | Quanto devono allontanarsi per rilasciare il clic destro; deve essere maggiore della soglia precedente. |
| <a id="par-pinky-ready-close"></a>Right click ready | Entro questa distanza tra pollice e mignolo, Iris resta nello stato [Cursor](#stato-cursor). |
| Right click ready release | Quanto deve allontanarsi il pollice per uscire da questo stato. |
| <a id="par-fingers-joined"></a>Fingers together | Quanto devono essere vicini indice e medio per attivare lo scroll. |
| <a id="par-fingers-apart"></a>Fingers apart | Quanto devono essere distanti per interrompere lo scroll. |
| Scroll speed | Clic di scroll al secondo, alla massima inclinazione. |
| Scroll range | Quanto inclinare la mano per raggiungere la velocità massima. |
| Scroll deadzone | Margine di tolleranza prima che lo scroll abbia effettivamente inizio. |

### Preview

| Parametro | Descrizione |
| --- | --- |
| <a id="par-show-preview"></a>Open preview at start | Mostra la finestra di anteprima all'avvio. |
| Draw the hand skeleton | Disegna lo scheletro della mano nell'anteprima. |
| Show the frame rate | Quanti fotogrammi al secondo riesce a seguire il riconoscitore. |
| Show the state | Lo stato corrente — [Idle](#stato-idle), [Active](#stato-active), [Cursor](#stato-cursor) o [Scroll](#stato-scroll) — nel colore del bordo. |
| Show the gesture | Il gesto che viene riconosciuto e da quanto tempo è tenuto. |
| Show the pinch distances | Distanza tra pollice e indice e tra pollice e mignolo; servono a tarare i clic. |
| Show the finger gap | Distanza tra indice e medio: sotto la soglia le due dita contano come unite e parte lo scroll. |
| Show the last command | L'ultimo tasto multimediale premuto. |
| Show the pointer target | Il pixel verso cui viene mandato il cursore, e la velocità di scroll. |
| Draw the active zone | Disegna la zona attiva nell'anteprima. |
| Idle / Active / Cursor / Scroll | Il colore del bordo dell'anteprima per ciascuno stato. |

### Audio

| Parametro | Descrizione |
| --- | --- |
| Play sounds | Suona a ogni cambio di stato. |
| Audio volume | Volume del suono riprodotto durante le transizioni di stato. |
| Idle / Active / Cursor / Scroll | Il file `.wav` associato a ciascuno stato: il pulsante ▶ lo riproduce, quello con la cartella ne sceglie un altro. |

### Advanced

| Parametro | Descrizione |
| --- | --- |
| Detection confidence | Quanto Iris deve essere sicuro prima di segnalare una mano rilevata. |
| Presence confidence | Quanto deve essere sicuro che la mano sia ancora presente. |
| Tracking confidence | Quanto deve essere sicuro per continuare a seguire la stessa mano. |
| Pointer smoothing | Valori più bassi rendono il puntatore più stabile da fermo, a costo di più ritardo. |
| Pointer responsiveness | Valori più alti seguono meglio i movimenti rapidi. |
| Recognition smoothing | Lo stesso, ma per il riconoscimento dei gesti. |
| Recognition responsiveness | Beta scala con il segnale; qui l'unità è il metro. |

In alternativa ai pulsanti di ripristino puoi cancellare il file di configurazione:
1. Premi `Win + R`, digita (o copia) il seguente percorso e premi Invio:
   ```
   %appdata%
   ```
2. Entra nella cartella `Iris` ed elimina `config.json`.
3. Riavvia Iris: il file verrà ricreato con i valori di default.

## Disinstallazione

1. Elimina la cartella in cui hai estratto Iris.
2. Se vuoi rimuovere anche i dati di configurazione, elimina anche la cartella `Iris` dentro `%appdata%`.

## Compilare il codice sorgente

Clona la repository:
```
git clone https://github.com/Cheng98989/Iris.git
cd Iris
```

Crea/attiva l'ambiente Python (sviluppato con la 3.11.8) e installa le dipendenze necessarie, incluso `pyinstaller`. Poi compila:
```
pyinstaller Iris.spec
```

Il risultato — tutto il necessario per l'esecuzione — sarà nella cartella `dist`.

## Licenza

Distribuito con licenza [**GPL-3.0-or-later**](LICENCE.txt).

## Sviluppo e note dell'autore

Il progetto nasce per imparare a usare Python; è anche un progetto scolastico, quindi il proseguimento dello sviluppo dipende (anche) dalla mia disciplina — nessuna garanzia di manutenzione continua nel tempo.

Durante lo sviluppo ho usato l'IA come supporto, soprattutto a scopo didattico: niente vibecoding, l'IA è stata un confronto per discutere funzioni e risolvere problemi, non chi ha scritto il progetto al posto mio. L'IA è stata usata anche per la documentazione nel codice sorgente e nel README; il contenuto finale è comunque tutto rivisto da me.

Realizzato con:
- Python 3.11.8
- PySide6
- MediaPipe
- OpenCV
- Pynput

## Contatti

Per segnalazioni, domande o proposte, apri una issue su GitHub.
