from argparse import Namespace
from pathlib import Path
from typing import Any

from zotify import OAuth, Session
from zotify.collections import Album, Artist, Collection, Episode, Playlist, Show, Track
from zotify.config import Config
from zotify.file import TranscodingError
from zotify.loader import Loader
from zotify.logger import LogChannel, Logger
from zotify.utils import AudioFormat, PlayableType


class ParseError(ValueError): ...


class Selection:
    def __init__(self, session: Session):
        self.__session = session
        self.__items: list[dict[str, Any]] = []
        self.__print_labels = {
            "album": ("name", "artists"),
            "playlist": ("name", "owner"),
            "track": ("title", "artists", "album"),
            "show": ("title", "creator"),
        }

    def search(
        self,
        search_text: str,
        category: list[str] = [
            "track",
            "album",
            "artist",
            "playlist",
            "show",
            "episode",
        ],
    ) -> list[str]:
        offset = 0
        categories = ",".join(category)
        ids = []
        while True:
            with Loader("Searching..."):
                country = self.__session.api().invoke_url("me")["country"]
                resp = self.__session.api().invoke_url(
                    "search",
                    {
                        "q": search_text,
                        "type": categories,
                        "include_external": "audio",
                        "market": country,
                    },
                    limit=10,
                    offset=offset,
                )

            print(f'Search results for "{search_text}"')
            count = 0
            next_page = {}
            self.__items = []
            for cat in categories.split(","):
                label = cat + "s"
                items = resp[label]["items"]
                next_page[label] = resp[label]["next"]
                if len(items) > 0:
                    print(f"\n{label.capitalize()}:")
                    try:
                        self.__print(count, items, *self.__print_labels[cat])
                    except KeyError:
                        self.__print(count, items, "name")
                    count += len(items)
                    self.__items.extend(items)

            for id in self.__get_selection(allow_empty=True):
                ids.append(id)

            next_flag = False
            for page in next_page.values():
                if page is not None and next_flag is False:
                    next_flag = True
                    params = page.split("?", 1)[1]
                    page_offset = int(params.split("&")[0].split("=")[1])
                    offset = page_offset
                    break

            if not next_flag:
                break

            get_next = self.__get_next_prompt()
            if get_next.lower() == "n":
                break

        return ids

    def get(self, category: str, name: str = "", content: str = "") -> list[str]:
        with Loader("Fetching items..."):
            r = self.__session.api().invoke_url(f"me/{category}", limit=50)

        ids = []
        while True:
            if content != "":
                r = r[content]
            resp = r["items"]

            self.__items = []
            for i in range(len(resp)):
                try:
                    item = resp[i][name]
                except KeyError:
                    item = resp[i]
                self.__items.append(item)
                print(
                    "{:<2} {:<38}".format(
                        i + 1, self.__fix_string_length(item["name"], 38)
                    )
                )

            for id in self.__get_selection():
                ids.append(id)

            if r["next"] is None:
                break

            get_next = self.__get_next_prompt()
            if get_next.lower() == "n":
                break

            with Loader("Fetching items..."):
                r = self.__session.api().invoke_url(r["next"], raw_url=True)

        return ids

    @staticmethod
    def from_file(file_path: Path) -> list[str]:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()]

    def __get_selection(self, allow_empty: bool = False) -> list[str]:
        print("\nResults to save (eg: 1,2,5 1-3)")
        selection = ""
        while len(selection) == 0:
            selection = input("==> ")
            if len(selection) == 0 and allow_empty:
                return []
        ids = []
        selections = selection.split(",")
        for i in selections:
            if "-" in i:
                split = i.split("-")
                for x in range(int(split[0]), int(split[1]) + 1):
                    ids.append(self.__items[x - 1]["uri"])
            else:
                ids.append(self.__items[int(i) - 1]["uri"])
        return ids

    def __print(self, count: int, items: list[dict[str, Any]], *args: str) -> None:
        arg_range = range(len(args))
        category_str = "#  " + " ".join("{:<38}" for _ in arg_range)
        print(category_str.format(*[s.upper() for s in list(args)]))
        for item in items:
            count += 1
            fmt_str = "{:<2} ".format(count) + " ".join("{:<38}" for _ in arg_range)
            fmt_vals: list[str] = []
            for arg in args:
                match arg:
                    case "artists":
                        fmt_vals.append(
                            ", ".join([artist["name"] for artist in item["artists"]])
                        )
                    case "owner":
                        fmt_vals.append(item["owner"]["display_name"])
                    case "album":
                        fmt_vals.append(item["album"]["name"])
                    case "creator":
                        fmt_vals.append(item["publisher"])
                    case "title":
                        fmt_vals.append(item["name"])
                    case _:
                        fmt_vals.append(item[arg])
            print(
                fmt_str.format(
                    *(self.__fix_string_length(fmt_vals[x], 38) for x in arg_range),
                )
            )

    @staticmethod
    def __fix_string_length(text: str, max_length: int) -> str:
        if len(text) > max_length:
            return text[: max_length - 3] + "..."
        return text

    def __get_next_prompt(self) -> str:
        print("\nGet next page? Y/n")
        get_next = None
        while get_next not in ["Y", "y", "N", "n"]:
            get_next = input("==> ")
            if len(get_next) == 0:
                get_next = "y"

        return get_next


