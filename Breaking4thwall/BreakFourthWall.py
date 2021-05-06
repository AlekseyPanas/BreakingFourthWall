import pygame
import copy
import math
import random
import time
pygame.init()

# Rework sprite management     DONE
# Test inflates                DONE
# Add health text              DONE
# Add damage inflates          DONE
# Add collision logic          DONE
# Add slashes                  DONE
# Add pause button             DONE
# Add pause menu with restart and quit buttons    DONE
# Add gameover restart screen  DONE
# Add dialogue framework

# Add restart button knockout cutscene
# Add restart button game logic


class Game:
    FRICTION = 0.99

    def __init__(self, fourth_wall=False):
        self.RESET_GAME = False

        self.PAUSED = False
        self.WIN = False
        self.LOSS = False

        self.UNPAUSABLE = False

        self.IS_CUTSCENE = False
        self.CUTSCENE_STRING = ""

        self.BOSS = Boss(-1, 1)
        self.PLY = Player(-1, 1)

        # Current list, add queue list, and delete queue list for each item
        self.BULLETS = []
        self.bullet_q = []
        self.bullet_dq = []

        self.SLASHES = []
        self.slash_q = []
        self.slash_dq = []

        self.OTHER = []
        self.other_q = []
        self.other_dq = []

        self.RESTART = Button((SIZE[0] / 2, SIZE[1] / 3), (0, 0), (80, 35), pygame.image.load("reset.png"))
        self.BACK = Button((SIZE[0] / 2, SIZE[1] / 4), (0, 0), (80, 35), pygame.image.load("back.png"))
        self.PAUSE = Button((SIZE[0] * .9, SIZE[1] * .1), (0, 0), (80, 35), pygame.image.load("pause.png"))

        self.PAUSED_TEXT = get_arial_font_bold(50).render("Game Paused", True, (0, 0, 0)).convert_alpha()
        self.WIN_TEXT = get_arial_font_bold(50).render("You Win!", True, (0, 100, 0)).convert_alpha()
        self.LOSS_TEXT = get_arial_font_bold(50).render("You Lost!", True, (100, 0, 0)).convert_alpha()

        if not fourth_wall:
            self.BOSS.add_dialogue("I WILL DESTROY YOU!!", 5, 10)
        else:
            self.IS_CUTSCENE = True
            self.CUTSCENE_STRING = "restart"
            self.BOSS.add_dialogue("And you really thought you had me there huh...", 5, 20)

        # Calculates how fast the player is doing damage to the boss. If bad enough, mouse will be bound
        self.damage_accum = 0
        self.damage_dialogue = ["No more mousing around",
                                "Now stay there!",
                                "Stay!",
                                "Don't move",
                                "No more moving",
                                "Try aiming now!"]

        self.bind_counter = 0

    def run_game(self, screen):
        print(self.damage_accum)
        # Manages damage accumulation
        if self.damage_accum > 0:
            self.damage_accum -= .6
        if self.damage_accum < 0:
            self.damage_accum = 0
        if self.damage_accum > 170:
            self.PLY.bind_mouse([random.randint(50, 550) for _ in range(2)])
            self.bind_counter = 1000
            self.damage_accum = 0

            self.BOSS.clear_dialogue()
            self.BOSS.add_dialogue(random.choice(self.damage_dialogue), 5, 25)

        if self.bind_counter > 0:
            self.bind_counter -= 1
            if self.bind_counter == 0:
                self.PLY.unbind_mouse()

        # Manages all cutscenes using state machine with CUTSCENE_STRING
        if self.IS_CUTSCENE:
            if self.CUTSCENE_STRING == "restart":
                if not len(self.BOSS.dialogue_queue):
                    self.IS_CUTSCENE = False

            elif self.CUTSCENE_STRING == "i_1":
                # Boss moves towards point
                target = SIZE[0] / 2, SIZE[1] * .7

                y = target[1] - self.BOSS.pos[1]
                x = target[0] - self.BOSS.pos[0]
                h = math.sqrt(y ** 2 + x ** 2)
                y = (y / h)
                x = (x / h)
                self.BOSS.vel = (x, y)

                self.BOSS.update_physics(screen, self)

                if distance(target, self.BOSS.pos) < 20:
                    self.BOSS.vel = (0, 0)
                    self.CUTSCENE_STRING = "i_2"

            elif self.CUTSCENE_STRING == "i_2":
                self.BOSS.add_dialogue("Really? You're just gonna pause to give yourself a break?", 4, 15)
                self.BOSS.add_dialogue("I don't think so...", 10, 10)
                self.CUTSCENE_STRING = "i_3"

            elif self.CUTSCENE_STRING == "i_3":
                if not len(self.BOSS.dialogue_queue):
                    self.CUTSCENE_STRING = "i_4"

            elif self.CUTSCENE_STRING == "i_4":
                self.CUTSCENE_LASER = Laser(copy.copy(self.BOSS.pos), copy.copy(self.RESTART.pos))
                self.RESTART.height_vel = 5
                self.RESTART.vel = ((random.randint(20, 40) / 10) * random.choice([-1, 1]), 1)

                self.CUTSCENE_STRING = "i_5"

            elif self.CUTSCENE_STRING == "i_5":
                self.CUTSCENE_LASER.update(screen, self)
                self.CUTSCENE_LASER.render(screen, self)

                if self.RESTART.height <= 0:
                    self.RESTART.vel = (0, 0)

                    self.CUTSCENE_COUNT = 20
                    self.CUTSCENE_STRING = "i_6"

            elif self.CUTSCENE_STRING == "i_6":
                if self.CUTSCENE_COUNT > 0:
                    self.CUTSCENE_COUNT -= 1
                else:
                    self.CUTSCENE_STRING = "i_7"

            elif self.CUTSCENE_STRING == "i_7":
                self.BOSS.add_dialogue("Careful not to restart! Mwahaha!!!", 8, 15)
                self.BOSS.add_dialogue("Oh.. And no more pausing!", 7, 10)
                self.CUTSCENE_STRING = "i_8"

            elif self.CUTSCENE_STRING == "i_8":
                if not len(self.BOSS.dialogue_queue):
                    self.CUTSCENE_STRING = "i_9"

            elif self.CUTSCENE_STRING == "i_9":
                self.add_other(Laser(copy.copy(self.BOSS.pos), copy.copy(self.PAUSE.pos)))
                CUTSCENE_FRAGMENTS = fragmentate(self.PAUSE.image, self.PAUSE.pos)
                for frag in CUTSCENE_FRAGMENTS:
                    frag.vel = random.randint(-40, 10) / 10, random.randint(-10, 40) / 10

                self.add_other(CUTSCENE_FRAGMENTS[0])
                self.add_other(CUTSCENE_FRAGMENTS[1])

                self.PAUSED = False
                self.UNPAUSABLE = True
                self.IS_CUTSCENE = False

        # Checks for Cutscene conditions
        if not self.IS_CUTSCENE:
            if self.PAUSED and self.BOSS.health / self.BOSS.full_health <= 0.5 and (not (self.WIN or self.LOSS)) and (not self.UNPAUSABLE):
                print("OMG")
                self.IS_CUTSCENE = True
                self.CUTSCENE_STRING = "i_1"

        # Events
        if not self.IS_CUTSCENE:
            rem = []
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT:
                    # Pause Button Pauses Game
                    if (not self.UNPAUSABLE) and self.PAUSE.is_clicked(event.pos):
                        self.PAUSED = True
                        rem.append(event)

                    # Back button returns to game
                    elif self.PAUSED and not (self.WIN or self.LOSS) and self.BACK.is_clicked(event.pos):
                        self.PAUSED = False

                    # Restart button restarts game
                    elif (self.PAUSED or self.UNPAUSABLE) and self.RESTART.is_clicked(event.pos):
                        self.RESET_GAME = True
                        if self.UNPAUSABLE and (not (self.WIN or self.LOSS)):
                            set_4th_wall_toggle(True)

            for event in rem:
                if event in events:
                    events.remove(event)

        # Runs logic for boss and player
        self.BOSS.run_sprite(screen, self)
        self.PLY.run_sprite(screen, self)

        # Runs logic for bullets, slashes, and other objects
        for o in self.SLASHES + self.BULLETS + self.OTHER:
            o.run_sprite(screen, self)

        # Runs logic for buttons
        if self.PAUSED or self.UNPAUSABLE:
            self.RESTART.run_sprite(screen, self)

            # If the game is in the unpausable state, restart button chases mouse
            if self.UNPAUSABLE:
                y = pygame.mouse.get_pos()[1] - self.RESTART.pos[1]
                x = pygame.mouse.get_pos()[0] - self.RESTART.pos[0]
                h = math.sqrt(y ** 2 + x ** 2)
                y = (y / h) * 1.5
                x = (x / h) * 1.5

                self.RESTART.vel = (x, y)

        if self.PAUSED:
            if not (self.WIN or self.LOSS):
                self.BACK.run_sprite(screen, self)

            if self.WIN:
                screen.blit(self.WIN_TEXT, self.WIN_TEXT.get_rect(center=(SIZE[0] / 2, SIZE[1] / 5)))
            elif self.LOSS:
                screen.blit(self.LOSS_TEXT, self.LOSS_TEXT.get_rect(center=(SIZE[0] / 2, SIZE[1] / 5)))
            else:
                screen.blit(self.PAUSED_TEXT, self.PAUSED_TEXT.get_rect(center=(SIZE[0] / 2, SIZE[1] / 7)))
        if not self.UNPAUSABLE:
            self.PAUSE.run_sprite(screen, self)

        # Win conditions
        if self.PLY.health <= 0:
            self.LOSS = True
            self.PAUSED = True
        elif self.BOSS.health <= 0:
            self.WIN = True
            self.PAUSED = True

        # Runs object updater
        if not self.PAUSED and not self.IS_CUTSCENE:
            self.update_objects()

    def update_objects(self):
        # Decreases lifetime for all objects
        for obj in self.BULLETS + self.SLASHES + self.OTHER:
            obj.lifetime -= 1

        # Removes dead objects by kill flag or by lifetime count
        self.BULLETS = [b for b in self.BULLETS if not b.kill and b.lifetime > 0]
        self.SLASHES = [s for s in self.SLASHES if not s.kill and s.lifetime > 0]
        self.OTHER = [o for o in self.OTHER if not o.kill and o.lifetime > 0]

        # Removes objects in delete queues
        for b in self.bullet_dq:
            self.BULLETS.remove(b)
        for s in self.slash_dq:
            self.SLASHES.remove(s)
        for o in self.other_dq:
            self.OTHER.remove(o)

        # Adds new objects
        for b in self.bullet_q:
            self.BULLETS.append(b)
        for s in self.slash_q:
            self.SLASHES.append(s)
        for o in self.other_q:
            self.OTHER.append(o)

        # Clears queues
        self.bullet_q = []
        self.bullet_dq = []

        self.slash_q = []
        self.slash_dq = []

        self.other_q = []
        self.other_dq = []

    # Add and delete methods for all object types
    def add_bullet(self, bullet):
        self.bullet_q.append(bullet)

    def add_slash(self, slash):
        self.slash_q.append(slash)

    def add_other(self, other):
        self.other_q.append(other)

    def delete_bullet(self, bullet):
        self.bullet_dq.append(bullet)

    def delete_slash(self, slash):
        self.slash_dq.append(slash)

    def delete_other(self, other):
        self.other_dq.append(other)


