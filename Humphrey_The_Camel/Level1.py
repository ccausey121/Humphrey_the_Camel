def WORLD1GAME():
    import arcade
    import glob
    import math
    import sys

# --------------------------
# SCREEN CONSTANTS
# --------------------------
    SCREEN_WIDTH = 1200
    SCREEN_HEIGHT = 500
    SCREEN_TITLE = "Humphrey the Camel"

# --------------------------
# GAMEPLAY CONSTANTS
# --------------------------
    TILE_SCALING = 0.5
    COIN_SCALING = 0.5

# --------------------------
# PHYSICS CONSTANTS
# --------------------------
    PLAYER_MOVEMENT_SPEED = 5
    GRAVITY = 1
    PLAYER_JUMP_SPEED = 20

# --------------------------
# SPIT CONSTANTS
# --------------------------
    SPIT_MOVE_FORCE = 4500
    SPIT_MASS = 0.1
    SPIT_GRAVITY = 1


# ==============================================================
# PLAYER CLASS
# ==============================================================
    class PlayerCharacter(arcade.Sprite):
        def __init__(self):
            super().__init__()
            self.physics_engine = None
            self.scale = TILE_SCALING
        # Face Direction
            # 0 = facing right, 1 = facing left
            self.character_face_direction = 0
            self.is_on_ground = False
        
        # Animations
            self.cur_texture = 0
            self.walk_textures = []
            self.jump_textures = []

            main_path = "humphrey"

        # IDLE textures
            self.idle_texture_pair = (
                arcade.load_texture(f"{main_path}_sprite(1).png"),
                arcade.load_texture(f"{main_path}_sprite(1).png").flip_left_right()
                # flip_left_right() creates the mirrored texture
            )

        # WALK textures (glob finds multiple frames)
            for texture_path in sorted(glob.glob(f"{main_path}_sprite(*).png")):
                tex = arcade.load_texture(texture_path)
                tex_m = tex.flip_left_right()
                self.walk_textures.append((tex, tex_m))

        # Jump textures
            for texture_path in sorted(glob.glob(f"{main_path}_jump(*).png")):
                tex = arcade.load_texture(texture_path)
                tex_m = tex.flip_left_right()
                self.jump_textures.append((tex, tex_m))

        # Initial texture
            self.texture = self.idle_texture_pair[0]

        def update_animation(self, delta_time: float = 1/60):
        # Detect DIRECTION
            if self.change_x < 0:
                self.character_face_direction = 1
            elif self.change_x > 0:
                self.character_face_direction = 0

        # AIR animations
            is_on_ground = self.physics_engine and self.physics_engine.can_jump()

            if not is_on_ground:
                frame = (self.cur_texture // 5) % len(self.jump_textures)
                self.texture = self.jump_textures[frame][self.character_face_direction]
                self.cur_texture += 1
                return

        # Idle animation
            if self.change_x == 0:
                self.texture = self.idle_texture_pair[self.character_face_direction]
                return

        # Walking animation
            self.cur_texture += 1
            if self.cur_texture >= len(self.walk_textures) * 5:
                self.cur_texture = 0

            frame = self.cur_texture // 5
            self.texture = self.walk_textures[frame][self.character_face_direction]


# ==============================================================
# SPIT CLASS
# ==============================================================
    class SpitSprite(arcade.SpriteSolidColor):
        def update(self, delta_time=1/60):
        # Apply MOVEMENT for SPIT
            self.center_x += self.change_x
            self.center_y += self.change_y

        # World BOUNDARIES for SPIT (removes spit when too far)
            WORLD_LEFT, WORLD_RIGHT = -200, 3200
            WORLD_BOTTOM, WORLD_TOP = -200, SCREEN_HEIGHT + 200

            if (self.center_x < WORLD_LEFT or
                self.center_x > WORLD_RIGHT or
                self.center_y < WORLD_BOTTOM or
                self.center_y > WORLD_TOP):
                self.remove_from_sprite_lists()


# ==============================================================
# ENEMY CLASS
# ==============================================================
    class Enemy(arcade.Sprite):
        def __init__(self, x1, x2, y, speed=2):
            super().__init__("samaltmansprite.png", 0.8)  # Use any sprite that you have
            self.left_limit = x1
            self.right_limit = x2
            self.center_x = x1
            self.center_y = y
            self.speed = speed
            self.change_x = speed  # start moving RIGHT

        def update_enemy(self, physics_engine, platforms):
            """Move enemy, check wall collisions, reverse direction."""
        # Move enemy
            self.center_x += self.change_x
    
        # Check collisions with walls
            hit_list = arcade.check_for_collision_with_list(self, platforms)
    
            if len(hit_list) > 0:
            # Reverse movement
                self.change_x *= -1
    
            # Move enemy back out of collision
                self.center_x += self.change_x * 2

    
# ==============================================================
# MAIN GAME CLASS
# ==============================================================
    class MyGame(arcade.Window):
        def __init__(self):
        # Setting up EMPTY WINDOW
            super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        
        # Scene = container for sprites
            self.scene = None
            self.tile_map = None
            self.player_sprite = None
            self.physics_engine = None

        # Spit projectiles
            self.spit_list = None

            self.collected_coins = 0
            self.total_coins = 0
        
            self.enemies_killed = 0
            self.total_enemies = 0

        
        # Keys
            self.moving_key_pressed = False

        # Cameras
            self.camera = arcade.Camera2D()
            self.gui_camera = arcade.Camera2D()

            self.text_outline = (7, 24, 33)
            self.text_fill = (224, 248, 207)
            self.text_size = 24
            self.text_font = ('Bauhaus 93', 'Sans Serif Collection')
        
        # Scoring, timer, lives
            self.score = 0
            self.lives = 3
        
        # Lives GUI
            self.life_sprites = arcade.SpriteList()

        # Background color
            self.background_color = (224,248,207)

        # Sounds
            self.collect_coin_sound = arcade.load_sound("SonicRings.wav")
            self.jump_sound = arcade.load_sound("SonicJump.wav")
            self.enemy_die = arcade.load_sound("SonicEnemyDie.wav")
            self.player_die = arcade.load_sound("SonicDies.wav")
            self.spit_sound = arcade.load_sound("SonicSpit.wav")
            self.bgm_player = None

        def draw_outlined_text(self, text, x, y, size=None):
            size = size or self.text_size
        # Outline
            arcade.draw_text(text, x - 2, y, self.text_outline, size, font_name=self.text_font)
            arcade.draw_text(text, x + 2, y, self.text_outline, size, font_name=self.text_font)
            arcade.draw_text(text, x, y - 2, self.text_outline, size, font_name=self.text_font)
            arcade.draw_text(text, x, y + 2, self.text_outline, size, font_name=self.text_font)
        # Fill
            arcade.draw_text(text, x, y, self.text_fill, size, font_name=self.text_font)


    # ----------------------------------------------------------
    # SETUP
    # ----------------------------------------------------------
        def setup(self):
            if hasattr(self, "bgm_player") and self.bgm_player:
                arcade.stop_sound(self.bgm_player)

            map_name = "world1_map_last.tmx"
        
            layer_options = {
                "ground": {"use_spatial_hash": True},
                "platforms": {"use_spatial_hash": True},
                "end": {"use_spatial_hash": True},
            }

            self.tile_map = arcade.load_tilemap(
                map_name,
                scaling=TILE_SCALING+1.7,
                layer_options=layer_options
            )
        
            self.scene = arcade.Scene.from_tilemap(self.tile_map)

        
            end_layer = self.scene["end"]
            self.scene.add_sprite_list("EndArea", use_spatial_hash=True)
            for tile in end_layer:
                invis = arcade.Sprite()
                invis.width = tile.width
                invis.height = tile.height
                invis.center_x = tile.center_x
                invis.center_y = tile.center_y
                invis.visible = False
                self.scene["EndArea"].append(invis)

        
        # Create PLAYER
            self.player_sprite = PlayerCharacter()
            self.player_sprite.center_x = 128
            self.player_sprite.center_y = 128
            self.scene.add_sprite("Player", self.player_sprite)

            collision_sprites = arcade.SpriteList()
            if hasattr(self.tile_map, "sprite_lists"):
                for name in ("ground", "platforms"):
                    if name in self.tile_map.sprite_lists:
                        for sprite in self.tile_map.sprite_lists[name]:
                            collision_sprites.append(sprite)
        # Set up for SPIT
            self.spit_list = arcade.SpriteList()

        # Add COINS
            coinX = [97,224,256,289,320,416,512,592,625,689,721,753,783,832,863,945,960,993,992,1073,1102,1151,1231]
            coinY = [145,113,113,48,48,81,96,65,65,194,95,32,32,81,81,65,65,65,194,112,112,48,192]
            for a in range(len(coinX)):
                coin = arcade.Sprite("shrubGrass.png", COIN_SCALING)
                coin.center_x = (coinX[a] * 2.20) + 16.6
                coin.center_y = (coinY[a] * (-2)) + 495
                self.scene.add_sprite("Coins", coin)
        
        # Two enemies patrolling between box areas
            enemyX1 = [560,753,944,1057]
            enemyX2 = [703,911,1008,1152]
            enemyY = [192,192,192,192]

        # ENEMY List
            self.enemy_list = arcade.SpriteList()
            self.scene.add_sprite_list("Enemies", self.enemy_list)
        
            for a in range(len(enemyX1)):
                enemyGlobX1 = (enemyX1[a] * 2.20) + 16.6
                enemyGlobY = (enemyY[a] * (-2)) + 495
                enemyGlobX2 = (enemyX2[a] * 2.20) + 16.6

                enemy = Enemy(x1=enemyGlobX1,x2=enemyGlobX2,y=enemyGlobY,speed=(1.3*a+1))

                self.scene.add_sprite("Enemies", enemy)

            self.total_coins = len(self.scene["Coins"])
            self.total_enemies = len(self.scene["Enemies"])

        
        # Create PHYSICS ENGINE
            self.physics_engine = arcade.PhysicsEnginePlatformer(
                self.player_sprite, gravity_constant=GRAVITY, platforms=collision_sprites,
            )
       
            self.player_sprite.physics_engine = self.physics_engine

            self.enemy_physics_engines = []
            for enemy in self.scene["Enemies"]:
                engine = arcade.PhysicsEnginePlatformer(
                    enemy,
                    gravity_constant=GRAVITY,
                    platforms=collision_sprites
                )
                self.enemy_physics_engines.append(engine)


        # Initialize our CAMERA, setting a VIEWPORT the size of our window.
            self.camera = arcade.Camera2D()

        # Initialize our GUI CAMERA, initial settings are the same as our CAMERA.
            self.gui_camera = arcade.Camera2D()
        
        # Reset score and timer
            self.score = 0

            self.time_elapsed = 0.0

        # Score Text
            self.score_text = arcade.Text(
                f"Score: {self.score}",
                x=15, y=SCREEN_HEIGHT-40,
                color=[98, 129, 65],
                font_size=30,
                align="left",
                font_name=('Bauhaus 93', 'Sans Serif Collection')
            )

        # Time Text
            self.time_text = arcade.Text(
                f"Time: {self.time_elapsed}",
                x=15, y=SCREEN_HEIGHT-70,
                color=[98, 129, 65],
                font_size=30,
                align="left",
                font_name=('Bauhaus 93', 'Sans Serif Collection')
            )

        # Life Text + Icon
            self.life_sprites = arcade.SpriteList()
            icon = arcade.Sprite("iconHumphrey.png", scale=0.5)
            icon.center_x = 40
            icon.center_y = 40
            self.life_sprites.append(icon)
    

            self.life_text = arcade.Text(
                f"x {self.lives}",
                x=70, y=25,
                color=[98, 129, 65],
                font_size=24,
                align="left",
                font_name=('Bauhaus 93', 'Sans Serif Collection')
            )

        # Boundary for END OF LEVEL
            self.end_of_map = SCREEN_WIDTH + 2000

            self.bgm = arcade.Sound("HTC WORLD 1.wav", streaming=True)
            self.bgm_player = self.bgm.play(volume=1, loop=True)

    # ----------------------------------------------------------
    # DRAW
    # ----------------------------------------------------------
        def on_draw(self):
            self.clear()

        # Use game camera
            self.camera.use()

        # Draw scene + spit
            self.scene.draw()
            self.spit_list.draw()

        # Draw GUI text
            self.gui_camera.use()
        
        # Score
            self.draw_outlined_text(f"Score: {self.score}", 15, SCREEN_HEIGHT - 40, size=30)
        
        # Time
            self.draw_outlined_text(f"Time: {'{:.2f}'.format(self.time_elapsed)}", 15, SCREEN_HEIGHT - 70, size=30)
        
        # Lives
            self.life_sprites.draw()
            self.draw_outlined_text(f"x {self.lives}", 70, 25)
    # ----------------------------------------------------------
    # KEY PRESSES
    # ----------------------------------------------------------
        def on_key_press(self, key, modifiers):
            if key in (arcade.key.UP, arcade.key.LEFT, arcade.key.RIGHT):
                self.moving_key_pressed = True

            if key == arcade.key.UP:
            # JUMP if allowed
                if self.physics_engine.can_jump():
                    self.player_sprite.change_y = PLAYER_JUMP_SPEED
                    arcade.play_sound(self.jump_sound)

            elif key == arcade.key.LEFT:
                self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED

            elif key == arcade.key.RIGHT:
                self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED

            elif key == arcade.key.SPACE:
                arcade.play_sound(self.spit_sound, volume=0.4)
            
            # Create NEW SPIT
                spit = SpitSprite(width=5, height=5, color=(7,24,33))
                self.spit_list.append(spit)

            # SPAWN SPIT at player center
                spit.center_x = self.player_sprite.center_x
                spit.center_y = self.player_sprite.center_y

            # DIRECTION of SPIT
                if self.player_sprite.character_face_direction == 0:
                    angle = 0  # Right
                else:
                    angle = math.pi  # Left

                spit.angle = math.degrees(angle)

            # Movement vector
                spit.change_x = math.cos(angle) * 15
                spit.change_y = math.sin(angle) * 15


    # ----------------------------------------------------------
    # KEY RELEASES
    # ----------------------------------------------------------
        def on_key_release(self, key, modifiers):
            if key in (arcade.key.LEFT, arcade.key.RIGHT):
                self.player_sprite.change_x = 0

            self.moving_key_pressed = False


    # ----------------------------------------------------------
    # ON UPDATE
    # ----------------------------------------------------------
        def on_update(self, delta_time):
        # Update PLAYER Physics
            self.physics_engine.update()
        
        # Update PLAYER animations
            self.scene.update_animation(delta_time, ["Player"])
    
            platforms = self.scene["platforms"]
            for enemy, engine in zip(self.scene["Enemies"], self.enemy_physics_engines):
                engine.update()
                enemy.update_enemy(engine, platforms)
    
            self.player_sprite.is_on_ground = self.physics_engine.can_jump()
        
        # --------------------------
        # PLAYER - ENEMY Collisions
        # --------------------------
            enemy_hit_list = arcade.check_for_collision_with_list(
                self.player_sprite, self.scene["Enemies"]
            )
    
            if enemy_hit_list:
                for enemy in enemy_hit_list:
                    if not self.player_sprite.is_on_ground and self.player_sprite.change_y < 0:
                    # Hit from above
                        arcade.play_sound(self.enemy_die)
                        self.player_sprite.change_y = PLAYER_JUMP_SPEED * 1.5
                        enemy.remove_from_sprite_lists()
                        self.enemies_killed += 1
                    # Add POINTS
                        self.score += 200
                        self.score_text.text = f"Score: {self.score}"
                    else:
                    # Reset level
                        arcade.play_sound(self.player_die,volume=0.5)
                        self.lives -= 1
                        if self.lives <= 0:
                            if self.bgm_player:
                                arcade.stop_sound(self.bgm_player)

                            arcade.exit()
                            #self.close()        # Cierra la ventana limpiamente
                            #sys.exit(0)          #Mata el programa completo SIN error
                    
                    # Save Lives
                        previous_lives = self.lives

                        if self.bgm_player:
                            arcade.stop_sound(self.bgm_player)
                        self.setup()
    
                    # Restore Lives
                        self.lives = previous_lives
                        self.life_text.text = f"x {self.lives}"
                        self.score_text.text = f"Score: {self.score}"
                    
                    # Player INITIAL POSITION
                        self.player_sprite.center_x = 128
                        self.player_sprite.center_y = 128
                        self.player_sprite.change_x = 0
                        self.player_sprite.change_y = 0
                        return
    
        # --------------------------
        # PLAYER - COINS Collisions
        # --------------------------
            coin_list = arcade.check_for_collision_with_list(
                self.player_sprite, self.scene["Coins"]
            )
    
            for coin in coin_list:
                coin.remove_from_sprite_lists()
                arcade.play_sound(self.collect_coin_sound, volume=0.4)
                self.score += 100
                self.collected_coins += 1
                self.score_text.text = f"Score: {self.score}"
    


            end_collisions = arcade.check_for_collision_with_list(
                self.player_sprite,
                self.scene["EndArea"]
            )
            
            if end_collisions:
                self.finish_level()


        # --------------------------
        # Smooth Camera
        # --------------------------
            CAMERA_MAX_X = 3100 - SCREEN_WIDTH / 2
            target_x = self.player_sprite.center_x
            target_y = self.player_sprite.center_y - 100
    
            min_x = SCREEN_WIDTH / 2
            min_y = SCREEN_HEIGHT / 2
    
            if target_x < min_x:
                target_x = min_x
    
            if target_y < min_y:
                target_y = min_y

            if target_x > CAMERA_MAX_X:
                target_x = CAMERA_MAX_X
        
            smooth = 0.1
            self.camera.position = (
                self.camera.position[0] + (target_x - self.camera.position[0]) * smooth,
                self.camera.position[1] + (target_y - self.camera.position[1]) * smooth
            )

        # --------------------------
        # Update SPIT
        # --------------------------
            self.spit_list.update()

        # --------------------------
        # SPIT - ENEMY collisions
        # --------------------------
            for spit in self.spit_list:
                hit_enemies = arcade.check_for_collision_with_list(spit, self.scene["Enemies"])
                for enemy in hit_enemies:
                    arcade.play_sound(self.enemy_die)
                    enemy.remove_from_sprite_lists()
                    spit.remove_from_sprite_lists()
                    self.enemies_killed += 1
                    self.score += 200
                    self.score_text.text = f"Score: {self.score}"
    
        # --------------------------
        # Timer
        # --------------------------
            self.time_elapsed += delta_time
            self.time_text.text = f"Time: {'{:.2f}'.format(self.time_elapsed)}"
    
        # --------------------------
        # Screen Boundaries
        # --------------------------
            if self.player_sprite.left < 0:
                self.player_sprite.left = 0
            if self.player_sprite.right > 3100:
                self.player_sprite.right = 3100
            if self.player_sprite.bottom < 0:
                arcade.play_sound(self.player_die)
                self.lives -= 1
                if self.lives <= 0:
                    if self.bgm_player:
                        arcade.stop_sound(self.bgm_player)

                    arcade.exit()
                    #self.close() # Cierra la ventana limpiamente
                    
                    #sys.exit()          # Mata el programa completo SIN error
                    
            # Save Lives
                previous_lives = self.lives

                if self.bgm_player:
                    arcade.stop_sound(self.bgm_player)
                self.setup()
    
            # Restore Lives
                self.lives = previous_lives
                self.life_text.text = f"x {self.lives}"
                self.score_text.text = f"Score: {self.score}"
                    
            # Player INITIAL POSITION
                self.player_sprite.center_x = 128
                self.player_sprite.center_y = 128
                self.player_sprite.change_x = 0
                self.player_sprite.change_y = 0
                return


        def on_close(self):
            if self.bgm_player:
                arcade.stop_sound(self.bgm_player)
            super().on_close()

        def finish_level(self):
    
            if self.bgm_player:
                arcade.stop_sound(self.bgm_player)
            arcade.exit()
            #self.close()
            
            #sys.exit()
    
# ==============================================================
# MAIN
# ==============================================================
    def main_level1():
        window = MyGame()
        window.setup()
        arcade.run()
        

    main_level1()
