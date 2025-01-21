# Traktor to rekordbox (trak2rek)
An open source python script to translate your Traktor Pro collection to rekordbox. <br>
Transfers Tracks, Playlists, Cue points, Tempo, Key, and other metadata. <br>
Developed and tested on Windows with Traktor Pro 3 and rekordbox 7, should work on macOS aswell.

## Requirements
* Python 3.9 or newer
* [ffmpeg](https://ffmpeg.org)
* [ffmpeg-python](https://github.com/kkroening/ffmpeg-python)

## Usage
1. Install python and [ffmpeg](https://ffmpeg.org/download.html)
2. Install ffmpeg-python: `pip install ffmpeg-python`
3. Export your Traktor collection as .nml file or locate it in the Traktor folder (The default location on windows is `<UserData>\Documents\Native Instruments\Traktor <version>\collection.nml`)
4. `python trak2rek.py -t [path/to/your/]collection.nml -r [where/to/save/]rekordbox.xml [-c]` <br> (Use the -c option if you want to convert flac files to wav, as some CDJs don't support flac)
5. Import the rekordbox.xml collection into rekordbox (Might differ for other versions of rekordbox)
   1. In the preferences under "View>Layout>Media browser" make sure "rekordbox xml" is ticked
   2. In the preferences under "Advanced>rekordbox xml>Imported library" browse to the rekordbox.xml file you created in step 4
   3. In the media browser go to the rekordbox xml tab (looks like <>, see red arrow on the screenshot below)
   4. Right click on Playlists to import all playlists and tracks (green arrow)
   5. In case there is a problem with tracks that were already in your collection before importing from the xml file, refer to [this video](https://youtu.be/xzW0jHWSNPk) for a fix

![viewing contents of rekordbox xml](https://github.com/user-attachments/assets/5ea0e64a-c686-48c2-856f-b73816b271c9)