class Object:
    def __init__(self, lifetime, z_order, tags):
        self.lifetime = lifetime
        self.kill = False

        # Draw order
        self.z_order = z_order

        # Set of string tags that can identify an object
        self.tags = set(tags)

    @staticmethod
    def rotate(image, rect, angle):
        """Rotate the image while keeping its center."""
        # Rotate the original image without modifying it.
        new_image = pygame.transform.rotate(image, angle)
        # Get a new rect with the center of the old rect.
        rect = new_image.get_rect(center=rect.center)
        return new_image, rect

    def run_sprite(self, screen, game):
        self.render(screen, game)
        if not game.PAUSED and not game.IS_CUTSCENE:
            self.update(screen, game)

    def render(self, screen, game):
        pass

    def update(self, screen, game):
        pass


class Button(Object):
    BUTTON_GRAVITY = 0.2

    def __init__(self, pos, vel, size, image):
        super().__init__(0, 0, {})

        # Position of center of button.
        self.pos = list(pos)
        self.vel = list(vel)

        # For popping effect when knocked out of pause menu
        self.height = 0
        self.height_vel = 0

        # Width/height of image and the loaded image.
        self.size = size
        self.image = pygame.transform.scale(image, (size[0], size[1]))

        self.button_rect = self.image.get_rect(center=self.pos)

        self.button_state = "static"

    def run_sprite(self, screen, game):
        self.render(screen, game)
        self.update(screen, game)

    def render(self, screen, game):
        screen.blit(self.image, self.button_rect)

    def update(self, screen, game):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

        self.height += self.height_vel
        self.height_vel -= Button.BUTTON_GRAVITY
        if self.height < 0:
            self.height = 0
            self.height_vel = 0

        self.button_rect.center = (self.pos[0], self.pos[1] - self.height)

    def jump(self, height_vel):
        self.height_vel = height_vel

    def is_clicked(self, pos):
        return self.button_rect.collidepoint(pos)


