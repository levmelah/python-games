import pygame, sys
W, H = 800, 600
WHITE, BLACK, RED, GREEN, BLUE, GRAY = (255,255,255), (0,0,0), (255,50,50), (50,205,50), (50,150,255), (100,100,100)

class LevelDevil:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 30)
        self.level = 1
        self.reset_level()

    def reset_level(self):
        self.p = pygame.Rect(50, 450, 40, 40)
        self.p_vel_y = 0
        self.is_jump = False
        self.door = pygame.Rect(700, 420, 40, 80)
        self.f_left = pygame.Rect(0, 500, 300, 100)
        self.f_right = pygame.Rect(500, 500, 300, 100)

        # גשר צ'יט (מקש 1)
        self.bridge = pygame.Rect(300, 500, 200, 20)
        self.bridge_active = False

        # משתני מלכודות
        self.trap_f = pygame.Rect(300, 500, 200, 100) # לבל 1

        # שלב 2: רצפה ימנית שנפתחת לקוצים
        self.f_right_solid = pygame.Rect(620, 500, 180, 100)
        self.f_right_trap = pygame.Rect(500, 500, 120, 100)
        self.lvl2_spikes = pygame.Rect(500, 560, 120, 40)

        self.mid_p = pygame.Rect(320, 500, 160, 100) # לבל 4, 7, 9, 11, 14, 15, 16, 17, 18, 20
        self.spikes = pygame.Rect(340, 500, 120, 0) # לבל 4
        self.wall = pygame.Rect(650, 400, 40, 100) # לבל 7, 20 - משוכה שאפשר לקפוץ מעליה
        self.rain = [pygame.Rect(350 + i*100, -50 - i*100, 30, 30) for i in range(3)] # לבל 6
        self.moving_p = pygame.Rect(320, 500, 160, 20) # לבל 8
        if self.level == 13: self.door = pygame.Rect(700, 180, 40, 80)

        # לבל 10 - רצפה מהבהבת (חייבים לתפוס את הרגע שהיא "דולקת")
        self.blink_floor = pygame.Rect(300, 500, 200, 100)
        self.blink_timer = 0

        # לבל 11 - שער קוצים נופל מהתקרה
        self.ceil_spike = pygame.Rect(500, -100, 40, 100)

        # לבל 12 - מסוע שדוחף אחורה
        self.conveyor = pygame.Rect(300, 500, 300, 100)

        # לבל 13 - מעלית עולה לדלת גבוהה
        self.elevator = pygame.Rect(350, 500, 100, 20)
        self.walkway13 = pygame.Rect(450, 200, 300, 20)

        # לבל 14, 20 - דלת מזויפת שנראית זהה לאמיתית
        self.fake_door = pygame.Rect(600, 420, 40, 80)

        # לבל 16 - שני קירות שנסגרים משני הצדדים
        self.wall_l = pygame.Rect(150, 400, 40, 100)
        self.wall_r = pygame.Rect(650, 400, 40, 100)

        # לבל 17 - כפתור שפותח את הדלת לזמן מוגבל
        self.button = pygame.Rect(350, 470, 40, 30)
        self.door_open_timer = 0

        # לבל 18 - סלעים נופלים
        self.boulders = [pygame.Rect(400, -50 - i*150, 35, 35) for i in range(3)]

        # לבל 19 - שקיעה מהירה + מפתח חדש (2) לגשר
        self.sink_floor19 = pygame.Rect(300, 500, 200, 100)
        self.bridge2_active = False

        self.trig = False
        self.dead = self.win = False

    def update(self):
        if self.dead or self.win:
            if pygame.key.get_pressed()[pygame.K_RETURN]:
                if self.win: self.level = 1 if self.level >= 20 else self.level + 1
                self.reset_level()
            return

        if pygame.key.get_pressed()[pygame.K_1]: self.bridge_active = True
        if pygame.key.get_pressed()[pygame.K_2]: self.bridge2_active = True

        # תנועה ומקשים
        k = pygame.key.get_pressed()
        l, r = k[pygame.K_LEFT] or k[pygame.K_a], k[pygame.K_RIGHT] or k[pygame.K_d]
        if self.level == 3 and self.is_jump: l, r = r, l
        if self.level in (15, 20): l, r = r, l  # בקרות הפוכות קבועות

        self.p.x += (r - l) * 5
        if self.level == 12 and not self.is_jump: self.p.x -= 2  # מסוע דוחף אחורה
        self.p_vel_y += 0.8
        self.p.y += self.p_vel_y
        px = self.p.x

        # לוגיקת מלכודות לפי שלב
        if self.level == 1 and px > 250 and not self.bridge_active: self.trap_f.y += 10
        if self.level == 2 and px > 260: self.trig = True

        if self.level == 4 and self.p.colliderect(self.mid_p) and not self.bridge_active:
            if self.spikes.height < 40: self.spikes.height += 8; self.spikes.y -= 8

        if self.level == 5 and px > 450:
            self.trig = True
            if self.f_right.y < H: self.f_right.y += 12; self.door.y += 2.2

        if self.level == 6:
            for s in self.rain:
                s.y += 6
                if s.y > H: s.y = -50

        if self.level in (7, 20) and px > 450: self.wall.x -= 7
        if self.level == 8:
            if self.p.colliderect(self.moving_p): self.trig = True
            if self.trig: self.moving_p.y += 8

        if self.level == 9 and px > 450: self.door.y = 320

        # לבל 10 - שעון ההבהוב
        if self.level == 10: self.blink_timer += 1

        # לבל 11 - שער קוצים נופל מהתקרה
        if self.level == 11 and px > 400 and self.ceil_spike.y < 460: self.ceil_spike.y += 12

        # לבל 13 - מעלית עולה כל הזמן
        if self.level == 13 and self.elevator.y > 200: self.elevator.y -= 1.5

        # לבל 16 - שני קירות נסגרים משני הצדדים
        if self.level == 16 and px > 300:
            if self.wall_l.x < 300: self.wall_l.x += 6
            if self.wall_r.x > 340: self.wall_r.x -= 6

        # לבל 17 - כפתור פותח דלת לזמן מוגבל
        if self.level == 17:
            if self.p.colliderect(self.button): self.door_open_timer = 90
            if self.door_open_timer > 0: self.door_open_timer -= 1

        # לבל 18 - סלעים נופלים
        if self.level == 18:
            for b in self.boulders:
                b.y += 9
                if b.y > H: b.y = -50

        # לבל 19 - שקיעה מהירה (מפתח 2 פותח גשר בטוח)
        if self.level == 19 and px > 250 and not self.bridge2_active: self.sink_floor19.y += 8

        # התנגשויות רצפה וגשר
        platforms = [self.f_left]
        if self.level == 2:
            platforms.append(self.f_right_solid)
            if not self.trig: platforms.append(self.f_right_trap)
        elif self.level == 5:
            platforms.append(self.f_right)
        else:
            platforms.append(self.f_right)

        if self.level == 1: platforms.append(self.trap_f)
        if self.level in (4, 7, 9, 11, 14, 15, 16, 17, 18, 20): platforms.append(self.mid_p)
        if self.level == 8: platforms.append(self.moving_p)
        if self.bridge_active: platforms.append(self.bridge)

        if self.level == 10 and (self.blink_timer // 80) % 2 == 0: platforms.append(self.blink_floor)
        if self.level == 12: platforms.append(self.conveyor)
        if self.level == 13: platforms.append(self.elevator); platforms.append(self.walkway13)
        if self.level == 19:
            platforms.append(self.bridge if self.bridge2_active else self.sink_floor19)

        for pl in platforms:
            if self.p.colliderect(pl) and self.p_vel_y > 0 and self.p.bottom <= pl.top + 15:
                if self.level == 5 and self.trig and pl == self.f_right: continue
                if self.level == 8 and self.trig and pl == self.moving_p: continue
                self.p.bottom = pl.top; self.p_vel_y = 0; self.is_jump = False

        # בדיקות הפסד (מוות) וניצחון
        if self.p.y > H: self.dead = True
        if self.level == 2 and self.trig and self.p.colliderect(self.lvl2_spikes): self.dead = True
        if self.level == 4 and self.p.colliderect(self.spikes): self.dead = True
        if self.level == 5 and not self.win and (self.p.y > 550 and px > 500): self.dead = True
        if self.level == 6 and any(self.p.colliderect(s) for s in self.rain): self.dead = True
        if self.level in (7, 20) and self.p.colliderect(self.wall): self.dead = True

        # לבל 11, 16, 17, 18, 14/20 - בדיקות מוות נוספות
        if self.level == 11 and self.p.colliderect(self.ceil_spike): self.dead = True
        if self.level == 16 and (self.p.colliderect(self.wall_l) or self.p.colliderect(self.wall_r)): self.dead = True
        if self.level == 17 and self.door_open_timer <= 0 and self.p.colliderect(self.door): self.dead = True
        if self.level == 18 and any(self.p.colliderect(b) for b in self.boulders): self.dead = True
        if self.level in (14, 20) and self.p.colliderect(self.fake_door): self.dead = True

        if self.p.colliderect(self.door):
            if self.level == 17 and self.door_open_timer <= 0:
                pass  # דלת חסומה - כבר סומן כמוות למעלה
            elif self.level != 5 or (self.level == 5 and self.p_vel_y > 0):
                self.win = True

    def draw(self):
        self.screen.fill(BLACK)
        pygame.draw.rect(self.screen, GRAY, self.f_left)

        if self.level == 2:
            pygame.draw.rect(self.screen, GRAY, self.f_right_solid)
            if not self.trig: pygame.draw.rect(self.screen, GRAY, self.f_right_trap)
            else: pygame.draw.rect(self.screen, RED, self.lvl2_spikes)
        else:
            pygame.draw.rect(self.screen, GRAY, self.f_right)

        if self.bridge_active: pygame.draw.rect(self.screen, GRAY, self.bridge)

        if self.level == 1: pygame.draw.rect(self.screen, GRAY, self.trap_f)
        if self.level in (4, 7, 9, 11, 14, 15, 16, 17, 18, 20): pygame.draw.rect(self.screen, GRAY, self.mid_p)
        if self.level == 4: pygame.draw.rect(self.screen, RED, self.spikes)
        if self.level == 5: pygame.draw.rect(self.screen, RED, pygame.Rect(500, 570, 300, 30))
        if self.level == 6: [pygame.draw.rect(self.screen, RED, s) for s in self.rain]
        if self.level in (7, 20): pygame.draw.rect(self.screen, RED, self.wall)
        if self.level == 8: pygame.draw.rect(self.screen, GRAY, self.moving_p)

        if self.level == 10 and (self.blink_timer // 80) % 2 == 0: pygame.draw.rect(self.screen, GRAY, self.blink_floor)
        if self.level == 11: pygame.draw.rect(self.screen, RED, self.ceil_spike)
        if self.level == 12: pygame.draw.rect(self.screen, (200, 150, 50), self.conveyor)
        if self.level == 13:
            pygame.draw.rect(self.screen, GRAY, self.elevator)
            pygame.draw.rect(self.screen, GRAY, self.walkway13)
        if self.level in (14, 20): pygame.draw.rect(self.screen, GREEN, self.fake_door)
        if self.level == 16:
            pygame.draw.rect(self.screen, RED, self.wall_l)
            pygame.draw.rect(self.screen, RED, self.wall_r)
        if self.level == 17: pygame.draw.rect(self.screen, (255, 200, 0), self.button)
        if self.level == 18: [pygame.draw.rect(self.screen, GRAY, b) for b in self.boulders]
        if self.level == 19:
            pygame.draw.rect(self.screen, GRAY, self.bridge if self.bridge2_active else self.sink_floor19)

        door_color = RED if (self.level == 17 and self.door_open_timer <= 0) else GREEN
        pygame.draw.rect(self.screen, door_color, self.door)
        pygame.draw.rect(self.screen, BLUE, self.p)

        self.screen.blit(self.font.render(f"Level: {self.level}", True, WHITE), (20, 20))
        if self.level == 3 and self.is_jump:
            self.screen.blit(self.font.render("IN AIR: INVERTED!", True, RED), (250, 20))

        if self.dead: self.screen.blit(self.font.render("Dead! Press ENTER", True, RED), (300, 250))
        if self.win: self.screen.blit(self.font.render("Win! Press ENTER" if self.level < 20 else "GOD MODE CLEARED!", True, GREEN), (300, 250))
        pygame.display.flip()

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN and e.key in [pygame.K_SPACE, pygame.K_w, pygame.K_UP] and not self.is_jump:
                    self.p_vel_y, self.is_jump = -15, True
                if e.type == pygame.KEYDOWN and e.key == pygame.K_r: self.reset_level()
            self.update(); self.draw(); self.clock.tick(60)

if __name__ == "__main__":
    LevelDevil().run()