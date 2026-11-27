import sys
from time import sleep

import pygame

import prefs
from alien import Alien
from background import Background
from bullet import Bullet
from button import Button
from camera3d import Camera
from game_stats import GameStats
from hud import ControlBar
from lang import Lang
from scoreboard import Scoreboard
from settings import Settings
from ship import Ship
from sounds import Sounds


class AlienInvasion:
    """A perspective (pseudo-3D) take on Alien Invasion.

    The fleet lives in world space and flies towards the player, so aliens grow
    as they close in. Everything is projected by camera3d.Camera.
    """

    def __init__(self):
        pygame.init()
        self.settings = Settings()

        # Saved choices: language, music track, mute
        self.prefs = prefs.load()
        self.lang = Lang(self.prefs['language'])
        self.sounds = Sounds(track=self.prefs['music_track'],
                             muted=self.prefs['muted'])

        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height))
        pygame.display.set_caption("Alien Invasion 3D")
        self.clock = pygame.time.Clock()

        # The playfield is everything above the control bar
        self.view_rect = pygame.Rect(
            0, 0, self.settings.screen_width,
            self.settings.screen_height - self.settings.control_bar_height)
        self.camera = Camera(self.view_rect)

        self.background = Background(self)
        self.stats = GameStats(self)
        self.ship = Ship(self)
        self.sb = Scoreboard(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self._create_fleet()

        # The Play button and the control bar along the bottom
        self.play_button = Button(self, 'play')
        self.control_bar = ControlBar(self)

        self.sounds.start_music()

    # ------------------------------------------------------------- the loop ---
    def run_game(self):
        while True:
            self._check_events()
            self.background.update()
            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()
            self._update_screen()
            self.clock.tick(self.settings.fps)

    # ---------------------------------------------------------------- fleet ---
    def _create_fleet(self):
        """Build a grid of aliens: columns across, rows receding into depth."""
        columns = self.settings.alien_columns
        spacing = self.settings.column_spacing
        first_x = -(columns - 1) * spacing / 2

        for row in range(self.settings.alien_rows):
            z = self.settings.first_row_z + row * self.settings.row_spacing
            for column in range(columns):
                self.aliens.add(Alien(self, x=first_x + column * spacing, z=z))

    def _check_fleet_edges(self):
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._advance_fleet()
                break

    def _advance_fleet(self):
        """At an edge the fleet turns around and moves closer to the player."""
        for alien in self.aliens.sprites():
            alien.z -= self.settings.fleet_advance
            alien.update_projection()
        self.settings.fleet_direction *= -1

    def _update_aliens(self):
        self._check_fleet_edges()
        self.aliens.update()

        # An alien that reaches the ship's depth is a hit, wherever it is
        reach_z = self.settings.ship_z + 10
        for alien in self.aliens.sprites():
            if alien.z <= reach_z:
                self._ship_hit()
                return

        # And so is one that flies into the ship side-on
        if self._alien_touching_ship():
            self._ship_hit()

    def _alien_touching_ship(self):
        near_z = self.settings.ship_z + Alien.SIZE
        reach_x = (Alien.SIZE + Ship.SIZE) / 2
        for alien in self.aliens.sprites():
            if alien.z <= near_z and abs(alien.x - self.ship.x) <= reach_x:
                return True
        return False

    # -------------------------------------------------------------- bullets ---
    def _fire_bullet(self):
        if len(self.bullets) < self.settings.bullet_allowed:
            self.bullets.add(Bullet(self))
            self.sounds.play('shoot')

    def _update_bullets(self):
        self.bullets.update()
        far_limit = self.settings.first_row_z + (
            self.settings.alien_rows * self.settings.row_spacing) + 80
        for bullet in self.bullets.copy():
            if bullet.z > far_limit:
                self.bullets.remove(bullet)
        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """Collisions are tested in world space, not on screen, so a far alien
        is no harder to hit than a near one."""
        hit_any = False
        reach_x = (Alien.SIZE + Bullet.SIZE) / 2
        reach_z = Alien.SIZE / 2 + max(4.0, self.settings.bullet_speed / 2)

        for bullet in self.bullets.copy():
            for alien in self.aliens.sprites():
                if (abs(alien.x - bullet.x) <= reach_x
                        and abs(alien.z - bullet.z) <= reach_z):
                    self.bullets.remove(bullet)
                    self.aliens.remove(alien)
                    self.stats.score += self.settings.alien_points
                    hit_any = True
                    break

        if hit_any:
            self.sounds.play('explosion')
            self.sb.prep_score()
            self.sb.check_high_score()

        # If the whole fleet is destroyed, clear bullets and create a new fleet
        if not self.aliens:
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            # Move up a level
            self.stats.level += 1
            self.sb.prep_level()
            self.sounds.play('level_up')

    # ----------------------------------------------------------------- hits ---
    def _ship_hit(self):
        # Lose one of the three lives
        self.stats.ships_left -= 1
        self.sb.prep_ships()

        if self.stats.ships_left > 0:
            self.sounds.play('ship_hit')
            self.aliens.empty()
            self.bullets.empty()
            self._create_fleet()
            self.ship.center_ship()
            self._update_screen()
            sleep(0.5)
        else:
            self.sounds.play('game_over')
            self.stats.game_active = False
            pygame.mouse.set_visible(True)
            # Keep the best score even if the window is closed right away
            self.stats.save_high_score()

    # --------------------------------------------------------------- events ---
    def _check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit_game()
                continue
            if event.type == pygame.MOUSEMOTION:
                self._update_cursor(event.pos)
            if self.control_bar.handle_event(event):
                continue
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._check_play_button(pygame.mouse.get_pos())
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_event(event)

    def _update_cursor(self, pos):
        """Hide the pointer over the playfield, but never over the control bar."""
        pygame.mouse.set_visible(
            not self.stats.game_active or self.control_bar.rect.collidepoint(pos))

    def _check_play_button(self, mouse_pos):
        if self.play_button.rect.collidepoint(mouse_pos) and not self.stats.game_active:
            self._start_game()

    def _check_keydown_events(self, event):
        if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
            self.ship.moving_left = True
        elif event.key == pygame.K_p and not self.stats.game_active:
            self._start_game()
        elif event.key == pygame.K_l:
            self.set_language(self.lang.next_language())
        elif event.key == pygame.K_m:
            self.toggle_mute()
        elif event.key == pygame.K_n:
            self.next_track()
        elif event.key == pygame.K_q:
            self._quit_game()
        elif event.key == pygame.K_SPACE and self.stats.game_active:
            self._fire_bullet()

    def _check_keyup_event(self, event):
        if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
            self.ship.moving_left = False

    def _start_game(self):
        self.settings.initialize_dynamic_settings()
        self.stats.reset_stats()
        self.sb.prep_all()
        self.stats.game_active = True

        self.aliens.empty()
        self.bullets.empty()
        self._create_fleet()
        self.ship.center_ship()

        self._update_cursor(pygame.mouse.get_pos())

    def _quit_game(self):
        """Save the high score and the preferences, then close the game."""
        self.stats.save_high_score()
        self._save_prefs()
        self.sounds.stop_music()
        pygame.quit()
        sys.exit()

    # ---------------------------------------------------- control bar hooks ---
    def _save_prefs(self):
        prefs.save({
            'language': self.lang.code,
            'music_track': self.sounds.track_index,
            'muted': self.sounds.muted,
        })

    def set_language(self, code):
        """Switch language and re-render every piece of text."""
        self.lang.set_language(code)
        self.sb.prep_all()
        self.control_bar.refresh()
        self._save_prefs()

    def next_track(self):
        self.sounds.next_track()
        self._save_prefs()

    def previous_track(self):
        self.sounds.previous_track()
        self._save_prefs()

    def toggle_mute(self):
        self.sounds.toggle_mute()
        self._save_prefs()

    # ----------------------------------------------------------------- draw ---
    def _update_screen(self):
        self.screen.fill(self.settings.bg_color)
        self.background.draw()

        # Painter's algorithm: the farthest alien is drawn first
        for alien in sorted(self.aliens.sprites(), key=lambda a: -a.z):
            alien.draw()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.ship.blitme()

        self.sb.show_score()
        if not self.stats.game_active:
            self._draw_start_panel()
        self.control_bar.draw()

        pygame.display.flip()

    def _draw_start_panel(self):
        """Dim the playfield, then show the title or the game-over message."""
        veil = pygame.Surface(self.view_rect.size, pygame.SRCALPHA)
        veil.fill((4, 4, 16, 150))
        self.screen.blit(veil, self.view_rect.topleft)

        heading_key = 'game_over' if self.stats.ships_left <= 0 else 'title'
        heading = self.lang.font(56).render(
            self.lang.ts(heading_key), True, (240, 240, 255))
        self.screen.blit(heading, heading.get_rect(
            center=(self.view_rect.centerx, self.play_button.rect.top - 80)))

        self.play_button.draw_button()

        hint = self.lang.font(20).render(
            self.lang.ts('press_play'), True, (170, 175, 210))
        self.screen.blit(hint, hint.get_rect(
            center=(self.view_rect.centerx, self.play_button.rect.bottom + 34)))


if __name__ == '__main__':
    ai = AlienInvasion()
    ai.run_game()