class Boss(Object):
    SPEED = 2

    def __init__(self, lifetime, z_order):
        super().__init__(lifetime, z_order, {})

        self.pos = [SIZE[1] / 4, SIZE[1] / 2]
        self.radius = 20
        self.color = (255, 0, 0)

        self.vel = [0, 0]

        self.dialogue_queue = []  # {"text": "hello", "delay": 5, "total_lifetime": 40}
        self.current_text_idx = [0]
        self.rendered_texts = []
        self.current_text = []

        self.full_health = 5000
        self.health = 0
        self.health_text = None
        self.update_health(self.full_health)

        # Always counts down if above 0. Only shows hp above zero. Increase when taken damage to show hp
        self.show_hp = 100

        self.textbox_surf = pygame.Surface((self.radius * 7, self.radius * 5), pygame.SRCALPHA, 32)
        pygame.draw.rect(self.textbox_surf, (200, 200, 200), pygame.Rect(0, 0, self.radius * 7, self.radius * 4.5))
        pygame.draw.polygon(self.textbox_surf, (200, 200, 200), ((self.radius*3, self.radius * 4.5), (self.radius*4, self.radius * 4.5), (self.radius*3.5, self.radius*5)))
        self.textbox_surf = self.textbox_surf.convert_alpha()

        self.dialogue_size = self.radius * .7
        self.dialogue_font = get_arial_font(int(self.dialogue_size))
        self.dialogue_gap = self.radius * .05
        self.dialogue_max_line_width = self.textbox_surf.get_rect().width * 0.8

    def add_dialogue(self, text, delay, extra_lifetime):
        self.dialogue_queue.append({"text": text, "delay": delay, "total_lifetime": len(text) + extra_lifetime})

    def clear_dialogue(self):
        self.dialogue_queue = []

    def run_sprite(self, screen, game):
        self.render(screen, game)
        if not game.PAUSED and not game.IS_CUTSCENE:
            self.update(screen, game)
        self.run_dialogue(screen, game)

    def run_dialogue(self, screen, game):
        # Resets text
        if not len(self.dialogue_queue):
            self.current_text_idx = [0]
            self.rendered_texts = []
            self.current_text = []

        else:
            cur_dial = self.dialogue_queue[0]
            text = cur_dial["text"]

            # Calculates text
            if not len(self.current_text):
                split_words = text.split()
                split_words = [i if idx == len(split_words) - 1 else (i + " ") for idx, i in enumerate(split_words)]

                while True:
                    # Is the inner loop done
                    finish_inner = False

                    # The word at which to end slicing
                    word_cutoff = 1

                    if not len(split_words):
                        break

                    while not finish_inner:
                        # Gets all words up to word_cutoff and strips the last word removing the trailing space
                        current_line = split_words[:word_cutoff]
                        current_line[-1] = current_line[-1].strip()

                        # Checks how long this modified line is
                        line_length = self.dialogue_font.size("".join(current_line))[0]

                        # If the modified line is too long or the end of the list has been reached:
                        if line_length > self.dialogue_max_line_width or word_cutoff > len(split_words):
                            # Go back a step to the word cut_off where it wasnt too long
                            word_cutoff -= 1

                            # Recreate that old line
                            current_line = split_words[:word_cutoff]
                            current_line[-1] = current_line[-1].strip()

                            # Add the new line to the dialogue list
                            self.current_text.append("".join(current_line))

                            # Remove the added line by slicing up to the word count
                            split_words = split_words[word_cutoff:]

                            # End the inner loop
                            finish_inner = True
                        else:
                            # If all is good, move to next word
                            word_cutoff += 1

            # Shifts letter
            if ticks % cur_dial["delay"] == 0:

                # Deals with indexing of the current letter in each sentence
                self.current_text_idx[-1] += 1
                if not len(self.current_text_idx) > len(self.current_text):
                    if self.current_text_idx[-1] >= len(self.current_text[len(self.current_text_idx) - 1]):
                        self.current_text_idx[-1] -= 1
                        self.current_text_idx.append(0)

                if not len(self.current_text_idx) > len(self.current_text):
                    # Renders new text
                    self.rendered_texts = []
                    for idx, i in enumerate(self.current_text_idx):
                        self.rendered_texts.append(self.dialogue_font.render(self.current_text[idx][:i+1], True, (20, 0, 0)))

            # Deletes
            if sum(self.current_text_idx) >= cur_dial["total_lifetime"]:
                self.dialogue_queue.pop(0)
                self.current_text_idx = [0]
                self.rendered_texts = []
                self.current_text = []

    def render(self, screen, game):
        pygame.draw.circle(screen, self.color, self.pos, self.radius)

        if self.show_hp > 0:
            screen.blit(self.health_text, self.health_text.get_rect(center=(self.pos[0], self.pos[1] + self.radius*1.5)))

        if len(self.dialogue_queue):
            # Render text box
            screen.blit(self.textbox_surf, self.textbox_surf.get_rect(center=(self.pos[0], self.pos[1] - self.radius*3.5)))

            # Render text
            if len(self.rendered_texts):
                dialogue_box_center_height = self.pos[1] - self.radius * 3.5
                total_height = len(self.rendered_texts) * (self.dialogue_size + self.dialogue_gap)

                shift_back_constant = self.dialogue_size / 2 + self.dialogue_gap

                start_height = dialogue_box_center_height - (total_height / 2)

                for i in range(len(self.rendered_texts)):
                    screen.blit(self.rendered_texts[i], self.rendered_texts[i].get_rect(center=(self.pos[0], start_height + (self.dialogue_size + self.dialogue_gap) * (i + 1) - shift_back_constant)))

    def update_health(self, health):
        self.health = health
        self.health_text = get_arial_font(13).render(str(self.health), True, (225, 0, 0))

    def take_damage(self, game, damage):
        self.update_health(self.health - damage)
        game.add_other(InflateSurface(200, 0, {}, get_damage_surface(damage), .5, 1.5, 50, copy.copy(self.pos), True, vel=(random.randint(-10, 10) / 10, -2)))
        self.show_hp = 100

        game.damage_accum += 20

    def update(self, screen, game):
        self.run_AI(screen, game)

        self.update_physics(screen, game)

    def update_physics(self, screen, game):
        self.pos[0] += self.vel[0] * self.SPEED
        self.pos[1] += self.vel[1] * self.SPEED

        if self.show_hp > 0:
            self.show_hp -= 1

    def run_AI(self, screen, game):
        x = game.PLY.pos[0] + game.PLY.vel[0] * 50 - self.pos[0]
        y = game.PLY.pos[1] + game.PLY.vel[1] * 50 - self.pos[1]
        h = math.sqrt(y ** 2 + x ** 2)

        try:
            x = (x / h) * 5
            y = (y / h) * 5
        except:
            x = 0
            y = 0

        x += random.uniform(-1, 1)
        y += random.uniform(-1, 1)

        if ticks % 5 == 0:
            if distance(self.pos, game.PLY.pos) < (self.radius + game.PLY.radius) * 4:
                game.add_slash(Slash(False, (100, 0, 100), [self.pos[0] + x*10, self.pos[1] + y*10]))
            else:
                game.add_bullet(Bullet(copy.copy(self.pos), (x, y), False))

        self.vel = [0, 0]

        vel = [game.PLY.pos[0] - self.pos[0], game.PLY.pos[1] - self.pos[1]]
        try:
            vel = [vel[0] / math.sqrt(vel[0] ** 2 + vel[1] ** 2), vel[1] / math.sqrt(vel[0] ** 2 + vel[1] ** 2)]
        except:
            vel = [0, 0]

        self.vel[0] += vel[0]
        self.vel[1] += vel[1]

        count = 0
        for bullet in game.BULLETS:
            if bullet.isPlayer:
                a = +bullet.vel[1]
                b = -bullet.vel[0]
                c = +bullet.vel[0] * bullet.pos[1] - bullet.vel[1] * bullet.pos[0]

                x = (b * (+b * self.pos[0] - a * self.pos[1]) - a * c) / (a ** 2 + b ** 2)
                y = (a * (-b * self.pos[0] + a * self.pos[1]) - b * c) / (a ** 2 + b ** 2)

                dist = distance(self.pos, [x, y])

                if dist < (self.radius + bullet.radius) * 1.5:
                    count += 1

                    vel = [x - self.pos[0], y - self.pos[1]]
                    try:
                        vel = [vel[0] / math.sqrt(vel[0] ** 2 + vel[1] ** 2),
                               vel[1] / math.sqrt(vel[0] ** 2 + vel[1] ** 2)]
                    except:
                        vel = [0, 0]

                    self.vel[0] += -vel[0] / count
                    self.vel[1] += -vel[1] / count


