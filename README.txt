Iris 0.1.0
Control your desktop in a different way.

https://github.com/Cheng98989/Iris


RUNNING IT
----------
Double-click Iris.exe. There is no installer.

The first time, Windows may show "Windows protected your PC", because
Iris.exe is not digitally signed. To go ahead, click "More info", then
"Run anyway". Some antivirus software may quarantine the file for the
same reason.

Iris needs a working webcam, and has only been tested on Windows 11.


THE TWO KEYS TO REMEMBER
------------------------
Esc    Closes Iris straight away, even while it runs in the background.
       Use it if a misread gesture starts doing something you did not
       ask for.

F12    Pauses Iris. Gestures keep being recognised but nothing is acted
       on, until you press F12 again.


WHERE EVERYTHING IS
-------------------
Once started, Iris has no window of its own: it lives in the system
tray, next to the clock. Click its icon for the menu:

  Preview     show or hide the camera preview
  Settings    open the settings panel
  Restart     restart Iris
  Quit        close Iris

Closing the preview window does not close Iris. It keeps running in the
background.


LIMITATIONS
-----------
The pointer stops answering your gestures over windows that run with
administrator privileges. Windows prevents it on purpose, and there are
two separate cases.

The administrator privileges prompt. When Windows asks you to confirm
an elevation, it switches to a separate, protected desktop where no
application can send input. There is no way around it: that screen
exists precisely so that no software can answer on your behalf. Use the
mouse and the keyboard to confirm or cancel.

The windows of apps started as administrator. An ordinary application
cannot send input to a window with higher privileges, so the pointer
stays put for as long as one of those is in the foreground. It answers
again as soon as you switch to another window.

If you need gesture control over those applications too, start Iris by
right-clicking Iris.exe and choosing "Run as administrator". That only
covers the second case: the privileges prompt stays out of reach either
way.


YOUR FILES
----------
Iris keeps its data in %appdata%\Iris

  config.json    your settings
  iris.log       what went wrong, if anything did
  audio\         the sounds you picked for the states

To get there, paste %appdata%\Iris into the address bar of any folder
window.


UNINSTALLING
------------
Delete the folder you extracted. If you want your settings gone too,
delete %appdata%\Iris as well. Nothing is written anywhere else, and
nothing is added to the registry.


PRIVACY
-------
Iris does not collect or send webcam images over the Internet. All
processing happens on your own computer.


HELP AND BUGS
-------------
Full documentation, in English and Italian, is on the project page:

  https://github.com/Cheng98989/Iris

Found a problem? Open an issue there. If Iris closed on its own, attach
%appdata%\Iris\iris.log: it records what went wrong.


LICENCE
-------
GPL-3.0-or-later. The full text is in LICENCE.txt, next to this file.
