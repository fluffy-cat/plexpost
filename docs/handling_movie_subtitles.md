# Post-Processing Subtitles in Movies
## Motivation
Torrented movies come in a wide variety of organisations.
Some come with subtitles at the same level as the main video file.
Others place subtitles in a sub directory.
However, Plex only recognises subtitle files placed in the same directory as the main video file.

For Plex to pick up subtitles in torrented movies, these subtitles must be reorganised into a canonical form.

## Nomenclature
Sidecar(adjective) subtitle: A subtitle that has been placed alongside a video file. Plex can index a movie along with a sidecar subtitle

Sidecar(noun): Shortened form of sidecar subtitle

Sidecar(verb): The act of relocating a subtitle alongside a video file

Vobsub: DirectVobSub subtitle format. This subtitle format consists of an .idx and .sub file

## Scenario Summary
When reorganising subtitles, Plexpost looks at a couple of indicators. These indicators determine how the subtitles will be reorganised.

If a movie already has a sidecar subtitle, no further action is taken.

Otherwise, Plexpost looks for a vobsub file. If it is present, a copy of the idx+sub file is placed alongside the main video file.

Finally, if there are no vobsubs, the highest ranked sub will be sidecar-ed.

When new sidecar files are copied, the original will always be left intact. No subtitles files are deleted during movie post processing.

| | | Has sidecar | - |
| --- | --- | --- | --- |
| | | N | Y |
| Has Vobsub | N | Sidecar sub (3) | Do nothing (1) |
| - | Y | Sidecar vobsub (2) | Do nothing (1) |

## Scenario 0
- No subtitles present

Do nothing

## Scenario 1
- Movie has any type of sidecar subtitles
- Other subtitles may be present

Do nothing

## Scenario 2
- Movie has a vobsub subtitle
- There are no sidecar subtitles
- There is one or more subtitles in sub directory

Sidecar vobsub files

## Scenario 3
- One or more subtitles in sub directory
- No vobsub present
- No sidecar subtitles

Rank subtitles based on filename. Subs containing english|eng|en > english|eng|en with sdh > anything else. Pick highest scoring sub and sidecar it