class Player(Object):
    SPEED = 4

    def __init__(self, lifetime, z_order):
        super().__init__(lifetime, z_order, {})

        self.pos = [SIZE[1] * 0.75, SIZE[1] / 2]

        self.radius = 10
        self.color = (0, 0, 0)

        self.vel = [0, 0]

        self.health = 0
        self.health_text = None
        self.update_health(2000)

        # Always counts down if above 0. Only shows hp above zero. Increase when taken damage to show hp
        self.show_hp = 100

        # Mouse can be locked to a certain position
        self.is_mouse_bound = False
        self.mouse_bind_pos = (300, 300)

    def render(self, screen, game):
        pygame.draw.circle(screen, self.color, self.pos, self.radius)
        if self.show_hp > 0:
            screen.blit(self.health_text, self.health_text.get_rect(center=(self.pos[0], self.pos[1] + self.radius*1.5)))

    def update_health(self, health):
        self.health = health
        self.health_text = get_arial_font(10).render(str(self.health), True, (200, 0, 0))

    def bind_mouse(self, pos):
        self.is_mouse_bound = True
        self.mouse_bind_pos = tuple(pos)

    def unbind_mouse(self):
        self.is_mouse_bound = False

    def take_damage(self, game, damage):
        self.update_health(self.health - damage)
        game.add_other(InflateSurface(200, 0, {}, get_damage_surface(damage), .5, 1.5, 50, copy.copy(self.pos), True, vel=(random.randint(-10, 10) / 10, -2)))
        self.show_hp = 100

    def update(self, screen, game):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

        if self.show_hp > 0:
            self.show_hp -= 1

        self.event_handle(screen, game)

        # Bind the mouse to a certain location
        if self.is_mouse_bound:
            pygame.mouse.set_pos(self.mouse_bind_pos)
            # Draws binding circles every 5 ticks (visual effect)
            if ticks % 15 == 0:
                game.add_other(BindCircle(self.mouse_bind_pos))

    def event_handle(self, screen, game):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Shooty shoot
                if event.button == pygame.BUTTON_LEFT:
                    y = event.pos[1] - self.pos[1]
                    x = event.pos[0] - self.pos[0]
                    h = math.sqrt(y ** 2 + x ** 2)
                    y = (y / h) * 5
                    x = (x / h) * 5

                    game.add_bullet(Bullet(copy.copy(self.pos), (x + self.vel[0]*.1, y + self.vel[1]*.1), True))
                # Slashy Slash
                elif event.button == pygame.BUTTON_RIGHT:
                    mouse_pos = pygame.mouse.get_pos()
                    y = mouse_pos[1] - self.pos[1]
                    x = mouse_pos[0] - self.pos[0]
                    h = math.sqrt(y ** 2 + x ** 2)
                    y = (y / h) * 20
                    x = (x / h) * 20
                    game.add_slash(Slash(True, (100, 100, 0), [self.pos[0] + x, self.pos[1] + y]))

        # ASWD Movement
        self.vel = [(-self.SPEED if pygame.key.get_pressed()[pygame.K_a] else 0) + (self.SPEED if pygame.key.get_pressed()[pygame.K_d] else 0),
                    (self.SPEED if pygame.key.get_pressed()[pygame.K_s] else 0) + (-self.SPEED if pygame.key.get_pressed()[pygame.K_w] else 0)]


