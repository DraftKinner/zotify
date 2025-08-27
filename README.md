![Logo banner](./assets/banner.png)

# Zotify

This is a fork of Zotify's [dev branch](https://github.com/zotify-dev/zotify/tree/v1.0-dev) which hasn't seen any activity for months. This fork will be updated to include missing/unimplemented features and maintained by yours truly until the original developers decide to come home with the milk.

A customizable music and podcast downloader. \
Built on [Librespot](https://github.com/kokarare1212/librespot-python).

## Features

- Save tracks at up to 320kbps<sup>**1**</sup>
- Save to most popular audio formats
- Built in search
- Bulk downloads
- Downloads synced lyrics<sup>**2**</sup>
- Embedded metadata
- Downloads all audio, metadata and lyrics directly, no substituting from other services.

**1**: Non-premium accounts are limited to 160kbps \
**2**: Requires premium

## Installation

Requires Python 3.11 or greater. \
Optionally requires FFmpeg to save tracks as anything other than Ogg Vorbis.
<details><summary>Full installation instructions with FFmpeg</summary>

<details><summary>Windows</summary>

This guide uses *Scoop* (https://scoop.sh) to simplify installing prerequisites and *pipx* to manage Zotify itself. 
There are other ways to install and run Zotify on Windows but this is the official recommendation, other methods of installation will not receive support.

- Open PowerShell (cmd will not work)
- Install Scoop by running:
  - `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`
  - `irm get.scoop.sh | iex`
- After installing scoop run: `scoop install python ffmpeg-shared git`
- Install pipx:
  - `python3 -m pip install --user pipx`
  - `python3 -m pipx ensurepath`
- Now close PowerShell and reopen it to ensure the pipx command is available. Proceed to install zotify using the __pipx__ command below.
</details>

<details><summary>macOS</summary>

- Open the Terminal app
- Install *Homebrew* (https://brew.sh) by running: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
- After installing Homebrew run: `brew install python@3.11 pipx ffmpeg git`
- Setup pipx: `pipx ensurepath`
- Proceed to install zotify using either of the commands below.
</details>

<details><summary>Linux (Most Popular Distributions)</summary>

- Install `python3`, `pip` (if a separate package), `ffmpeg`, and `git` from your distribution's package manager or software center.
- Then install pipx, either from your package manager or through pip with: `python3 -m pip install --user pipx`
- Proceed to install zotify using either of the commands below.
</details>

</details>
<br>

Enter the following command in terminal to install the latest stable version of Zotify.
```text
python -m pip install git+https://github.com/DraftKinner/zotify.git

or

pipx install git+https://github.com/DraftKinner/zotify.git
```

Or to install the latest version, use:
```text
python -m pip install git+https://github.com/DraftKinner/zotify.git@dev

or

pipx install git+https://github.com/DraftKinner/zotify.git@dev
```

## General Usage

### Simplest usage

Downloads specified items. Accepts any combination of track, album, playlist, episode or artists, URLs or URIs. \
`zotify <items to download>`

### Basic options

```text
    -p,  --playlist         Download selection of user's saved playlists
    -lt, --liked-tracks     Download user's liked tracks
    -le, --liked-episodes   Download user's liked episodes
    -f,  --followed         Download selection of users followed artists
    -s,  --search <search>  Searches for items to download
```

<details><summary>All configuration options</summary>

| Config key              | Command line argument     | Description                                         | Default                                                    |
| ----------------------- | ------------------------- | --------------------------------------------------- | ---------------------------------------------------------- |
| path_credentials        | --credentials             | Path to credentials file                            |                                                            |
| album_library           | --album-library           | Path to root of album library                       |                                                            |
| podcast_library         | --podcast-library         | Path to root of podcast library                     |                                                            |
| playlist_library        | --playlist-library        | Path to root of playlist library                    |                                                            |
| output_album            | --output-album            | File layout for saved albums                        | {album_artist}/{album}/{track_number}. {artists} - {title} |
| output_playlist_track   | --output-playlist-track   | File layout for tracks in a playlist                | {playlist}/{playlist_number}. {artists} - {title}          |
| output_playlist_episode | --output-playlist-episode | File layout for episodes in a playlist              | {playlist}/{playlist_number}. {episode_number} - {title}   |
| output_podcast          | --output-podcast          | File layout for saved podcasts                      | {podcast}/{episode_number} - {title}                       |
| download_quality        | --download-quality        | Audio download quality (auto for highest available) |                                                            |
| download_real_time      | --download-real-time      | Downloads songs as fast as they would be played     |                                                            |
| artwork_size            | --artwork-size            | Image size of track's cover art                     |                                                            |
| audio_format            | --audio-format            | Audio format of final track output                  |                                                            |
| transcode_bitrate       | --transcode-bitrate       | Transcoding bitrate (-1 to use download rate)       |                                                            |
| ffmpeg_path             | --ffmpeg-path             | Path to ffmpeg binary                               |                                                            |
| ffmpeg_args             | --ffmpeg-args             | Additional ffmpeg arguments when transcoding        |                                                            |
| language                | --language                | Language for metadata, ISO 639-1 language code      |                                                            |
| lyrics_file             | --lyrics-file             | Save lyrics to a file                               |                                                            |
| lyrics_only             | --lyrics-only             | Only download lyrics and not actual audio           |                                                            |
| create_playlist_file    | --playlist-file           | Save playlist information to an m3u8 file           |                                                            |
| save_metadata           | --save-metadata           | Save metadata, required for other metadata options  |                                                            |
| save_genre              | --save-genre              | Add genre to metadata                               |                                                            |
| all_artists             | --all-artists             | Add all track artists to artist tag in metadata     |                                                            |
| replace_existing        | --replace-existing        | Redownload and replace songs if they already exist  |                                                            |
| skip_previous           | --skip-previous           | Skip previously downloaded songs in the playlist    |                                                            |
| skip_duplicates         | --skip-duplicates         | Skip downloading existing track to different album  |                                                            |
| print_downloads         | --print-downloads         | Print messages when a song is finished downloading  |                                                            |
| print_progress          | --print-progress          | Show progress bars                                  |                                                            |
| print_skips             | --print-skips             | Show messages if a song is being skipped            |                                                            |
| print_warnings          | --print-warnings          | Show warnings                                       |                                                            |
| print_errors            | --print-errors            | Show errors                                         |                                                            |

</details>

### Compatibility with official version

Do note that `--skip-previous` and `--skip-duplicates` won't immediately work with playlists and albums downloaded using the official version (both dev and main branches). To make the playlist/album compatible with this fork such that `--skip-previous` and `--skip-duplicates` will both work, simply add the `-m` or `--match` flag to the download command. This will try to match filenames present in the library to ones that are to be downloaded. Note that output formats should match between the current download command and the existing files.

For example:
```
zotify -m <playlist/album_url>
zotify -m -p
zotify -m -d <text_file_with_urls_to_download>
```
This only needs to be done once per existing album or playlist.


### More about search

- `-c` or `--category` can be used to limit search results to certain categories.
  - Available categories are "album", "artist", "playlist", "track", "show" and "episode".
  - You can search in multiple categories at once
- You can also narrow down results by using field filters in search queries
  - Currently available filters are album, artist, track, year, upc, tag:hipster, tag:new, isrc, and genre.
  - Available filters are album, artist, track, year, upc, tag:hipster, tag:new, isrc, and genre.
  - The artist and year filters can be used while searching albums, artists and tracks. You can filter on a single year or a range (e.g. 1970-1982).
  - The album filter can be used while searching albums and tracks.
  - The genre filter can be used while searching artists and tracks.
  - The isrc and track filters can be used while searching tracks.
  - The upc, tag:new and tag:hipster filters can only be used while searching albums. The tag:new filter will return albums released in the past two weeks and tag:hipster can be used to show only albums in the lowest 10% of popularity.

## Usage as a library

Zotify can be used as a user-friendly library for saving music, podcasts, lyrics and metadata.

Here's a very simple example of downloading a track and its metadata:

```python
from zotify import Session

session = Session.from_userpass(username="username", password="password")
track = session.get_track("4cOdK2wGLETKBW3PvgPWqT")
output = track.create_output("./Music", "{artist} - {title}")

file = track.write_audio_stream(output)

file.write_metadata(track.metadata)
file.write_cover_art(track.get_cover_art())
file.clean_filename()
```

## Contributing

Pull requests are always welcome, but if adding an entirely new feature we encourage you to create an issue proposing the feature first so we can ensure it's something that fits the scope of the project.

When reporting bugs or requesting features, ***PLEASE*** check current and closed issues first. Duplicates will be closed immediately.

Zotify aims to be a comprehensive and user-friendly tool for downloading music and podcasts.
It is designed to be simple by default but offer a high level of configuration for users that want it.
All new contributions should follow this principle to keep the program consistent.

## Will my account get banned if I use this tool?

There have been no *confirmed* cases of accounts getting banned as a result of using Zotify.
However, it is still a possiblity and it is recommended you use Zotify with a burner account where possible.

Consider using [Exportify](https://watsonbox.github.io/exportify/) to keep backups of your playlists.

## Disclaimer

Using Zotify violates Sp‌otify user guidelines and may get your account suspended.

Zotify is intended to be used in compliance with DMCA, Section 1201, for educational, private and fair use, or any simlar laws in other regions.
Zotify contributors are not liable for damages caused by the use of this tool. See the [LICENSE](./LICENCE) file for more details.
