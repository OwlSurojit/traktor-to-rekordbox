from argparse import ArgumentParser
import xml.etree.ElementTree as ET
import os
import urllib.parse
import random
import ffmpeg

KEYS = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

def flac2wav_filename(filename):
    directory, file = os.path.split(filename)
    file_no_ext, _ = os.path.splitext(file)
    os.makedirs(f'{directory}/convertedWavs', exist_ok=True)
    return  f'{directory}/convertedWavs/{file_no_ext}.wav'


def camelotToKey(camelot):
    return KEYS[camelot % 12] + ('m' if camelot >= 12 else '')

def trak2rek(trakfile, rekfile, convert_flac):
    trak = ET.parse(trakfile).getroot()
    collection = trak.find('COLLECTION')

    rek = ET.Element('DJ_PLAYLISTS', attrib={'Version': '1.0.0'})
    ET.SubElement(rek, 'PRODUCT', attrib={'Name': 't2r', 'Version': '1.0.0', 'Company': 'roundestrobin'})

    rek_collection = ET.SubElement(rek, 'COLLECTION', attrib={'Entries': collection.get('ENTRIES')})

    for track in collection:
        if track.tag != 'ENTRY':
            continue

        info = track.find('INFO')
        location = track.find('LOCATION')
        tempo = track.find('TEMPO')
        if location is not None:
            filename = location.get('VOLUME') + location.get('DIR', '').replace("/:", "/") + location.get('FILE')
        else:
            filename = ''

        file_extension = filename.rsplit('.', 1)[-1].upper()
        if convert_flac and file_extension == 'FLAC':
            wav_file = flac2wav_filename(filename)
            if os.path.exists(filename):
                if not os.path.exists(wav_file):
                    ffmpeg.input(filename).output(wav_file).run()
                    print(f'Converted {filename} to {wav_file}')
                filename = wav_file
                file_extension = 'WAV'


        rek_track = ET.SubElement(rek_collection, 'TRACK')
        rek_track.set('TrackID', str(hash(filename) % 1000000000))
        rek_track.set('Name', track.get('TITLE', default=''))
        rek_track.set('Artist', track.get('ARTIST', default=''))
        rek_track.set('Album', track.find('ALBUM').get('TITLE', '') if track.find('ALBUM') is not None else '')
        rek_track.set('Composer', '')
        rek_track.set('Genre', info.get('GENRE', '') if info is not None else '')
        rek_track.set('Kind', file_extension + ' File')
        try:
            rek_track.set('Size', str(os.path.getsize(filename)) if filename else '')
        except:
            rek_track.set('Size', '')
        rek_track.set('TotalTime', info.get('PLAYTIME', '') if info is not None else '')
        rek_track.set('Year', info.get('RELEASEDATE', '').split("/")[0] if info is not None else '')
        rek_track.set('AverageBpm', tempo.get('BPM', '') if tempo is not None else '')
        rek_track.set('DateAdded', info.get('IMPORT_DATE', '') if info is not None else '')
        rek_track.set('BitRate', info.get('BITRATE', '') if info is not None else '')
        rek_track.set('Comments', info.get('COMMENT', '') if info is not None else '')
        rek_track.set('PlayCount', info.get('PLAYCOUNT', '') if info is not None else '')
        rek_track.set('Rating', str(int(info.get('RANKING', 0)) // 51) if info is not None else '')
        rek_track.set('Location', urllib.parse.quote('file://localhost/' + filename, safe = ':/()') if filename else '')
        rek_track.set('Tonality', camelotToKey(int(track.find('MUSICAL_KEY').get('VALUE', 0))) if track.find('MUSICAL_KEY') is not None else '')
        rek_track.set('Label', info.get('LABEL', '') if info is not None else '')

        autogrid_cue = track.find('.//CUE_V2[@NAME="AutoGrid"]')
        if autogrid_cue is not None:
            rek_tempo = ET.SubElement(rek_track, 'TEMPO')
            rek_tempo.set('Inizio', str(float(autogrid_cue.get('START', '0')) / 1000))
            rek_tempo.set('Bpm', tempo.get('BPM', '') if tempo is not None else '')
            rek_tempo.set('Metro', '4/4')
            rek_tempo.set('Battito', '1')

        for cue in track.findall('CUE_V2'):
            rek_cue = ET.SubElement(rek_track, 'POSITION_MARK')
            rek_cue.set('Name', cue.get('NAME', ''))
            rek_cue.set('Type', '0')
            rek_cue.set('Start', str(float(cue.get('START', 0)) / 1000))
            rek_cue.set('Num', cue.get('HOTCUE', ''))
            rek_cue.set('Red', str(random.randint(0, 255)))
            rek_cue.set('Green', str(random.randint(0, 255)))
            rek_cue.set('Blue', str(random.randint(0, 255)))

        """ 
        TRACK tags
            TrackID (9 digits) --> from title or AUDIO_ID
            Name = TITLE
            Artist = ARTIST
            Composer = ""
            Album = <ALBUM>.TITLE
            Genre = <INFO>.GENRE
            Kind (MP3 File) --> from <LOCATION>.FILE
            Size = os.path.getsize(file)
            TotalTime = <INFO>.PLAYTIME
            Year --> from <INFO>.RELEASEDATE
            AverageBpm = <TEMPO>.BPM
            DateAdded = <INFO>.IMPORT_DATE
            BitRate = <INFO>.BITRATE
            SampleRate --> N/A
            Comments = <INFO>.COMMENT
            PlayCount = <INFO>.PLAYCOUNT
            Rating = <INFO>.RANKING / 51
            Location (file://localhost/C:/...) --> from <LOCATION>.VOLUME + <LOCATION>.DIR + <LOCATION>.FILE (remove :)
            Tonality --> camelot wheel from <MUSICAL_KEY>.VALUE
            Label = <INFO>.LABEL
            TEMPO tags (not 100% if this is universal, could also just let rekordbox do its thing...)
                Inizio = <CUE_V2 (Name == AutoGrid)>. START / 1000
                Bpm = <TEMPO>.BPM
                Metro = 4/4 ig
                Battito = 1 ig
            POSITION_MARK tags ~ CUE_V2 tags
                Name = NAME
                Type = TYPE
                Start = START / 1000
                Num = HOTCUE
                Red/Green/Blue = whatev
        """

    playlists = trak.find('PLAYLISTS')
    if playlists is not None:
        def translate_playlist(node, rek_node):
            if node.get('TYPE') == 'FOLDER':
                subnodes = node.find('SUBNODES')
                if subnodes is None:
                    return
                rek_folder = ET.SubElement(rek_node, 'NODE')
                folder_name = node.get('NAME', '')
                rek_folder.set('Name', folder_name if folder_name != '$ROOT' else 'ROOT')
                rek_folder.set('Type', '0')
                rek_folder.set('Count', subnodes.get('COUNT', '0'))
                for subnode in node.find('SUBNODES'):
                    translate_playlist(subnode, rek_folder)
            elif node.get('TYPE') == 'PLAYLIST':
                playlist = node.find('PLAYLIST')
                if playlist is None:
                    return
                rek_playlist = ET.SubElement(rek_node, 'NODE')
                rek_playlist.set('Name', node.get('NAME', ''))
                rek_playlist.set('Type', '1')
                rek_playlist.set('KeyType', '0')
                rek_playlist.set('Entries', playlist.get('ENTRIES', '0'))
                for entry in playlist.findall('ENTRY'):
                    rek_playlist_track = ET.SubElement(rek_playlist, 'TRACK')
                    if entry.find('PRIMARYKEY') is not None:
                        playlist_track_filename = entry.find('PRIMARYKEY').get('KEY', '').replace('/:', '/')
                    else:
                        continue
                    if convert_flac and os.path.splitext(playlist_track_filename)[1].upper() == '.FLAC':
                        playlist_track_filename = flac2wav_filename(playlist_track_filename)
                    rek_playlist_track.set('Key', str(hash(playlist_track_filename) % 1000000000))

        root_node = playlists.find('NODE')
        rek_playlists = ET.SubElement(rek, 'PLAYLISTS')
        translate_playlist(root_node, rek_playlists)


        """
        Playlists
        NODE 
            Name = <PLAYLIST>.NAME
            Type = "1"
            KeyType = "0"
            Entries = <PLAYLIST>.ENTRIES
            TRACK
                Key = TrackID corresponding to PRIMARYKEY track
        """

    rek_tree = ET.ElementTree(rek)
    ET.indent(rek_tree, space='  ', level=0)
    rek_tree.write(rekfile, encoding='utf-8', xml_declaration=True)


def main():
    parser = ArgumentParser()
    parser.add_argument('-t', '-i', '--traktor', help='Input traktor collection.nml file', default='$COLLECTION.nml')    
    parser.add_argument('-r', '-o', '--rekordbox', help='Output rekordbox.xml file', default='rekordbox.xml')
    parser.add_argument('-c', '--convert-flac', help='Convert FLAC files to WAV', action='store_true')
    args = parser.parse_args()
    trak2rek(args.traktor, args.rekordbox, args.convert_flac)

if __name__ == '__main__':
    main()