class Bullet(Object):
    def __init__(self, pos, vel, isPlayerBullet):
        super().__init__(150, 0, {})

        self.isPlayer = isPlayerBullet

        self.pos = list(pos)
        self.radius = 3
        self.color_bs = (150, 0, 0)
        self.color_pl = (200, 200, 0)

        self.vel = list(vel)

    def update(self, screen, game):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

        # Collision Logic
        if self.isPlayer:
            if distance(self.pos, game.BOSS.pos) <= game.BOSS.radius + self.radius:
                game.BOSS.take_damage(game, random.randint(20, 55))
                game.delete_bullet(self)
        else:
            if distance(self.pos, game.PLY.pos) <= game.PLY.radius + self.radius:
                game.PLY.take_damage(game, random.randint(5, 35))
                game.delete_bullet(self)

    def render(self, screen, game):
        pygame.draw.circle(screen, self.color_pl if self.isPlayer else self.color_bs, self.pos, self.radius)


class InflateSurface(Object):
    def __init__(self, lifetime, z_order, tags, surface, start_scale, stop_scale, scale_time, pos, fade=False,
                 initial_opacity=255, delay_inflation=0, vel=(0, 0), angle_vel=0.0):
        super().__init__(lifetime, z_order, tags)

        self.surface_rect = surface.get_rect()

        self.pos = list(pos)
        self.vel = vel

        self.angle = 0
        self.angle_vel = angle_vel

        self.start_scale = (self.surface_rect.w * start_scale, self.surface_rect.h * start_scale)
        self.stop_scale = (self.surface_rect.w * stop_scale, self.surface_rect.h * stop_scale)
        self.scale_time = scale_time
        self.current_scale = list(copy.copy(self.start_scale))
        self.scale_increment = ((self.stop_scale[0] - self.start_scale[0]) / self.scale_time,
                                (self.stop_scale[1] - self.start_scale[1]) / self.scale_time)

        self.surface = pygame.Surface(self.surface_rect.size, pygame.SRCALPHA, 32).convert_alpha()
        self.surface.blit(surface, (0, 0))

        self.opacity = initial_opacity
        self.fade_increment = (self.opacity + 1) / self.scale_time
        self.fade = fade

        # Delays inflation for a given amount of time
        self.delay_inflation = delay_inflation

    def update(self, screen, game):
        if self.delay_inflation == 0:
            if self.current_scale[0] < self.stop_scale[0]:
                self.current_scale[0] += self.scale_increment[0]
                self.current_scale[1] += self.scale_increment[1]
            if self.fade:
                self.opacity -= self.fade_increment
            if self.angle_vel:
                self.angle += self.angle_vel
            self.pos[0] += self.vel[0]
            self.pos[1] += self.vel[1]

            self.more_logic(screen, game)
        else:
            self.delay_inflation -= 1

    def more_logic(self, screen, game):
        pass

    def render(self, screen, game):
        if self.opacity > 0:
            new_surf = pygame.transform.scale(self.surface, [int(x) for x in self.current_scale]).convert_alpha()

            if self.angle_vel:
                new_surf = pygame.transform.rotate(new_surf, self.angle).convert_alpha()

            rect = new_surf.get_rect()
            rect.center = self.pos

            if self.fade:
                new_surf.fill((255, 255, 255, self.opacity if self.opacity >= 0 else 0), None, pygame.BLEND_RGBA_MULT)

            screen.blit(new_surf, rect)


