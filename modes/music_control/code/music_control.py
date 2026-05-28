from functools import partial
from mpf.core.mode import Mode


class MusicControl(Mode):

    def mode_start(self, **kwargs):
        super().mode_start(**kwargs)

        self.current_song = None

        for song_number in range(1, 20):
            self.add_mode_event_handler(
                f"play_song_{song_number}",
                partial(self.play_song, song_number=song_number)
            )

        self.add_mode_event_handler("music_stop_current", self.stop_current_song)


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