class App:
    def __init__(self, args: Namespace):
        self.__config = Config(args)
        self.__existing = {}
        self.__duplicates = {}
        Logger(self.__config)

        # Create session
        if args.username != "" and args.token != "":
            oauth = OAuth(args.username)
            oauth.set_token(args.token, OAuth.RequestType.REFRESH)
            self.__session = Session.from_oauth(
                oauth, self.__config.credentials_path, self.__config.language
            )
        elif self.__config.credentials_path.is_file():
            self.__session = Session.from_file(
                self.__config.credentials_path,
                self.__config.language,
            )
        else:
            username = args.username
            while username == "":
                username = input("Username: ")
            oauth = OAuth(username)
            auth_url = oauth.auth_interactive()
            print(f"\nClick on the following link to login:\n{auth_url}")
            self.__session = Session.from_oauth(
                oauth, self.__config.credentials_path, self.__config.language
            )

        # Get items to download
        ids = self.get_selection(args)
        with Loader("Parsing input..."):
            try:
                collections = self.parse(ids)
            except ParseError as e:
                Logger.log(LogChannel.ERRORS, str(e))
                exit(1)
        if len(collections) > 0:
            with Loader("Scanning collections..."):
                self.scan(collections, args.match)
            self.download_all(collections)
        else:
            Logger.log(LogChannel.WARNINGS, "there is nothing to do")
        exit(0)

    def get_selection(self, args: Namespace) -> list[str]:
        selection = Selection(self.__session)
        try:
            if args.search:
                return selection.search(" ".join(args.search), args.category)
            elif args.playlist:
                return selection.get("playlists")
            elif args.followed:
                return selection.get("following?type=artist", content="artists")
            elif args.liked_tracks:
                return selection.get("tracks", "track")
            elif args.liked_episodes:
                return selection.get("episodes")
            elif args.download:
                ids = []
                for x in args.download:
                    ids.extend(selection.from_file(x.strip()))
                return ids
            elif args.urls:
                return args.urls
        except KeyboardInterrupt:
            Logger.log(LogChannel.WARNINGS, "\nthere is nothing to do")
            exit(130)
        except (FileNotFoundError, ValueError):
            pass
        Logger.log(LogChannel.WARNINGS, "there is nothing to do")
        exit(0)

    def parse(self, links: list[str]) -> list[Collection]:
        collections: list[Collection] = []
        for link in links:
            link = link.rsplit("?", 1)[0]
            try:
                split = link.split(link[-23])
                _id = split[-1]
                id_type = split[-2]
            except IndexError:
                raise ParseError(f'Could not parse "{link}"')

            collection_types = {
                "album": Album,
                "artist": Artist,
                "show": Show,
                "track": Track,
                "episode": Episode,
                "playlist": Playlist,
            }
            try:
                collections.append(
                    collection_types[id_type](_id, self.__session.api(), self.__config)
                )
            except ValueError:
                raise ParseError(f'Unsupported content type "{id_type}"')
        return collections

    def scan(self, collections: list[Collection], match: bool):
        if self.__config.replace_existing:
            return

        if match:
            for collection in collections:
                collection.get_match()

        if self.__config.skip_previous:
            for collection in collections:
                try:
                    existing = collection.get_existing(
                        self.__config.audio_format.value.ext
                    )
                    self.__existing.update(existing)
                except IndexError as err:
                    Logger.log(
                        LogChannel.WARNINGS, f"{err} Cannot scan for existing tracks"
                    )

        if self.__config.skip_duplicates:
            for collection in collections:
                try:
                    duplicates = collection.get_duplicates(
                        self.__config.audio_format.value.ext,
                        self.__config.album_library,
                        self.__config.playlist_library,
                        self.__config.podcast_library,
                    )
                    self.__duplicates.update(duplicates)
                except IndexError as err:
                    Logger.log(
                        LogChannel.WARNINGS, f"{err} Cannot scan for duplicate tracks"
                    )

    def download_all(self, collections: list[Collection]) -> None:
        count = 0
        total = sum(len(c.playables) for c in collections)
        for collection in collections:
            for playable in collection.playables:
                count += 1

                # Skip duplicates and previously downloaded
                if playable.duplicate:
                    Logger.log(
                        LogChannel.SKIPS,
                        f'Skipping "{self.__duplicates[playable.id]}": Duplicated from another collection',
                    )
                    continue
                if playable.existing:
                    Logger.log(
                        LogChannel.SKIPS,
                        f'Skipping "{self.__existing[playable.id]}": Previously downloaded',
                    )
                    continue

                # Get track data
                if playable.type == PlayableType.TRACK:
                    try:
                        with Loader("Adjusting rate limiter..."):
                            self.__session.rate_limiter.check_restore_condition(count)
                        with Loader("Fetching track..."):
                            track = self.__session.get_track(
                                playable.id, self.__config.download_quality
                            )
                    except Exception as err:
                        self.handle_exception(err, playable.type, count, skip=True)
                        continue
                elif playable.type == PlayableType.EPISODE:
                    try:
                        with Loader("Adjusting rate limiter..."):
                            self.__session.rate_limiter.check_restore_condition(count)
                        with Loader("Fetching episode..."):
                            track = self.__session.get_episode(playable.id)
                    except Exception as err:
                        self.handle_exception(err, playable.type, count, skip=True)
                        continue
                else:
                    Logger.log(
                        LogChannel.SKIPS,
                        f'Download Error: Unknown playable content "{playable.type}"',
                    )
                    continue

                # Create download location and generate file name
                track.metadata.extend(playable.metadata)
                if self.__config.save_genre:
                    track.add_genre()
                if self.__config.all_artists:
                    track.add_all_artists()
                try:
                    output = track.create_output(
                        self.__config.audio_format.value.ext,
                        playable.library,
                        playable.output_template,
                        self.__config.replace_existing,
                    )
                except FileExistsError:
                    Logger.log(
                        LogChannel.SKIPS,
                        f'Skipping "{track.name}": Already exists at specified output',
                    )
                    continue

                # Download track
                if not self.__config.lyrics_only:
                    with Logger.progress(
                        desc=f"({count}/{total}) {track.name}",
                        total=track.input_stream.size,
                    ) as p_bar:
                        file = track.write_audio_stream(
                            output, p_bar, self.__config.download_real_time
                        )

                # Download lyrics
                if playable.type == PlayableType.TRACK and self.__config.lyrics_file:
                    if not self.__session.is_premium():
                        Logger.log(
                            LogChannel.SKIPS,
                            f'Failed to save lyrics for "{track.name}": Lyrics are only available to premium users',
                        )
                    else:
                        with Loader("Fetching lyrics..."):
                            try:
                                track.get_lyrics().save(output)
                            except FileNotFoundError as e:
                                Logger.log(LogChannel.SKIPS, str(e))
                Logger.log(
                    LogChannel.DOWNLOADS, f"\nDownloaded {track.name} ({count}/{total}){' lyrics only' if self.__config.lyrics_only else ''}"
                )

                if not self.__config.lyrics_only:
                    # Transcode audio
                    if (
                        self.__config.audio_format != AudioFormat.VORBIS
                        or self.__config.ffmpeg_args != ""
                    ):
                        try:
                            with Loader("Converting audio..."):
                                file.transcode(
                                    self.__config.audio_format,
                                    self.__config.download_quality,
                                    self.__config.transcode_bitrate,
                                    True,
                                    self.__config.ffmpeg_path,
                                    self.__config.ffmpeg_args.split(),
                                )
                        except TranscodingError as e:
                            Logger.log(LogChannel.ERRORS, str(e))

                    # Write metadata
                    if self.__config.save_metadata:
                        with Loader("Writing metadata..."):
                            file.write_metadata(track.metadata)
                            file.write_cover_art(
                                track.get_cover_art(self.__config.artwork_size)
                            )

                    # Remove temp filename
                    file.clean_filename()

                # Reset rate limit counter for every successful download
                self.__session.rate_limiter.clear_consec_hits()

    def handle_exception(
        self,
        err: str,
        playable_type: PlayableType | None = None,
        count: int | None = None,
        skip: bool | None = None,
    ) -> None:

        if skip:
            Logger.log(
                LogChannel.SKIPS, f"Skipping {playable_type.value} #{count}: {err}"
            )

        if "EX01" in str(err):
            try:
                self.__session.rate_limiter.handle_server_limit_hit(True)
            except Exception as e:
                self.handle_exception(e)
        if "EX02" in str(err):
            Logger.log(LogChannel.ERRORS, "Server too busy or down. Try again later")
            exit(1)