class Slash(InflateSurface):
    def __init__(self, isPlayerSlash, color, pos):
        surf = pygame.Surface((160, 160), pygame.SRCALPHA, 32).convert_alpha()
        pygame.draw.circle(surf, color, (80, 80), 80)

        super().__init__(200, 5, {}, surf, .01, 1, 30, pos, True)

        self.isPlayer = isPlayerSlash

        self.has_hit = False

    def more_logic(self, screen, game):
        # Collision logic
        if not self.has_hit:
            if self.isPlayer:
                if distance(self.pos, game.BOSS.pos) <= game.BOSS.radius + self.surface_rect.width / 3:
                    game.BOSS.take_damage(game, random.randint(25, 80))
                    self.has_hit = True
            else:
                if distance(self.pos, game.PLY.pos) <= game.PLY.radius + self.surface_rect.width / 3:
                    game.PLY.take_damage(game, random.randint(5, 80))
                    self.has_hit = True


class BindCircle(InflateSurface):
    def __init__(self, pos):
        surf = pygame.Surface((50, 50), pygame.SRCALPHA, 32).convert_alpha()
        pygame.draw.circle(surf, (0, 0, 255), (25, 25), 25, 2)

        super().__init__(100, 5, {}, surf, .6, 1.2, 28, pos, True, initial_opacity=150)


