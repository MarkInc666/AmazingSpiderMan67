from functools import partial
from mpf.core.mode import Mode


class MusicControl(Mode):

    CHAPTER_BASE_SONGS = {
        1: 1,
        2: 2,
        3: 71,
        4: 79,
        5: 68,
        6: 25,
        7: 67,
        8: 66,
        9: 65,
        10: 78,
        11: 81,
    }

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.current_song = None

        for song_number in range(1, 99):
            self.add_mode_event_handler(
                f"play_song_{song_number}",
                partial(self.play_song, song_number=song_number)
            )

        self.add_mode_event_handler("music_stop_current", self.stop_current_song)
        self.add_mode_event_handler("play_chapter_base_music", self.play_chapter_base_music)


    def play_chapter_base_music(self, **kwargs):
        if not self.machine.game:
            return

        chapter = int(self.machine.game.player["selected_chapter"])
        song_number = self.CHAPTER_BASE_SONGS.get(chapter, 1)
        self.play_song(song_number=song_number)


    def play_song(self, song_number=None, **kwargs):
        song = f"song_{song_number}"

        if self.current_song == song:
            return

        if self.current_song:
            self.machine.events.post(f"stop_music_{self.current_song}")

        self.current_song = song
        self.machine.variables.set_machine_var("current_music_song", song)

        self.machine.events.post(f"play_music_{song}")


    def stop_current_song(self, **kwargs):
        if not self.current_song:
            return

        self.machine.events.post(f"stop_music_{self.current_song}")
        self.machine.variables.set_machine_var("current_music_song", "")

        self.current_song = None
