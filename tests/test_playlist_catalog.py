"""Tests for playlist catalog."""

from __future__ import annotations

from pathlib import Path

from downtify.library_catalog import _resolve_playlist_filter_name
from downtify.playlist_catalog import PlaylistCatalog
from downtify.track_index import normalize_spotify_track_id


def test_replace_and_list_tracks(tmp_path: Path) -> None:
    catalog = PlaylistCatalog(tmp_path / 'lib.db')
    track = tmp_path / 'Artist - Song.mp3'
    track.write_bytes(b'audio')
    song = {'song_id': '4uLU6hMCjMI75M1A2tKUQC', 'name': 'Song'}
    catalog.replace_playlist_tracks(
        'My List',
        [(song, 'Artist - Song.mp3', track)],
        spotify_id='playlist12345678901234567890',
    )
    rows = catalog.list_tracks('My List')
    assert len(rows) == 1
    assert rows[0]['filename'] == 'Artist - Song.mp3'
    assert normalize_spotify_track_id(song) == rows[0]['track_spotify_id']


def test_update_filename_by_content_key(tmp_path: Path) -> None:
    track = tmp_path / 't.mp3'
    track.write_bytes(b'12345')
    catalog = PlaylistCatalog(tmp_path / 'lib.db')
    song = {'song_id': '4uLU6hMCjMI75M1A2tKUQC'}
    catalog.upsert_track('Pl', song, 'old/t.mp3', track)
    ck = catalog.list_tracks('Pl')[0]['content_key']
    assert ck
    names = catalog.update_filename_by_content_key(ck, 'new/t.mp3')
    assert 'Pl' in names
    assert catalog.list_tracks('Pl')[0]['filename'] == 'new/t.mp3'


def test_list_playlist_names_prefers_human_title_over_spotify_id(
    tmp_path: Path,
) -> None:
    catalog = PlaylistCatalog(tmp_path / 'lib.db')
    sid = '4uLU6hMCjMI75M1A2tKUQC'
    catalog.ensure_playlist(sid, spotify_id=sid)
    catalog.ensure_playlist('Road Trip', spotify_id=sid)
    assert catalog.list_playlist_names() == ['Road Trip']


def test_delete_playlist_removes_track_rows(tmp_path: Path) -> None:
    """Playlist delete must clear track rows even without FK CASCADE."""

    catalog = PlaylistCatalog(tmp_path / 'lib.db')
    track = tmp_path / 'Artist - Song.mp3'
    track.write_bytes(b'audio')
    catalog.upsert_track(
        'Gone',
        {'song_id': '4uLU6hMCjMI75M1A2tKUQC'},
        'Gone/Artist - Song.mp3',
        track,
    )
    assert catalog.list_tracks('Gone')
    assert catalog.delete_playlist('Gone') == ['Gone/Artist - Song.mp3']
    assert catalog.list_tracks('Gone') == []


def test_resolve_playlist_filter_maps_id_alias_to_named_playlist(
    tmp_path: Path,
) -> None:
    catalog = PlaylistCatalog(tmp_path / 'lib.db')
    track = tmp_path / 'Artist - Song.mp3'
    track.write_bytes(b'audio')
    sid = '4uLU6hMCjMI75M1A2tKUQC'
    song = {'song_id': '6habFhsOp2NvshLv26DqMb'}
    catalog.ensure_playlist(sid, spotify_id=sid)
    catalog.replace_playlist_tracks(
        'Road Trip',
        [(song, 'Artist - Song.mp3', track)],
        spotify_id=sid,
    )
    assert _resolve_playlist_filter_name(catalog, sid) == 'Road Trip'
    assert _resolve_playlist_filter_name(catalog, 'Road Trip') == 'Road Trip'