class Laser(InflateSurface):
    def __init__(self, start, end):
        size = abs(end[0] - start[0]), abs(end[1] - start[1])
        surf = pygame.Surface(size, pygame.SRCALPHA, 32)
        new_start = [0, 0]
        new_end = [0, 0]

        if end[1] > start[1]:
            new_end[1] = size[1]
            new_start[1] = 0
        else:
            new_end[1] = 0
            new_start[1] = size[1]

        if end[0] > start[0]:
            new_end[0] = size[0]
            new_start[0] = 0
        else:
            new_end[0] = 0
            new_start[0] = size[0]

        pygame.draw.line(surf, (255, 0, 0), new_start, new_end, 5)
        surf = surf.convert_alpha()

        super().__init__(100, -1, {}, surf, 1, 1, 50, (start[0] + (end[0] - start[0]) / 2, start[1] + (end[1] - start[1]) / 2), fade=True)


# Cuts the given surface in half and returns 2 flying inflating surfaces for the halves
def fragmentate(surf, center):
    height = surf.get_height()
    width = surf.get_width() / 2

    pos1 = center[0] - width / 2, center[1]
    pos2 = center[0] + width / 2, center[1]

    surface1 = pygame.Surface((width, height), pygame.SRCALPHA, 32)
    surface1.blit(surf, (0, 0))
    surface1 = surface1.convert_alpha()

    surface2 = pygame.Surface((width, height), pygame.SRCALPHA, 32)
    surface2.blit(surf, (-width, 0))
    surface2 = surface2.convert_alpha()

    return (InflateSurface(150, -1, {}, surface1, 1, 1.2, 100, pos1, fade=True, angle_vel=(random.randint(-30, 30) / 10)),
            InflateSurface(150, -1, {}, surface2, 1, 1.2, 100, pos2, fade=True, angle_vel=(random.randint(-30, 30) / 10)))


