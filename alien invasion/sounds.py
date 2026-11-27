"""Sound effects and a small library of background music tracks."""
import os

import pygame

# Folder of this file, so sounds load no matter where the game is started from
SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sounds')


class Sounds:
    EFFECTS = {
        'shoot': 'shoot.wav',
        'explosion': 'explosion.wav',
        'ship_hit': 'ship_hit.wav',
        'level_up': 'level_up.wav',
        'game_over': 'game_over.wav',
    }

    VOLUMES = {
        'shoot': 0.35,
        'explosion': 0.5,
        'ship_hit': 0.6,
        'level_up': 0.5,
        'game_over': 0.6,
    }

    # (text key, file, volume) - the last entry is silence, so it has no file
    TRACKS = (
        ('track_space', 'space_music.wav', 0.45),
        ('track_arcade', 'arcade_music.wav', 0.3),
        ('track_pulse', 'pulse_music.wav', 0.38),
        ('track_none', None, 0.0),
    )

    def __init__(self, track=0, muted=False):
        self.enabled = True
        self.effects = {}
        self.track_index = track % len(self.TRACKS)
        self.muted = bool(muted)

        # If the machine has no working audio device, the game still runs
        try:
            pygame.mixer.init(frequency=22050, channels=2)
        except pygame.error:
            self.enabled = False
            return

        for name, filename in self.EFFECTS.items():
            try:
                sound = pygame.mixer.Sound(os.path.join(SOUND_DIR, filename))
            except (pygame.error, FileNotFoundError):
                continue
            sound.set_volume(self.VOLUMES.get(name, 0.5))
            self.effects[name] = sound

    # ------------------------------------------------------------ effects ---
    def play(self, name):
        if not self.enabled or self.muted:
            return
        sound = self.effects.get(name)
        if sound:
            sound.play()

    # -------------------------------------------------------------- music ---
    @property
    def track_key(self):
        """The text key of the current track, for the control bar label."""
        return self.TRACKS[self.track_index][0]

    def start_music(self):
        """Load and loop the chosen track; silence and mute just stop it."""
        if not self.enabled:
            return
        pygame.mixer.music.stop()
        key, filename, volume = self.TRACKS[self.track_index]
        if filename is None or self.muted:
            return
        path = os.path.join(SOUND_DIR, filename)
        if not os.path.exists(path):
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    def stop_music(self):
        if self.enabled:
            pygame.mixer.music.stop()

    def set_track(self, index):
        self.track_index = index % len(self.TRACKS)
        self.start_music()

    def next_track(self):
        self.set_track(self.track_index + 1)

    def previous_track(self):
        self.set_track(self.track_index - 1)

    def toggle_mute(self):
        """Mute or unmute music and effects together; returns True when muted."""
        self.muted = not self.muted
        self.start_music()
        return self.muted
