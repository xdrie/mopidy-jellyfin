from __future__ import unicode_literals

import logging

from mopidy import backend, models


logger = logging.getLogger(__name__)


class JellyfinLibraryProvider(backend.LibraryProvider):

    root_directory = models.Ref.directory(uri='jellyfin:',
                                          name='Jellyfin')

    def browse(self, uri):
        # display top level libraries
        if uri == self.root_directory.uri:
            logger.debug('Get Jellyfin library list')
            return self.backend.remote.get_library_roots()

        # split uri
        parts = uri.split(':')

        # display artists
        # uri: jellyfin:directory
        if uri.startswith('jellyfin:directory:') and len(parts) == 3:
            logger.debug('Get Jellyfin artist list')
            library_id = parts[-1]

            return self.backend.remote.get_artists(library_id)

        # display albums or tracks based on type of parent object
        # uri:
        #   jellyfin:$library_name:artist
        #   jellyfin:$library_name:album
        elif uri.startswith('jellyfin:') and len(parts) == 3:
            item_id = parts[-1]
            item_type = self.backend.remote.get_item(item_id).get('Type')
            logger.debug('Jellyfin item type: {}'.format(item_type))
            if item_type == "Folder":
                return self.backend.remote.get_albums(item_id)
            elif item_type == "MusicAlbum":
                return self.backend.remote.get_tracks(item_id)

        return []

    def lookup(self, uri=None, uris=None):
        logger.debug('Jellyfin lookup: {}'.format(uri or uris))
        if uri:
            parts = uri.split(':')

            if uri.startswith('jellyfin:track:') and len(parts) == 3:
                track_id = parts[-1]
                tracks = [self.backend.remote.get_track(track_id)]

            elif uri.startswith('jellyfin:album:') and len(parts) == 3:
                album_id = parts[-1]
                album_data = self.backend.remote.get_directory(album_id)
                tracks = [
                    self.backend.remote.get_track(i['Id'])
                    for i in album_data.get('Items', [])
                ]

                tracks = sorted(tracks, key=lambda k: k.track_no)

            elif uri.startswith('jellyfin:artist:') and len(parts) == 3:
                artist_id = parts[-1]

                tracks = self.backend.remote.lookup_artist(artist_id)

            else:
                logger.info('Unknown Jellyfin lookup URI: {}'.format(uri))
                tracks = []

            return [track for track in tracks if track]

        else:
            return {uri: self.lookup(uri=uri) for uri in uris}

    def search(self, query=None, uris=None, exact=False):
        return self.backend.remote.search(query)