def distance(p, q):
    return math.sqrt((q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2)


def get_arial_font(size):
    return pygame.font.SysFont("Arial", size, False)


def get_arial_font_bold(size):
    return pygame.font.SysFont("Arial", size, True)


def get_damage_surface(damage):
    return get_arial_font_bold(int(20 + damage / 30)).render(str(damage), True, (255, 0, 0))


fps = 0
last_fps_show = 0
clock = pygame.time.Clock()

SIZE = (600, 600)
screen = pygame.display.set_mode(SIZE)

GAME = Game()

running = True
events = []

ticks = 0

set_4th_wall = False
def set_4th_wall_toggle(bool):
    global set_4th_wall
    set_4th_wall = bool

while running:
    screen.fill((255, 255, 255))

    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    GAME.run_game(screen)

    pygame.display.update()

    ticks += 1

    if GAME.RESET_GAME:
        GAME = Game(set_4th_wall)
        if set_4th_wall:
            set_4th_wall = False

    # sets fps to a variable. can be set to caption any time for testing.
    last_fps_show += 1
    if last_fps_show == 30:  # every 30th frame:
        fps = clock.get_fps()
        pygame.display.set_caption("FPS: " + str(fps))
        last_fps_show = 0

    # fps max 60
    clock.tick(60)
