from panda3d.core import NodePath, CollisionNode, CollisionSphere, CollisionTraverser, CollisionHandlerQueue, CollisionRay, TextNode, DirectionalLight, AmbientLight
from panda3d.core import AntialiasAttrib, ClockObject, Material, Point3, LineSegs
from panda3d.core import loadPrcFile
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectEntry, DGG, DirectOptionMenu, DirectButton
import hashlib
import json
import os

from camera import Camera

globalClock = ClockObject.getGlobalClock()

# Load configuration file
loadPrcFile("config/conf.prc")

class GridDemo(ShowBase):
    def __init__(self, size):
        super().__init__()
        
        # ========================================== #
        # 1. ENGINE & GRAPHICS SETUP                 #
        # ========================================== #
        self.render.setAntialias(AntialiasAttrib.MLine)
        self.custom_font = self.loader.loadFont("fonts/Montserrat-Regular.ttf")
        self.background_color = (0.5, 0.5, 0.5)
        self.setBackgroundColor(self.background_color)
        
        self.myMaterial = Material()
        self.myMaterial.setShininess(16)
        self.myMaterial.setSpecular((0.25, 0.25, 0.25, 1))
        
        dlight = DirectionalLight('dlight')
        dlight.setColor((1, 1, 1, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(-45, -45, -45)
        self.render.setLight(dlnp)
        
        alight = AmbientLight('alight')
        alight.setColor((0.2, 0.2, 0.2, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)

        self.ball_model = self.loader.loadModel("models/sphere.bam")
        self.black_texture = self.loader.loadTexture("textures/black.png")
        self.white_texture = self.loader.loadTexture("textures/white.png")

        # ========================================== #
        # 2. GAME STATE & GRID VARIABLES             #
        # ========================================== #
        self.initial_size = size
        self.size = "0,0,0"
        self.x_size = 1
        self.y_size = 1
        self.z_size = 1
        
        self.black_points = 0
        self.white_points = 0
        self.black_captures = 0
        self.white_captures = 0
        self.komi = 0.5
        
        self.current_color = 0  # 0 = black, 1 = white
        self.turn = 1
        self.pass_count = 0  
        self.game_ended = False
        self.match_history = []
        
        self.nodes = []
        self.line_nodes = []
        self.balls = {}
        
        self.last_plane_action = None
        self.current_plane = -1
        self.layer_count = 0
        self.grid_color = (1, 1, 1)

        # ========================================== #
        # 3. TIMER VARIABLES                         #
        # ========================================== #
        self.timer_running = False
        self.timer_task = None
        self.timer_mode = "No Timer"
        
        self.main_time = 0
        self.increment = 0
        self.byo_periods = 5
        self.byo_time = 30
        
        self.black_time = self.main_time
        self.white_time = self.main_time
        self.black_byo_periods_left = self.byo_periods
        self.white_byo_periods_left = self.byo_periods
        self.black_byo_yomi_time = self.byo_time
        self.white_byo_yomi_time = self.byo_time
        self.black_byo_yomi_periods = self.byo_periods
        self.white_byo_yomi_periods = self.byo_periods

        # ========================================== #
        # 4. INITIALIZATION ROUTINES                 #
        # ========================================== #
        self.camera_control = Camera(self, self.initial_size)
        self.setup_collision_system()
        self.disableMouse()
        self.bind_inputs()
        
        self.extra_gui_elements = {}
        self.help_show = 0
        self.extra_show = 0
        
        self.setup_gui()
        self.game_over_text = OnscreenText(
            text="To start, select a grid size and press enter.",
            pos=(0, 0), scale=0.1, fg=(0, 0, 0, 1), align=TextNode.ACenter, font=self.custom_font
        )

    # ========================================== #
    # SAVE, LOAD & RESET                         #
    # ========================================== #
    def save_game(self):
        if self.turn == 1:
            return
        if not os.path.exists("./save"):
            os.makedirs("./save")
            
        serializable_history = []
        for state in self.match_history:
            serializable_balls = {f"{k[0]},{k[1]},{k[2]}": v for k, v in state['balls'].items()}
            serializable_history.append({
                'balls': serializable_balls,
                'current_color': state['current_color'],
                'turn': state['turn'],
                'black_captures': state['black_captures'],
                'white_captures': state['white_captures'],
                'board_hash': state['board_hash']
            })
            
        payload = {
            'size_str': self.size,
            'match_history': serializable_history
        }
        with open("./save/savegame.json", "w") as f:
            json.dump(payload, f, indent=4)
            
    def load_game(self):
        path = "./save/savegame.json"
        if not os.path.exists(path):
            print("No save file found.")
            return
        try:
            with open(path, "r") as f:
                payload = json.load(f)
                
            self.size = payload['size_str']
            self.reset_game()
            self.generate_grid(self.size)
            
            self.match_history = []
            for state in payload['match_history']:
                deserialized_balls = {}
                for k_str, v in state['balls'].items():
                    coords = tuple(int(c) for c in k_str.split(','))
                    deserialized_balls[coords] = v
                self.match_history.append({
                    'balls': deserialized_balls,
                    'current_color': state['current_color'],
                    'turn': state['turn'],
                    'black_captures': state['black_captures'],
                    'white_captures': state['white_captures'],
                    'board_hash': state['board_hash']
                })
                
            if self.match_history:
                last_state = self.match_history[-1]
                for pos in list(self.balls.keys()):
                    self.balls[pos]['node'].removeNode()
                self.balls.clear()
                
                for pos, ball_data in last_state['balls'].items():
                    model = self.ball_model.copyTo(self.render)
                    model.setTexture(self.black_texture if ball_data['color'] == 0 else self.white_texture, 1)
                    model.setScale(0.49)
                    model.setPos(pos[0], pos[1], pos[2])
                    model.setMaterial(self.myMaterial)
                    self.balls[pos] = {'node': model, 'color': ball_data['color']}
                    
                self.current_color = last_state['current_color']
                self.turn = last_state['turn']
                self.black_captures = last_state['black_captures']
                self.white_captures = last_state['white_captures']
                
                self.turn_text.setText(f"Turn: {self.turn}")
                self.text_captures.setText(f"Black captures: {self.black_captures}\nWhite captures: {self.white_captures}")
                self.points()
                print("Match loaded successfully.")
        except Exception as e:
            print(f"Error loading game data: {e}")

    def reset_game(self):
        self.game_ended = False
        self.pass_count = 0
        self.white_points = 0
        self.black_points = 0
        self.black_captures = 0
        self.white_captures = 0
        self.current_color = 0
        self.turn = 1
        self.layer_count = 0
        self.match_history = []
        
        for ball_data in list(self.balls.values()):
            ball_data['node'].removeNode()
        self.balls.clear()
        
        self.pause_timer()
        self.show_everything()
        
        if hasattr(self, 'turn_text'):
            self.turn_text.setText(f"Turn: {self.turn}")
        if hasattr(self, 'text_captures'):
            self.text_captures.setText(f"Black captures: {self.black_captures}\nWhite captures: {self.white_captures}")
        if hasattr(self, 'text_points'):
            self.text_points.setText(f"Black: {self.black_points} pts\nWhite: {self.white_points} pts")

    # ========================================== #
    # GRID & RENDERING                           #
    # ========================================== #
    def generate_grid(self, size):
        try:
            parts = [int(x.strip()) for x in size.split(',')]
            self.x_size, self.y_size, self.z_size = parts

            # Clear old elements safely
            for ball_data in list(self.balls.values()):
                ball_data['node'].removeNode()
            self.balls.clear()

            for node in self.nodes:
                if not node.is_empty():
                    collision_node = node.find("**/+CollisionNode")
                    if collision_node:
                        collision_node.removeNode()
                    node.removeNode()

            for line_node in self.line_nodes:
                line_node.removeNode()
            self.line_nodes = []
            self.nodes = []

            # Generate vertices & nodes
            for x in range(self.x_size):
                for y in range(self.y_size):
                    for z in range(self.z_size):
                        vertex_node = NodePath(f"vertex_{x},{y},{z}")
                        vertex_node.setPos(x, y, z)
                        vertex_node.reparentTo(self.render)
                        collision_sphere = CollisionSphere(0, 0, 0, 0.25)
                        collision_node = vertex_node.attachNewNode(CollisionNode(f'cnode_{x}{y}{z}'))
                        collision_node.node().addSolid(collision_sphere)
                        collision_node.node().setIntoCollideMask(1)
                        collision_node.setColor(0.5, 0.5, 0.5, 1)
                        self.nodes.append(vertex_node)

            # Generate Grid Lines
            for z in range(self.z_size):
                lines = LineSegs()
                lines.setThickness(1)
                lines.setColor(1, 1, 1, 1)
                for y in range(self.y_size):
                    lines.moveTo(0, y, z)
                    lines.drawTo(self.x_size - 1, y, z)
                for x in range(self.x_size):
                    lines.moveTo(x, 0, z)
                    lines.drawTo(x, self.y_size - 1, z)
                line_node = self.render.attachNewNode(lines.create())
                self.line_nodes.append(line_node)

            self.game_over_text.destroy()  
            self.reset_camera(self.size)
            self.place_initial_ball()
            self.custom_grid_color(self.grid_color)
        except Exception as e:
            print(f"Error during grid generation: {e}")
            return

    def place_initial_ball(self): 
        initial_ball = self.loader.loadModel("smiley")
        initial_ball.setPos(0, 0, 0)
        initial_ball.setTexture(self.loader.loadTexture("textures/blue.png"), 1)
        initial_ball.setScale(0.05)
        initial_ball.reparentTo(self.render)

    def custom_background_color(self, event=None):
        if self.extra_show == 1 and "background_entry" in self.extra_gui_elements:
            text = self.extra_gui_elements["background_entry"].get()
        else:
            if isinstance(event, tuple) and len(event) == 3:
                text = ','.join(str(int(c * 255)) for c in event)
            else:
                text = ','.join(str(int(c * 255)) for c in self.background_color)
        try:
            color = [int(x.strip()) for x in text.split(',')]
            if len(color) != 3: return
            r, g, b = [c / 255.0 for c in color]
            if not all(0 <= c <= 1 for c in (r, g, b)): return
            self.setBackgroundColor(r, g, b)
            self.background_color = (r, g, b)
        except ValueError:
            return

    def custom_grid_color(self, event=None):
        if self.extra_show == 1 and "color_entry" in self.extra_gui_elements:
            text = self.extra_gui_elements["color_entry"].get()
        else:
            if isinstance(event, tuple) and len(event) == 3:
                text = ','.join(str(int(c * 255)) for c in event)
            else:
                text = ','.join(str(int(c * 255)) for c in self.grid_color)
        try:
            color = [int(x.strip()) for x in text.split(',')]
            if len(color) != 3: return
            r, g, b = [c / 255.0 for c in color]
            if not all(0 <= c <= 1 for c in (r, g, b)): return

            for line_node in self.line_nodes:
                line_node.removeNode()
            self.line_nodes = []
            self.grid_color = (r, g, b)

            for z in range(self.z_size):  
                lines = LineSegs()
                lines.setThickness(1)
                lines.setColor(r, g, b, 1)
                for y in range(self.y_size):  
                    lines.moveTo(0, y, z)
                    lines.drawTo(self.x_size - 1, y, z)  
                for x in range(self.x_size):  
                    lines.moveTo(x, 0, z)
                    lines.drawTo(x, self.y_size - 1, z)  
                line_node = self.render.attachNewNode(lines.create())
                self.line_nodes.append(line_node)
        except ValueError:
            return

    def show_nothing(self):
        for node in self.nodes: node.setScale(0.0)
        for ball_data in self.balls.values(): ball_data['node'].setScale(0.0)
        for line_node in self.line_nodes: line_node.hide()

    def show_everything(self):
        if self.x_size == 1 or self.y_size == 1 or self.z_size == 1: return
        for node in self.nodes: node.setScale(1.0)
        for ball_data in self.balls.values(): ball_data['node'].setScale(0.49)
        for line_node in self.line_nodes: line_node.show()
        
        if self.last_plane_action == 1:
            self.current_plane = (self.current_plane - 1) % self.z_size
        elif self.last_plane_action == 0:
            self.current_plane = (self.current_plane + 1) % self.z_size 

    def plane_up(self):
        self.show_one_floor(1, self.current_plane)
        self.last_plane_action = 1
        
    def plane_down(self):
        self.show_one_floor(0, self.current_plane)
        self.last_plane_action = 0

    def show_one_floor(self, up_or_down, current_z):
        if up_or_down == 0:
            if current_z is not None:
                if not hasattr(self, 'current_plane'): self.current_plane = 0
                else: self.current_plane = (self.current_plane - 1) % self.z_size
                z = self.current_plane
            else:
                z = current_z
                if not (0 <= z < self.z_size): return
        else:
            if current_z is not None:
                if not hasattr(self, 'current_plane'): self.current_plane = 0
                else: self.current_plane = (self.current_plane + 1) % self.z_size
                z = self.current_plane
            else:
                z = current_z
                if not (0 <= z < self.z_size): return

        for node in self.nodes:
            coords = node.getName().split('_')[1].split(',')
            z_pos = float(coords[2])
            node.setScale(1 if int(z_pos) == z else 0)

        for pos, ball_data in list(self.balls.items()):
            z_pos = pos[2]
            ball_data['node'].setScale(0.49 if z_pos == z else 0)

        for i, line_node in enumerate(self.line_nodes):
            if i == z: line_node.show()
            else: line_node.hide()

    def cut_layer(self):
        if self.x_size < 3 or self.y_size <= 3 or self.z_size <= 3: return
        biggestaxis = max(self.x_size, self.y_size, self.z_size)
        
        if self.layer_count < (biggestaxis / 2) - 1:
            for i in range(0, self.layer_count + 1):
                for node in self.nodes:
                    coords = node.getName().split('_')[1].split(',')
                    x, y, z = [int(c) for c in coords]
                    if (x <= i or y <= i or z <= i or 
                        x >= self.x_size-1-i or y >= self.y_size-1-i or z >= self.z_size-1-i):
                        node.setScale(0.2)
                for pos, ball_data in list(self.balls.items()):
                    x, y, z = pos
                    if (x <= i or y <= i or z <= i or 
                        x >= self.x_size-1-i or y >= self.y_size-1-i or z >= self.z_size-1-i):
                        ball_data['node'].setScale(0.2)
            self.layer_count += 1
        else:
            self.layer_count = 0
            self.show_everything()

    # ========================================== #
    # WEIQI / GO LOGIC (RULES & MECHANICS)       #
    # ========================================== #
    def spawn_model(self, pos):
        if self.game_ended: return
        pos_tuple = tuple(int(round(coord)) for coord in pos)
        if not self.is_legal_move(pos_tuple, self.current_color): return

        # Pure placement without double rendering actions
        model = self.ball_model.copyTo(self.render)
        texture = self.black_texture if self.current_color == 0 else self.white_texture
        model.setTexture(texture, 1)
        model.setScale(0.49)
        model.setPos(pos[0], pos[1], pos[2])
        model.setMaterial(self.myMaterial)
        self.balls[pos_tuple] = {'node': model, 'color': self.current_color}

        opponent_color = 1 - self.current_color
        captured_positions = set()
        for adj_pos in self.get_adjacent_positions(pos_tuple):
            if adj_pos in self.balls and self.balls[adj_pos]['color'] == opponent_color:
                group = self.get_group(adj_pos, opponent_color)
                if not self.group_has_liberty(group):
                    captured_positions.update(group)

        if captured_positions:
            for captured_pos in captured_positions:
                if captured_pos in self.balls:
                    self.balls[captured_pos]['node'].removeNode()
                    del self.balls[captured_pos]
            if opponent_color == 0: self.white_captures += len(captured_positions)
            else: self.black_captures += len(captured_positions)
            self.text_captures.setText(f"Black captures: {self.black_captures}\nWhite captures: {self.white_captures}")

        if self.increment > 0:
            if self.current_color == 0: self.black_time += self.increment
            else: self.white_time += self.increment

        self.current_color = (self.current_color + 1) % 2
        self.turn += 1
        self.pass_count = 0 

        self.match_history.append({
            'balls': {k: {'color': v['color']} for k, v in self.balls.items()},
            'current_color': self.current_color,
            'turn': self.turn,
            'black_captures': self.black_captures,
            'white_captures': self.white_captures,
            'board_hash': self.get_board_hash()
        })
        
        self.turn_text.setText(f"Turn: {self.turn}")
        
        if self.timer_mode != "No Timer":
            self.pause_timer()
            self.start_timer()
        elif self.timer_mode == "Byo-yomi":
            if self.current_color == 0:
                self.black_byo_yomi_time = self.byo_time
                self.black_byo_yomi_periods = self.byo_periods
            else:
                self.white_byo_yomi_time = self.byo_time
                self.white_byo_yomi_periods = self.byo_periods

    def is_legal_move(self, pos, color):
        pos_tuple = tuple(int(round(coord)) for coord in pos)
        if pos_tuple in self.balls: return False

        # Virtual execution setup
        sim_board = {k: v['color'] for k, v in self.balls.items()}
        sim_board[pos_tuple] = color
        
        opponent_color = 1 - color
        captured_positions = set()
        
        for adj_pos in self.get_adjacent_positions(pos_tuple):
            if (adj_pos in sim_board and sim_board[adj_pos] == opponent_color):
                group = self.get_virtual_group(adj_pos, opponent_color, sim_board)
                if not self.virtual_group_has_liberty(group, sim_board):
                    captured_positions.update(group)

        for captured_pos in captured_positions:
            del sim_board[captured_pos]

        # Suicide check on virtual board
        player_group = self.get_virtual_group(pos_tuple, color, sim_board)
        if not self.virtual_group_has_liberty(player_group, sim_board): 
            return False

        # Ko check on virtual board
        board_hash = self.get_virtual_board_hash(sim_board)
        if len(self.match_history) >= 2:
            if self.match_history[-2].get('board_hash') == board_hash:
                return False
        return True

    def get_virtual_group(self, pos, color, sim_board):
        visited = set()
        group = set()
        to_check = [pos]
        while to_check:
            current = to_check.pop()
            if current in visited or current not in sim_board or sim_board[current] != color: continue
            visited.add(current)
            group.add(current)
            to_check.extend(self.get_adjacent_positions(current))
        return group

    def virtual_group_has_liberty(self, group, sim_board):
        for pos in group:
            for adj in self.get_adjacent_positions(pos):
                if adj not in sim_board: return True
        return False

    def get_virtual_board_hash(self, sim_board):
        board_state = sorted((pos, col) for pos, col in sim_board.items())
        return hashlib.md5(str(board_state).encode()).hexdigest()

    def get_group(self, pos, color, visited=None):
        if visited is None: visited = set()
        if pos not in self.balls or self.balls[pos]['color'] != color or pos in visited: return set()
        
        group = set()
        to_check = [pos]
        while to_check:
            current = to_check.pop()
            if current in visited or current not in self.balls or self.balls[current]['color'] != color: continue
            visited.add(current)
            group.add(current)
            to_check.extend(self.get_adjacent_positions(current))
        return group

    def group_has_liberty(self, group):
        if not group: return False
        for pos in group:
            for adj in self.get_adjacent_positions(pos):
                if adj not in self.balls: return True
        return False

    def get_adjacent_positions(self, pos):
        x, y, z = pos
        adj = [(x+1,y,z), (x-1,y,z), (x,y+1,z), (x,y-1,z), (x,y,z+1), (x,y,z-1)]
        return [(ax, ay, az) for ax, ay, az in adj if 0 <= ax < self.x_size and 0 <= ay < self.y_size and 0 <= az < self.z_size]

    def get_board_hash(self):
        board_state = sorted((pos, self.balls[pos]['color']) for pos in self.balls)
        return hashlib.md5(str(board_state).encode()).hexdigest()

    def pass_turn(self):
        if self.game_ended: return
        self.pass_count += 1
        self.current_color = (self.current_color + 1) % 2
        self.turn += 1
        self.turn_text.setText(f"Turn: {self.turn}")
        
        if self.timer_mode == "Byo-yomi":
            if self.current_color == 0:
                self.black_byo_yomi_time = self.byo_time
                self.black_byo_yomi_periods = self.byo_periods
            else:
                self.white_byo_yomi_time = self.byo_time
                self.white_byo_yomi_periods = self.byo_periods

        self.start_timer()
        self.check_game_end()

    def check_game_end(self):
        if self.pass_count >= 2: self.end_game()

    def end_game(self):
        self.game_ended = True
        self.pause_timer()
        self.show_everything()
        self.points()
        winner = "Black" if self.black_points > self.white_points else "White" if self.white_points > self.black_points else "Draw"
        self.game_over_text = OnscreenText(
            text=f"Game Over! {winner} wins!",
            pos=(0, 0), scale=0.1, fg=(0, 1, 0, 1), align=TextNode.ACenter, font=self.custom_font
        )

    def points(self):
        self.black_points = self.black_captures + self.calculate_territory(0)
        self.white_points = self.white_captures + self.calculate_territory(1) + self.komi
        self.text_points.setText(text=f"Black: {self.black_points} pts\nWhite: {self.white_points} pts")
        self.text_captures.setText(text=f"Black cap: {self.black_captures}\nWhite cap: {self.white_captures}")

    def calculate_territory(self, color):
        territory, visited = 0, set()
        for x in range(self.x_size):
            for y in range(self.y_size):
                for z in range(self.z_size):
                    pos = (x, y, z)
                    if pos not in self.balls and pos not in visited:
                        region = self.get_region(pos, visited)
                        
                        colors_touched = set()
                        for reg_pos in region:
                            for adj in self.get_adjacent_positions(reg_pos):
                                if adj in self.balls:
                                    colors_touched.add(self.balls[adj]['color'])
                                    
                        # Bounded solely by one color (and not neutral/empty layout)
                        if len(colors_touched) == 1 and color in colors_touched:
                            territory += len(region)
        return territory
    
    def get_region(self, pos, visited):
        if pos in self.balls or pos in visited: return set()
        region, to_check = set(), [pos]
        while to_check:
            current = to_check.pop()
            if current in visited or current in self.balls: continue
            visited.add(current)
            region.add(current)
            to_check.extend([adj for adj in self.get_adjacent_positions(current) if adj not in self.balls and adj not in visited])
        return region

    def rewind_turn(self):
        if not self.match_history: return
        if len(self.match_history) == 1:
            self.match_history.pop()
            for pos in list(self.balls.keys()): self.balls[pos]['node'].removeNode()
            self.balls.clear()
            self.turn = 1
            self.current_color = 0
            self.turn_text.setText(f"Turn: {self.turn}")
            return 
            
        self.match_history.pop()
        prev_state = self.match_history[-1]
        
        for pos in list(self.balls.keys()): self.balls[pos]['node'].removeNode()
        self.balls.clear()

        for pos, ball_data in prev_state['balls'].items():
            model = self.ball_model.copyTo(self.render)
            model.setTexture(self.black_texture if ball_data['color'] == 0 else self.white_texture, 1)
            model.setScale(0.49)
            model.setPos(pos[0], pos[1], pos[2])
            model.setMaterial(self.myMaterial)
            self.balls[pos] = {'node': model, 'color': ball_data['color']}

        self.current_color = prev_state['current_color']
        self.turn = prev_state['turn']
        self.black_captures = prev_state['black_captures']
        self.white_captures = prev_state['white_captures']

        self.turn_text.setText(f"Turn: {self.turn}")
        self.text_captures.setText(f"Black cap: {self.black_captures}\nWhite cap: {self.white_captures}")
        self.points()

    # ========================================== #
    # TIMER SYSTEM                               #
    # ========================================== #
    def set_timer_mode(self, mode):
        self.timer_mode = mode
        self.reset_timers()

    def set_main_time(self, text):
        try: self.main_time = int(text); self.reset_timers()
        except ValueError: pass

    def set_increment(self, text):
        try: self.increment = int(text)
        except ValueError: pass

    def set_byo_time(self, text):
        try: self.byo_time = int(text); self.reset_timers()
        except ValueError: pass

    def set_byo_periods(self, text):
        try: self.byo_periods = int(text); self.reset_timers()
        except ValueError: pass

    def reset_timers(self):
        if self.timer_mode != "No Timer":
            self.black_time = self.main_time
            self.white_time = self.main_time
            self.black_byo_periods_left = self.byo_periods
            self.white_byo_periods_left = self.byo_periods
            self.timer_running = False
            self.update_timer_display()

    def start_timer(self):
        if self.timer_task: self.taskMgr.remove(self.timer_task)
        self.timer_running = True
        self.timer_task = self.taskMgr.add(self.update_timer, "update_timer")

    def pause_timer(self):
        if self.timer_task: self.taskMgr.remove(self.timer_task)
        self.timer_running = False

    def update_timer(self, task):
        if not self.timer_running or self.game_ended: return task.cont
        dt = globalClock.getDt()
        
        c_time = self.black_time if self.current_color == 0 else self.white_time
        c_byo_time = self.black_byo_yomi_time if self.current_color == 0 else self.white_byo_yomi_time
        c_byo_per = self.black_byo_yomi_periods if self.current_color == 0 else self.white_byo_yomi_periods

        if c_time > 0:
            c_time = max(0, c_time - dt)
        else:
            c_byo_time -= dt
            if c_byo_time <= 0:
                c_byo_per -= 1
                if c_byo_per <= 0:
                    self.handle_timeout()
                    return task.done
                c_byo_time = self.byo_time

        if self.current_color == 0:
            self.black_time, self.black_byo_yomi_time, self.black_byo_yomi_periods = c_time, c_byo_time, c_byo_per
        else:
            self.white_time, self.white_byo_yomi_time, self.white_byo_yomi_periods = c_time, c_byo_time, c_byo_per

        b_disp = self.format_time(self.black_time, self.black_byo_yomi_time, self.black_byo_yomi_periods)
        w_disp = self.format_time(self.white_time, self.white_byo_yomi_time, self.white_byo_yomi_periods)
        self.timer_text.setText(f"Black: {b_disp}\nWhite: {w_disp}")
        return task.cont
    
    def format_time(self, main_time, byo_yomi_time, byo_yomi_periods):
        if main_time > 0:
            return f"{int(main_time // 60)}:{int(main_time % 60):02d}"
        return f"{int(byo_yomi_time)} ({byo_yomi_periods})"

    def handle_timeout(self):
        winner = "Black" if self.current_color == 1 else "White"
        self.game_ended = True
        self.timer_text.setText(f"{winner} wins by timeout!")
        self.game_over_text = OnscreenText(
            text=f"Game Over! {winner} wins by timeout!",
            pos=(0, 0), scale=0.1, fg=(0.25, 1, 0, 1), align=TextNode.ACenter
        )

    def update_timer_display(self):
        if self.timer_mode == "No Timer":
            self.timer_text.setText("Black:NT\nWhite:NT")
            return
        b_mins, b_secs = divmod(int(self.black_time), 60)
        w_mins, w_secs = divmod(int(self.white_time), 60)
        b_ex = f" ({self.black_byo_periods_left} p)" if self.timer_mode == "Byo-yomi" else ""
        w_ex = f" ({self.white_byo_periods_left} p)" if self.timer_mode == "Byo-yomi" else ""
        self.timer_text.setText(f"Black: {b_mins}:{b_secs:02d}{b_ex}\nWhite: {w_mins}:{w_secs:02d}{w_ex}")

    # ========================================== #
    # INPUT & CAMERA CONTROLS                    #
    # ========================================== #
    def setup_collision_system(self):
        self.cTrav = CollisionTraverser()
        self.pickerQueue = CollisionHandlerQueue()
        self.pickerNode = CollisionNode("mouseRay")
        self.pickerNP = self.camera.attachNewNode(self.pickerNode)
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.pickerNode.setFromCollideMask(1)
        self.cTrav.addCollider(self.pickerNP, self.pickerQueue)

    def bind_inputs(self):
        self.accept("space", self.camera_control.start_rotation)
        self.accept("space-up", self.camera_control.stop_rotation)
        self.accept("wheel_up", self.camera_control.zoom_in)
        self.accept("wheel_down", self.camera_control.zoom_out)
        self.accept("arrow_left", self.camera_control.rotate_left)
        self.accept("arrow_right", self.camera_control.rotate_right)
        self.accept("arrow_up", self.camera_control.rotate_up)
        self.accept("arrow_down", self.camera_control.rotate_down)
        self.accept("s", self.cut_layer)
        
        self.accept("a", self.points)
        self.accept("x", self.gui_help)
        self.accept("c", self.gui_extra)
        self.accept("d", self.rewind_turn)
        self.accept("z", self.pass_turn)
        self.accept("mouse1", self.check_click)
        self.accept("mouse3", self.camera_control.start_rotation)
        self.accept("mouse3-up", self.camera_control.stop_rotation)
        self.accept("r", self.call_reset_camera)
        self.accept("q", self.plane_down)
        self.accept("e", self.plane_up)
        self.accept("w", self.show_everything)

    def check_click(self):
        if not self.mouseWatcherNode.hasMouse(): return
        mpos = self.mouseWatcherNode.getMouse()
        self.pickerRay.setFromLens(self.camNode, mpos.getX(), mpos.getY())
        if self.x_size == 1 and self.y_size == 1 and self.z_size == 1: return
        
        self.cTrav.traverse(self.render)
        if self.pickerQueue.getNumEntries() > 0:
            self.pickerQueue.sortEntries()
            hit = self.pickerQueue.getEntry(0)
            pos = hit.getIntoNodePath().getParent().getPos(self.render)
            pos_tuple = (int(round(pos.x)), int(round(pos.y)), int(round(pos.z)))

            if not (0 <= pos_tuple[0] < self.x_size and 0 <= pos_tuple[1] < self.y_size and 0 <= pos_tuple[2] < self.z_size): return
            if pos_tuple in self.balls: return
            self.spawn_model(pos_tuple)

    def call_reset_camera(self):
        self.reset_camera(self.size)

    def reset_camera(self, size):
        parts = [int(x.strip()) for x in size.split(',')]
        center = Point3((parts[0] - 1) / 2, (parts[1] - 1) / 2, (parts[2] - 1) / 2)
        self.camera_control.center = center
        self.camera_control.update_camera_position()
        self.camera.lookAt(center)

    # ========================================== #
    # USER INTERFACE (GUI)                       #
    # ========================================== #
    def process_coordinates(self, input_text=None):
        text = self.coord_entry.get() if input_text is None or not isinstance(input_text, str) else input_text
        try:
            coords = [int(x.strip()) for x in text.split(',')]
            if len(coords) != 3: return
            if not (0 <= coords[0] < self.x_size and 0 <= coords[1] < self.y_size and 0 <= coords[2] < self.z_size): return
            if tuple(coords) in self.balls: return
            self.spawn_model(tuple(coords))
            self.coord_entry["focus"] = 0
        except ValueError: return

    def set_grid_size(self, input_text=None):
        text = self.size_entry.get() if input_text is None else str(input_text)
        try:
            parts = [int(x.strip()) for x in text.split(',')]
            if len(parts) == 1:
                normalized_size = f"{parts[0]},{parts[0]},{parts[0]}"
            elif len(parts) == 2:
                normalized_size = f"{parts[0]},{parts[1]},1"
            else:
                normalized_size = f"{parts[0]},{parts[1]},{parts[2]}"
                
            self.size = normalized_size
            self.reset_game()
            self.generate_grid(self.size)
            
            if self.timer_mode != "No Timer":
                self.reset_timers()
                self.pause_timer()
            self.size_entry["focus"] = 0
        except Exception: 
            return

    def set_komi(self, text):
        try: self.komi = float(text)
        except ValueError: pass

    def setup_gui(self):
        if not self.custom_font.isValid(): self.custom_font = None
        TS = 0.065
        BS = 0.05

        self.extra = OnscreenText(text="C: timer & settings", parent=self.a2dTopLeft, pos=(0.03, -0.07), scale=TS, align=TextNode.ALeft, font=self.custom_font)
        self.help = OnscreenText(text="X: help", parent=self.a2dTopLeft, pos=(0.03, -0.16), scale=TS, align=TextNode.ALeft, font=self.custom_font)
        self.timer_text = OnscreenText(text="Black: --:--\nWhite: --:--", parent=self.a2dTopLeft, pos=(0.03, -0.27), scale=TS, align=TextNode.ALeft, font=self.custom_font, mayChange=True)
        self.turn_text = OnscreenText(text=f"Turn: {self.turn}", parent=self.a2dTopLeft, pos=(0.03, -0.42), scale=TS, align=TextNode.ALeft, mayChange=True)

        self.text_points = OnscreenText(text=f"Black: {self.black_points} pts\nWhite: {self.white_points} pts", parent=self.a2dTopRight, pos=(-0.03, -0.07), scale=TS, align=TextNode.ARight, font=self.custom_font, mayChange=True)
        self.text_captures = OnscreenText(text=f"Black cap: {self.black_captures}\nWhite cap: {self.white_captures}", parent=self.a2dTopRight, pos=(-0.03, -0.25), scale=TS, align=TextNode.ARight, font=self.custom_font, mayChange=True)
        
        self.save_game_gui = DirectButton(text=("Save", "Saved!", "Save", "disabled"), parent=self.a2dTopRight, pos=(-0.15, 0, -0.42), scale=BS, command=self.save_game)
        self.load_game_gui = DirectButton(text=("Load", "Loaded!", "Load", "disabled"), parent=self.a2dTopRight, pos=(-0.15, 0, -0.52), scale=BS, command=self.load_game)

        self.coord_label_info = OnscreenText(text="Blue ball = (0,0,0)", parent=self.a2dTopCenter, pos=(0, -0.07), scale=0.06, align=TextNode.ACenter, font=self.custom_font)

        self.size_label = OnscreenText(text="Grid size (x,y,z):", parent=self.a2dBottomLeft, pos=(0.03, 0.15), scale=TS, align=TextNode.ALeft, font=self.custom_font)
        self.size_entry = DirectEntry(text="", scale=BS, command=self.set_grid_size, initialText="", numLines=1, focus=0, parent=self.a2dBottomLeft, pos=(0.04, 0, 0.05), frameColor=(0, 0, 0, 0.6), text_fg=(1, 1, 1, 1), width=9)

        self.coord_label = OnscreenText(text="Move (x,y,z):", parent=self.a2dBottomCenter, pos=(0, 0.15), scale=TS, align=TextNode.ACenter, font=self.custom_font)
        self.coord_entry = DirectEntry(text="", scale=BS, command=self.process_coordinates, initialText="", numLines=1, focus=0, parent=self.a2dBottomCenter, pos=(-0.20, 0, 0.05), frameColor=(0, 0, 0, 0.6), text_fg=(1, 1, 1, 1), width=8)
        self.coord_entry.bind(DGG.ENTER, self.process_coordinates)

    def gui_help(self):
        if not self.custom_font.isValid(): self.custom_font = None
        if self.help_show == 0:
            self.hotkeys = OnscreenText(
                text="Space+mouse: rotate  |  LClick: play  |  RClick: recenter\n"
                     "R: reset camera  |  E/Q: plane up/down  |  W: show all\n"
                     "A: count points  |  Z: pass  |  D: rewind  |  S: shrink layer",
                parent=self.a2dTopLeft, pos=(0.03, -0.58), scale=0.065, align=TextNode.ALeft, font=self.custom_font
            )
        else: self.hotkeys.destroy()
        self.help_show = 1 - self.help_show 

    def gui_extra(self):
                if self.extra_show == 0:
                    S, ES, Ex = 0.065, 0.05, -0.70          
                    rows = [
                        (-0.22, "Grid color (r,g,b)",  "color",      self.custom_grid_color,     "",    6),
                        (-0.33, "Bg color (r,g,b)",    "background", self.custom_background_color,"",   6),
                        (-0.44, "Komi",                "komi",       self.set_komi,              "",    4),
                        (-0.55, "Timer method",        "timer_mode", None,                       None,  0),
                        (-0.66, "Main time (s)",       "main_time",  self.set_main_time,         "300", 4),
                        (-0.77, "Increment (s)",       "increment",  self.set_increment,         "0",   4),
                        (-0.88, "Byo-yomi time (s)",   "byo_time",   self.set_byo_time,          "30",  4),
                        (-0.95, "Byo-yomi periods",    "byo_periods",self.set_byo_periods,       "5",   4),
                    ]
                    for y, label, key, cmd, init, w in rows:
                        # SE CORRIGIÓ: 'self.a2dRight' por 'self.a2dRightCenter' en las siguientes líneas
                        self.extra_gui_elements[f"{key}_label"] = OnscreenText(text=label, parent=self.a2dRightCenter, pos=(-0.03, y), scale=S, align=TextNode.ARight, font=self.custom_font)
                        if key == "timer_mode":
                            self.extra_gui_elements["timer_mode_menu"] = DirectOptionMenu(parent=self.a2dRightCenter, pos=(Ex, 0, y), scale=ES, items=["No Timer", "Absolute", "Fischer", "Byo-yomi"], command=self.set_timer_mode, initialitem=0, frameColor=(0, 0, 0, 0.5), text_fg=(1, 1, 1, 1))
                        else:
                            entry = DirectEntry(text="", parent=self.a2dRightCenter, pos=(Ex, 0, y), scale=ES, command=cmd, initialText=init, frameColor=(0, 0, 0, 0.5), text_fg=(1, 1, 1, 1), width=w)
                            self.extra_gui_elements[f"{key}_entry"] = entry
                    
                    for name in ["color_entry", "background_entry", "main_time_entry", "increment_entry", "byo_time_entry", "byo_periods_entry"]:
                        if name in self.extra_gui_elements:
                            self.extra_gui_elements[name].bind(DGG.ENTER, lambda event, n=name: self.extra_gui_elements[n]["command"](self.extra_gui_elements[n].get()))
                else:
                    for element in self.extra_gui_elements.values():
                        if element is not None: element.destroy()
                    self.extra_gui_elements.clear()
                self.extra_show = 1 - self.extra_show

app = GridDemo(0)
app.run()
