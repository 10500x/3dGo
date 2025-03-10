from panda3d.core import NodePath, CollisionNode, CollisionSphere, CollisionTraverser, CollisionHandlerQueue, CollisionRay, TextNode
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectEntry, DirectButton, DirectFrame, DirectLabel, DGG, DirectOptionMenu
from direct.task import Task
from panda3d.core import ClockObject, Point3, LineSegs, WindowProperties
from camera import Camera
import hashlib

# Load configuration file
from panda3d.core import loadPrcFile
loadPrcFile("config/conf.prc")

globalClock = ClockObject.getGlobalClock()

class GridDemo(ShowBase):
    def __init__(self, size):
        super().__init__()
        self.custom_font = self.loader.loadFont("fonts/Montserrat-Regular.ttf")
        self.initial_size = size
        self.size = 1
        self.extra_gui_elements = {}
        self.background_color = (0.75, 0.75, 0.75)  # Default background color
        self.setBackgroundColor(self.background_color)
        self.ball_model = self.loader.loadModel("models/sphere.bam")
        self.black_texture = self.loader.loadTexture("textures/black.png")
        self.white_texture = self.loader.loadTexture("textures/white.png")
        self.camera_control = Camera(self, self.initial_size)
        self.black_points = 0
        self.white_points = 0
        self.black_captures = 0
        self.white_captures = 0
        self.komi = 6.5
        self.pass_count = 0
        self.game_ended = False
        self.match_history = []
        self.history_index = -1  # Tracks current position in history
        self.vertices = []
        self.edges = []
        self.nodes = []
        self.line_nodes = []
        self.balls = {}
        self.current_color = 0
        self.turn = 1
        self.current_plane = -1
        self.allow_moves = True
        self.grid_color = (1, 1, 1)  # Default grid color

        # Timer-related attributes
        self.timer_running = False
        self.black_time = 300  # Default 5 minutes in seconds
        self.white_time = 300
        self.active_timer = None
        self.timer_mode = "No Timer"
        self.main_time = 300
        self.increment = 0
        self.byo_periods = 5
        self.byo_time = 30
        self.black_byo_periods_left = self.byo_periods
        self.white_byo_periods_left = self.byo_periods
        self.black_byo_yomi_time = self.byo_time
        self.white_byo_yomi_time = self.byo_time
        self.black_byo_yomi_periods = self.byo_periods
        self.white_byo_yomi_periods = self.byo_periods
        self.timer_task = None

        # UI Theme
        self.panel_color = (0.1, 0.1, 0.1, 0.8)  # Dark gray with transparency
        self.text_color = (1, 1, 1, 1)  # White
        self.entry_color = (0.3, 0.3, 0.3, 0.9)  # Slightly lighter gray for entries
        self.button_color = (0.2, 0.6, 0.2, 0.9)  # Green for buttons
        self.button_rollover_color = (0.3, 0.8, 0.3, 0.9)  # Lighter green on hover
        props = self.win.getProperties()
        win_width = props.getXSize()
        win_height = props.getYSize()
        aspect_ratio = win_width / win_height if win_height > 0 else 1.0
        self.aspect_scale = 1.0 / aspect_ratio

        self.setup_collision_system()
        self.disableMouse()
        self.bind_inputs()
        self.setup_gui()
        self.generate_grid(size)
        self.place_initial_ball()

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
        self.accept("p", self.points)
        self.accept("h", self.gui_help)
        self.accept("g", self.toggle_settings)
        self.accept("k", self.rewind)
        self.accept("o", self.pass_turn)
        self.accept("f", self.redo)  # Bind F to redo
        self.accept("mouse1", self.check_click)
        self.accept("mouse3", self.change_camera_center)
        self.accept("r", self.reset_camera)
        self.accept("w", self.show_one_floor, [None])
        self.accept("s", self.show_everything)

    def place_initial_ball(self):
        initial_ball = self.loader.loadModel("smiley")
        initial_ball.setPos(0, 0, 0)
        initial_ball.setTexture(self.loader.loadTexture("textures/blue.png"), 1)
        initial_ball.setScale(0.05)
        initial_ball.reparentTo(self.render)

    def pass_turn(self):
        if self.game_ended:
            print("Game has already ended")
            return
        self.pass_count += 1
        print(f"Player {self.current_color} passed at Turn: {self.turn}, Current pass_count: {self.pass_count}")
        self.current_color = 1 - self.current_color
        self.turn += 1
        self.turn_text.setText(f"Turn: {self.turn}")

        if self.current_color == 0:
            self.black_byo_yomi_time = self.byo_time
            self.black_byo_yomi_periods = self.byo_periods
        else:
            self.white_byo_yomi_time = self.byo_time
            self.white_byo_yomi_periods = self.byo_periods

        self.start_timer()
        self.check_game_end()

    def check_game_end(self):
        if self.pass_count >= 2:
            self.end_game()

    def points(self):
        self.black_points = self.black_captures + self.calculate_territory(0)
        self.white_points = self.white_captures + self.calculate_territory(1) + self.komi
        self.text_points.setText(f"Black points: {self.black_points}\nWhite points: {self.white_points}")

    def end_game(self):
        self.game_ended = True
        self.points()
        winner = "Black" if self.black_points > self.white_points else "White" if self.white_points > self.black_points else "Draw"
        self.game_over_text.setText(f"Game Over! {winner} wins!")
        print(f"Game Over - {winner} wins with scores: Black {self.black_points}, White {self.white_points}")

    def reset_game(self):
        self.game_ended = False
        self.pass_count = 0
        self.white_points = 0
        self.black_points = 0
        self.black_captures = 0
        self.white_captures = 0
        self.balls.clear()
        self.match_history.clear()
        self.history_index = -1
        self.turn = 1
        self.current_color = 0
        self.turn_text.setText(f"Turn: {self.turn}")
        self.text_captures.setText(f"Black captures: 0\nWhite captures: 0")
        self.text_points.setText(f"Black points: 0\nWhite points: 0")
        self.reset_timers()

    def calculate_territory(self, color):
        territory = 0
        visited = set()
        print(f"Calculating territory for color {color} (0=Black, 1=White)")
        for x in range(self.size):
            for y in range(self.size):
                for z in range(self.size):
                    pos = (x, y, z)
                    if pos not in self.balls and pos not in visited:
                        region = self.get_region(pos, visited)
                        if not region:
                            continue
                        is_enclosed = self.is_region_enclosed(region, color)
                        if is_enclosed:
                            territory += len(region)
                            print(f"Found enclosed region for color {color}: {region}, size: {len(region)}")
                        else:
                            print(f"Region {region} is not fully enclosed for color {color}")
        print(f"Total territory for color {color}: {territory}")
        return territory

    def get_region(self, pos, visited):
        if pos in self.balls or pos in visited or not (0 <= pos[0] < self.size and
                                                      0 <= pos[1] < self.size and
                                                      0 <= pos[2] < self.size):
            return set()
        region = set()
        to_check = [pos]
        while to_check:
            current = to_check.pop()
            if current in visited or current in self.balls:
                continue
            visited.add(current)
            region.add(current)
            to_check.extend([adj for adj in self.get_adjacent_positions(current)
                            if adj not in self.balls and adj not in visited])
        return region

    def is_region_enclosed(self, region, color):
        boundary_visited = set()
        for pos in region:
            adj_positions = self.get_adjacent_positions(pos)
            for adj in adj_positions:
                if adj in region or adj in boundary_visited:
                    continue
                boundary_visited.add(adj)
                if not (0 <= adj[0] < self.size and 0 <= adj[1] < self.size and 0 <= adj[2] < self.size):
                    continue
                if adj not in self.balls:
                    external_region = self.get_region(adj, set(region))
                    if self.is_unbounded(external_region):
                        return False
                    continue
                if self.balls[adj]['color'] != color:
                    return False
        return True

    def is_unbounded(self, region):
        for pos in region:
            x, y, z = pos
            if (x == 0 or x == self.size - 1 or
                y == 0 or y == self.size - 1 or
                z == 0 or z == self.size - 1):
                return True
        return False

    def generate_grid(self, size):
        size = int(size)
        self.size = size

        # Clear existing balls
        for ball_data in list(self.balls.values()):
            ball_data['node'].removeNode()
        self.balls.clear()

        # Clear existing nodes
        for node in self.nodes:
            if not node.is_empty():
                collision_node = node.find("**/+CollisionNode")
                if collision_node:
                    collision_node.removeNode()
                node.removeNode()

        # Clear existing line nodes
        for line_node in self.line_nodes:
            line_node.removeNode()
        self.line_nodes = []
        self.nodes = []
        self.edges = []
        self.vertices = []

        for x in range(self.size):
            for y in range(self.size):
                for z in range(self.size):
                    vertex_node = NodePath(f"vertex_{x},{y},{z}")
                    vertex_node.setPos(x, y, z)
                    vertex_node.reparentTo(self.render)
                    collision_sphere = CollisionSphere(0, 0, 0, 0.15)
                    collision_node = vertex_node.attachNewNode(CollisionNode(f'cnode_{x}{y}{z}'))
                    collision_node.node().addSolid(collision_sphere)
                    collision_node.node().setIntoCollideMask(1)
                    if x + 1 < self.size:
                        self.edges.append(((x, y, z), (x + 1, y, z)))
                    if y + 1 < self.size:
                        self.edges.append(((x, y, z), (x, y + 1, z)))
                    if z + 1 < self.size:
                        self.edges.append(((x, y, z), (x, y, z + 1)))
                    self.vertices.append((x, y, z))
                    self.nodes.append(vertex_node)

        for z in range(self.size):
            lines = LineSegs()
            lines.setThickness(1)
            lines.setColor(*self.grid_color, 1)
            for y in range(self.size):
                lines.moveTo(0, y, z)
                lines.drawTo(self.size - 1, y, z)
            for x in range(self.size):
                lines.moveTo(x, 0, z)
                lines.drawTo(x, self.size - 1, z)
            line_node = self.render.attachNewNode(lines.create())
            self.line_nodes.append(line_node)

        self.place_initial_ball()
        self.reset_camera()

    def custom_background_color(self, event=None):
        if self.extra_show == 1 and "background_entry" in self.extra_gui_elements:
            text = self.extra_gui_elements["background_entry"].get()
        else:
            if isinstance(event, tuple) and len(event) == 3:
                text = ','.join(str(int(c * 255)) for c in event)
            else:
                text = ','.join(str(int(c * 255)) for c in self.background_color)

        try:
            color = [int(x.strip()) / 255.0 for x in text.split(',')]
            if len(color) != 3 or not all(0 <= c <= 1 for c in color):
                return
            r, g, b = color
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
            color = [int(x.strip()) / 255.0 for x in text.split(',')]
            if len(color) != 3 or not all(0 <= c <= 1 for c in color):
                return
            r, g, b = color
            self.grid_color = (r, g, b)

            for line_node in self.line_nodes:
                line_node.removeNode()
            self.line_nodes = []

            for z in range(self.size):
                lines = LineSegs()
                lines.setThickness(1)
                lines.setColor(r, g, b, 1)
                for y in range(self.size):
                    lines.moveTo(0, y, z)
                    lines.drawTo(self.size - 1, y, z)
                for x in range(self.size):
                    lines.moveTo(x, 0, z)
                    lines.drawTo(x, self.size - 1, z)
                line_node = self.render.attachNewNode(lines.create())
                self.line_nodes.append(line_node)
        except ValueError:
            return

    def set_grid_size(self, input_text=None):
        text = self.size_entry.get() if input_text is None else str(input_text)
        try:
            new_size = int(text.strip())
            self.size = new_size
            self.generate_grid(new_size)
            self.reset_game()
            self.turn = 1
            self.turn_text.setText(f"Turn: {self.turn}")
            self.size_entry["focus"] = 0
        except ValueError:
            return

    def gui_help(self):
        if self.help_show == 0:
            self.hotkeys = OnscreenText(
                text="Press space and move mouse to rotate\nLeft click to play\nRight click to change center\nR to reset camera\nW to move between planes\nS to see whole grid\nP to count points",
                pos=(-1.9, -0.1), scale=0.07, align=TextNode.ALeft, font=self.custom_font, fg=self.text_color
            )
        else:
            self.hotkeys.destroy()
        self.help_show = 1 - self.help_show

    def toggle_settings(self):
        if self.settings_frame.isHidden():
            self.settings_frame.show()
            self.game_over_text.hide()
        else:
            self.settings_frame.hide()
            self.game_over_text.show()

    def gui_extra(self):
        if self.extra_show == 0:
            gui_definitions = [
                ("color_label", OnscreenText, {"text": "Grid color, r,g,b", "pos": (-0.6, 0.5), "scale": 0.05, "align": TextNode.ALeft, "font": self.custom_font, "fg": self.text_color}),
                ("color_entry", DirectEntry, {"text": "", "scale": 0.05, "initialText": "255,255,255", "pos": (-0.1, 0, 0.5), "frameColor": self.entry_color, "text_fg": self.text_color, "width": 8, "command": self.custom_grid_color}),
                ("background_label", OnscreenText, {"text": "Background color, r,g,b", "pos": (-0.6, 0.4), "scale": 0.05, "align": TextNode.ALeft, "font": self.custom_font, "fg": self.text_color}),
                ("background_entry", DirectEntry, {"text": "", "scale": 0.05, "initialText": "191,191,191", "pos": (-0.1, 0, 0.4), "frameColor": self.entry_color, "text_fg": self.text_color, "width": 8, "command": self.custom_background_color}),
                ("komi_label", OnscreenText, {"text": "Komi", "pos": (-0.6, 0.3), "scale": 0.05, "align": TextNode.ALeft, "font": self.custom_font, "fg": self.text_color}),
                ("komi_entry", DirectEntry, {"text": "", "scale": 0.05, "initialText": "6.5", "pos": (-0.1, 0, 0.3), "frameColor": self.entry_color, "text_fg": self.text_color, "width": 5, "command": self.set_komi}),
                ("timer_label", OnscreenText, {"text": "Timer Method", "pos": (-0.6, 0.2), "scale": 0.05, "align": TextNode.ALeft, "font": self.custom_font, "fg": self.text_color}),
                ("timer_mode_menu", DirectOptionMenu, {"scale": 0.05, "items": ["No timer", "Absolute", "Fischer", "Byo-yomi"], "command": self.set_timer_mode, "initialitem": 0, "pos": (-0.1, 0, 0.2), "frameColor": self.panel_color, "text_fg": self.text_color}),
                ("main_time_label", OnscreenText, {"text": "Main Time (s)", "pos": (-0.6, 0.1), "scale": 0.05, "align": TextNode.ALeft, "font": self.custom_font, "fg": self.text_color}),
                ("main_time_entry", DirectEntry, {"text": "", "scale": 0.05, "initialText": "300", "pos": (-0.1, 0, 0.1), "frameColor": self.entry_color, "text_fg": self.text_color, "width": 5, "command": self.set_main_time}),
                ("increment_label", OnscreenText, {"text": "Increment (s)", "pos": (-0.6, 0.0), "scale": 0.05, "align": TextNode.ALeft, "font": self.custom_font, "fg": self.text_color}),
                ("increment_entry", DirectEntry, {"text": "", "scale": 0.05, "initialText": "0", "pos": (-0.1, 0, 0.0), "frameColor": self.entry_color, "text_fg": self.text_color, "width": 5, "command": self.set_increment}),
                ("byo_time_label", OnscreenText, {"text": "Byo-yomi Time (s)", "pos": (-0.6, -0.1), "scale": 0.05, "align": TextNode.ALeft, "font": self.custom_font, "fg": self.text_color}),
                ("byo_time_entry", DirectEntry, {"text": "", "scale": 0.05, "initialText": "30", "pos": (-0.1, 0, -0.1), "frameColor": self.entry_color, "text_fg": self.text_color, "width": 5, "command": self.set_byo_time}),
                ("byo_periods_label", OnscreenText, {"text": "Byo-yomi Periods", "pos": (-0.6, -0.2), "scale": 0.05, "align": TextNode.ALeft, "font": self.custom_font, "fg": self.text_color}),
                ("byo_periods_entry", DirectEntry, {"text": "", "scale": 0.05, "initialText": "5", "pos": (-0.1, 0, -0.2), "frameColor": self.entry_color, "text_fg": self.text_color, "width": 5, "command": self.set_byo_periods}),
            ]
            for name, cls, kwargs in gui_definitions:
                kwargs['parent'] = self.settings_frame
                obj = cls(**kwargs)
                self.extra_gui_elements[name] = obj
                if name.endswith("_entry"):
                    obj.bind(DGG.ENTER, lambda event, n=name: self.extra_gui_elements[n]["command"](self.extra_gui_elements[n].get()))
        else:
            for element in self.extra_gui_elements.values():
                if element is not None:
                    element.destroy()
            self.extra_gui_elements.clear()
        self.extra_show = 1 - self.extra_show

    def set_komi(self, text):
        try:
            self.komi = float(text)
            print(f"Komi set to: {self.komi}")
        except ValueError:
            print(f"Invalid komi value: {text}, keeping default komi: {self.komi}")

    def setup_gui(self):
        props = self.win.getProperties()
        win_width = props.getXSize()
        win_height = props.getYSize()
        aspect_ratio = win_width / win_height if win_height > 0 else 1.0
        self.aspect_scale = 1.0 / aspect_ratio

        # Stats Panel (Top Left)
        self.stats_frame = DirectFrame(
            frameColor=self.panel_color, frameSize=(-0.5, 0.5, -0.4, 0.4), pos=(-1.9, 0, 0.8)
        )
        self.instructions_text = OnscreenText(
            text="Press G for settings\nPress H for help", pos=(-0.25, 0.3), scale=0.05,
            fg=self.text_color, parent=self.stats_frame, align=TextNode.ALeft, font=self.custom_font
        )
        self.turn_text = OnscreenText(
            text=f"Turn: {self.turn}", pos=(-0.25, 0.15), scale=0.05,
            fg=self.text_color, parent=self.stats_frame, align=TextNode.ALeft, font=self.custom_font
        )
        self.timer_text = OnscreenText(
            text="Black: 0:00\nWhite: 0:00", pos=(-0.25, 0.05), scale=0.05,
            fg=self.text_color, parent=self.stats_frame, align=TextNode.ALeft, font=self.custom_font
        )

        # Points Panel (Top Right)
        self.points_frame = DirectFrame(
            frameColor=self.panel_color, frameSize=(-0.5, 0.5, -0.3, 0.3), pos=(1.4, 0, 0.8)
        )
        self.text_points = OnscreenText(
            text=f"Black points: {self.black_points}\nWhite points: {self.white_points}",
            pos=(-0.25, 0.2), scale=0.05, fg=self.text_color, parent=self.points_frame,
            align=TextNode.ALeft, font=self.custom_font
        )
        self.text_captures = OnscreenText(
            text=f"Black captures: {self.black_captures}\nWhite captures: {self.white_captures}",
            pos=(-0.25, 0.05), scale=0.05, fg=self.text_color, parent=self.points_frame,
            align=TextNode.ALeft, font=self.custom_font
        )

        # Input Panel (Bottom Left)
        self.input_frame = DirectFrame(
            frameColor=self.panel_color, frameSize=(-0.5, 0.5, -0.2, 0.2), pos=(-1.9, 0, -0.8)
        )
        self.game_over_text = OnscreenText(
            text="To start, select a grid size and press enter.", pos=(0, 0.9), scale=0.07,
            fg=self.text_color, align=TextNode.ACenter, font=self.custom_font
        )
        self.size_label = OnscreenText(
            text="Enter the grid size", pos=(-0.25, 0.1), scale=0.05,
            fg=self.text_color, parent=self.input_frame, align=TextNode.ALeft, font=self.custom_font
        )
        self.size_entry = DirectEntry(
            text="", scale=0.05, initialText="", pos=(-0.25, 0, 0),
            frameColor=self.entry_color, text_fg=self.text_color, width=5,
            parent=self.input_frame
        )
        self.size_entry.bind(DGG.ENTER, self.set_grid_size)
        self.enter_size_button = DirectButton(
            text="Enter size", scale=0.05, pos=(0.25, 0, 0),
            frameColor=(
                self.button_color,           # Normal state
                self.button_color,           # Pressed state
                self.button_rollover_color,  # Rollover state
                self.button_color            # Disabled state
            ),
            text_fg=self.text_color, parent=self.input_frame,
            command=self.set_grid_size
        )
        self.coord_label = OnscreenText(
            text="Enter x,y,z", pos=(-0.25, -0.1), scale=0.05,
            fg=self.text_color, parent=self.input_frame, align=TextNode.ALeft, font=self.custom_font
        )
        self.coord_entry = DirectEntry(
            text="", scale=0.05, initialText="", pos=(-0.25, 0, -0.1),
            frameColor=self.entry_color, text_fg=self.text_color, width=8,
            parent=self.input_frame
        )
        self.coord_entry.bind(DGG.ENTER, self.process_coordinates)
        self.submit_move_button = DirectButton(
            text="Submit move", scale=0.05, pos=(0.25, 0, -0.1),
            frameColor=(
                self.button_color,           # Normal state
                self.button_color,           # Pressed state
                self.button_rollover_color,  # Rollover state
                self.button_color            # Disabled state
            ),
            text_fg=self.text_color, parent=self.input_frame,
            command=self.process_coordinates
        )

        # Settings Frame (Bottom Right)
        self.settings_frame = DirectFrame(
            frameColor=self.panel_color, frameSize=(-0.7, 0.7, -0.6, 0.6), pos=(1.4, 0, -0.6)
        )
        self.settings_frame.hide()
        self.help_show = 0
        self.extra_show = 0
        
    def set_timer_mode(self, mode):
        self.timer_mode = mode
        self.reset_timers()

    def set_main_time(self, text):
        try:
            self.main_time = int(text)
            self.reset_timers()
        except ValueError:
            pass

    def set_increment(self, text):
        try:
            self.increment = int(text)
        except ValueError:
            pass

    def set_byo_time(self, text):
        try:
            self.byo_time = int(text)
            self.reset_timers()
        except ValueError:
            pass

    def set_byo_periods(self, text):
        try:
            self.byo_periods = int(text)
            self.reset_timers()
        except ValueError:
            pass

    def reset_timers(self):
        if self.timer_mode != "No timer":
            self.black_time = self.main_time
            self.white_time = self.main_time
            self.black_byo_periods_left = self.byo_periods
            self.white_byo_periods_left = self.byo_periods
            self.black_byo_yomi_time = self.byo_time
            self.white_byo_yomi_time = self.byo_time
            self.black_byo_yomi_periods = self.byo_periods
            self.white_byo_yomi_periods = self.byo_periods
            self.timer_running = False
            self.active_timer = None
            self.update_timer_display()
        else:
            return

    def start_timer(self):
        if self.timer_task:
            self.taskMgr.remove(self.timer_task)
        if self.timer_mode != "No timer":
            self.timer_running = True
            self.timer_task = self.taskMgr.add(self.update_timer, "update_timer")

    def pause_timer(self):
        if self.timer_task:
            self.taskMgr.remove(self.timer_task)
        self.timer_running = False

    def get_board_hash(self):
        board_state = sorted((pos, self.balls[pos]['color']) for pos in self.balls)
        return hashlib.md5(str(board_state).encode()).hexdigest()

    def update_timer(self, task):
        if not self.timer_running or self.game_ended:
            return task.cont

        dt = globalClock.getDt()
        current_time = self.black_time if self.current_color == 0 else self.white_time
        current_byo_yomi_time = self.black_byo_yomi_time if self.current_color == 0 else self.white_byo_yomi_time
        current_byo_yomi_periods = self.black_byo_yomi_periods if self.current_color == 0 else self.white_byo_yomi_periods

        if current_time > 0:
            current_time -= dt
            if current_time < 0:
                current_time = 0
                print(f"Player {self.current_color} main time depleted, entering byo-yomi")
        else:
            current_byo_yomi_time -= dt
            if current_byo_yomi_time <= 0:
                current_byo_yomi_periods -= 1
                print(f"Player {self.current_color} byo-yomi period ended, periods left: {current_byo_yomi_periods}")
                if current_byo_yomi_periods <= 0:
                    self.handle_timeout()
                    return task.done
                current_byo_yomi_time = self.byo_time

        if self.current_color == 0:
            self.black_time = current_time
            self.black_byo_yomi_time = current_byo_yomi_time
            self.black_byo_yomi_periods = current_byo_yomi_periods
        else:
            self.white_time = current_time
            self.white_byo_yomi_time = current_byo_yomi_time
            self.white_byo_yomi_periods = current_byo_yomi_periods

        black_display = self.format_time(self.black_time, self.black_byo_yomi_time, self.black_byo_yomi_periods)
        white_display = self.format_time(self.white_time, self.white_byo_yomi_time, self.white_byo_yomi_periods)
        black_fg = (1, 0.8, 0, 1) if self.current_color == 0 else self.text_color
        white_fg = (1, 0.8, 0, 1) if self.current_color == 1 else self.text_color
        self.timer_text.setText(f"[Black: {black_display}]" if self.current_color == 0 else f"Black: {black_display}\n[White: {white_display}]" if self.current_color == 1 else f"Black: {black_display}\nWhite: {white_display}")
        self.timer_text['fg'] = black_fg if self.current_color == 0 else white_fg
        return task.cont

    def format_time(self, main_time, byo_yomi_time, byo_yomi_periods):
        if main_time > 0:
            minutes = int(main_time // 60)
            seconds = int(main_time % 60)
            return f"{minutes}:{seconds:02d}"
        else:
            seconds = int(byo_yomi_time)
            return f"{seconds} ({byo_yomi_periods})"

    def handle_timeout(self):
        print(f"Player {self.current_color} timed out!")
        winner = "Black" if self.current_color == 1 else "White"
        self.game_ended = True
        self.timer_text.setText(f"{winner} wins by timeout!")
        self.game_over_text.setText(f"Game Over! {winner} wins by timeout!")

    def update_timer_display(self):
        if self.timer_mode == "No timer":
            self.timer_text.setText(f"Black: NT\nWhite: NT")
            return
        black_display = self.format_time(self.black_time, self.black_byo_yomi_time, self.black_byo_yomi_periods)
        white_display = self.format_time(self.white_time, self.white_byo_yomi_time, self.white_byo_yomi_periods)
        self.timer_text.setText(f"Black: {black_display}\nWhite: {white_display}")

    def process_coordinates(self, input_text=None):
        if input_text is not None and not isinstance(input_text, str):
            text = self.coord_entry.get()
        else:
            text = self.coord_entry.get() if input_text is None else input_text

        try:
            coords = [int(x.strip()) for x in text.split(',')]
            if len(coords) != 3:
                return
            x, y, z = coords

            if not (0 <= x < self.size and 0 <= y < self.size and 0 <= z < self.size):
                return

            pos = (x, y, z)
            if pos in self.balls:
                return

            self.spawn_model(pos)
            self.coord_entry["focus"] = 0
        except ValueError:
            return

    def get_group(self, pos, color, visited=None, balls=None):
        if balls is None:
            balls = self.balls
        if visited is None:
            visited = set()
        if pos not in balls or balls[pos]['color'] != color or pos in visited:
            return set()
        group = set()
        to_check = [pos]
        while to_check:
            current = to_check.pop()
            if current in visited or current not in balls or balls[current]['color'] != color:
                continue
            visited.add(current)
            group.add(current)
            to_check.extend(self.get_adjacent_positions(current))
        return group

    def check_click(self):
        if not self.mouseWatcherNode.hasMouse():
            return
        mpos = self.mouseWatcherNode.getMouse()
        self.pickerRay.setFromLens(self.camNode, mpos.getX(), mpos.getY())
        self.cTrav.traverse(self.render)
        if self.pickerQueue.getNumEntries() > 0:
            self.pickerQueue.sortEntries()
            hit = self.pickerQueue.getEntry(0)
            vertex_node = hit.getIntoNodePath().getParent()
            pos = vertex_node.getPos(self.render)
            pos_tuple = (int(round(pos.x)), int(round(pos.y)), int(round(pos.z)))
            if not (0 <= pos_tuple[0] < self.size and 0 <= pos_tuple[1] < self.size and 0 <= pos_tuple[2] < self.size):
                return
            if pos_tuple in self.balls:
                return
            self.spawn_model(pos_tuple)

    def rewind(self):
        if self.history_index <= 0:
            print("Cannot rewind further - at the start of history")
            return
        self.history_index -= 1
        state = self.match_history[self.history_index]
        self.restore_state(state)
        self.allow_moves = (self.history_index == len(self.match_history) - 1)
        print(f"Rewound to state - Turn: {self.turn}, Color: {self.current_color}, History index: {self.history_index}")

    def redo(self):
        if self.history_index >= len(self.match_history) - 1:
            print("Cannot redo further - at the latest state")
            return
        self.history_index += 1
        state = self.match_history[self.history_index]
        self.restore_state(state)
        self.allow_moves = (self.history_index == len(self.match_history) - 1)
        print(f"Redone to state - Turn: {self.turn}, Color: {self.current_color}, History index: {self.history_index}")

    def restore_state(self, state):
        for pos in list(self.balls.keys()):
            self.balls[pos]['node'].removeNode()
        self.balls.clear()
        for pos, data in state['balls'].items():
            model = self.ball_model.copyTo(self.render)
            texture = self.black_texture if data['color'] == 0 else self.white_texture
            model.setTexture(texture, 1)
            model.setScale(0.49)
            model.setPos(pos[0], pos[1], pos[2])
            model.reparentTo(self.render)
            self.balls[pos] = {'node': model, 'color': data['color']}
        self.current_color = state['current_color']
        self.turn = state['turn']
        self.black_captures = state['black_captures']
        self.white_captures = state['white_captures']
        self.black_time = state.get('black_time', self.main_time)
        self.white_time = state.get('white_time', self.main_time)
        self.black_byo_yomi_time = state.get('black_byo_yomi_time', self.byo_time)
        self.white_byo_yomi_time = state.get('white_byo_yomi_time', self.byo_time)
        self.black_byo_yomi_periods = state.get('black_byo_yomi_periods', self.byo_periods)
        self.white_byo_yomi_periods = state.get('white_byo_yomi_periods', self.byo_periods)
        self.turn_text.setText(f"Turn: {self.turn}")
        self.text_captures.setText(f"Black captures: {self.black_captures}\nWhite captures: {self.white_captures}")
        black_display = self.format_time(self.black_time, self.black_byo_yomi_time, self.black_byo_yomi_periods)
        white_display = self.format_time(self.white_time, self.white_byo_yomi_time, self.white_byo_yomi_periods)
        self.timer_text.setText(f"Black: {black_display}\nWhite: {white_display}")
        self.pause_timer()

    def spawn_model(self, pos):
        if self.game_ended or not self.allow_moves:
            print("Move not allowed (game ended or rewound)")
            return
        pos_tuple = tuple(int(round(coord)) for coord in pos)
        if not self.is_legal_move(pos_tuple, self.current_color):
            return
        model = self.ball_model.copyTo(self.render)
        texture = self.black_texture if self.current_color == 0 else self.white_texture
        model.setTexture(texture, 1)
        model.setScale(0.49)
        model.setPos(pos[0], pos[1], pos[2])
        model.reparentTo(self.render)
        self.balls[pos_tuple] = {'node': model, 'color': self.current_color}

        if self.increment > 0:
            if self.current_color == 0:
                self.black_time += self.increment
            else:
                self.white_time += self.increment

        self.current_color = 1 - self.current_color
        self.turn += 1
        self.pass_count = 0

        board_hash = self.get_board_hash()
        state = {
            'balls': {k: {'color': v['color']} for k, v in self.balls.items()},
            'current_color': self.current_color,
            'turn': self.turn,
            'black_captures': self.black_captures,
            'white_captures': self.white_captures,
            'black_time': self.black_time,
            'white_time': self.white_time,
            'black_byo_yomi_time': self.black_byo_yomi_time,
            'white_byo_yomi_time': self.white_byo_yomi_time,
            'black_byo_yomi_periods': self.black_byo_yomi_periods,
            'white_byo_yomi_periods': self.white_byo_yomi_periods,
            'board_hash': board_hash
        }
        self.match_history.append(state)
        self.history_index = len(self.match_history) - 1

        self.check_all_groups_for_captures()
        self.turn_text.setText(f"Turn: {self.turn}")
        self.text_captures.setText(f"Black captures: {self.black_captures}\nWhite captures: {self.white_captures}")
        self.text_points.setText(f"Black points: {self.black_points}\nWhite points: {self.white_points}")
        if self.timer_mode != "No timer":
            self.pause_timer()
            self.start_timer()
            if self.current_color == 0:
                self.black_byo_yomi_time = self.byo_time
                self.black_byo_yomi_periods = self.byo_periods
            else:
                self.white_byo_yomi_time = self.byo_time
                self.white_byo_yomi_periods = self.byo_periods

    def check_all_groups_for_captures(self):
        print(f"Before captures - Turn: {self.turn}, balls: {self.balls.keys()}")
        visited = set()
        captured_groups = []
        for pos in list(self.balls.keys()):
            if pos not in visited:
                color = self.balls[pos]['color']
                group = self.get_group(pos, color, visited.copy())
                has_lib = self.group_has_liberty(group)
                if group and not has_lib:
                    captured_groups.append((group, color))
                visited.update(group)

        for group, color in captured_groups:
            if color == 0:
                self.white_captures += len(group)
            else:
                self.black_captures += len(group)
            self.remove_group(group)
        print(f"After captures - Turn: {self.turn}, balls: {self.balls.keys()}")

    def get_adjacent_positions(self, pos):
        x, y, z = pos
        adj = [
            (x + 1, y, z), (x - 1, y, z),
            (x, y + 1, z), (x, y - 1, z),
            (x, y, z + 1), (x, y, z - 1)
        ]
        return [(ax, ay, az) for ax, ay, az in adj if 0 <= ax < self.size and 0 <= ay < self.size and 0 <= az < self.size]

    def is_legal_move(self, pos, color):
        pos_tuple = tuple(int(round(coord)) for coord in pos)
        if pos_tuple in self.balls:
            print(f"Move rejected: {pos_tuple} is occupied")
            return False

        temp_balls = {k: v.copy() for k, v in self.balls.items()}
        temp_balls[pos_tuple] = {'color': color}
        opponent_color = 1 - color
        captured_positions = set()
        visited = set()
        for adj_pos in self.get_adjacent_positions(pos_tuple):
            if (adj_pos in temp_balls and temp_balls[adj_pos]['color'] == opponent_color and
                adj_pos not in visited):
                group = self.get_group(adj_pos, opponent_color, visited.copy(), temp_balls)
                has_lib = self.group_has_liberty(group, temp_balls)
                if group and not has_lib:
                    captured_positions.update(group)
                visited.update(group)

        for captured_pos in captured_positions:
            del temp_balls[captured_pos]

        visited = set()
        player_groups = []
        for ball_pos in temp_balls:
            if (ball_pos not in visited and temp_balls[ball_pos]['color'] == color):
                group = self.get_group(ball_pos, color, visited.copy(), temp_balls)
                player_groups.append(group)
                visited.update(group)

        for group in player_groups:
            has_lib = self.group_has_liberty(group, temp_balls)
            if not has_lib:
                return False

        if captured_positions:
            for captured_pos in captured_positions:
                if captured_pos in self.balls:
                    self.balls[captured_pos]['node'].removeNode()
                    del self.balls[captured_pos]

        board_hash = self.get_board_hash()
        if len(self.match_history) >= 2:
            prev_board_hash = self.match_history[-2].get('board_hash')
            if prev_board_hash == board_hash:
                for captured_pos in captured_positions:
                    if captured_pos not in self.balls:
                        model = self.ball_model.copyTo(self.render)
                        texture = self.black_texture if opponent_color == 0 else self.white_texture
                        model.setTexture(texture, 1)
                        model.setScale(0.49)
                        model.setPos(*captured_pos)
                        model.reparentTo(self.render)
                        self.balls[captured_pos] = {'node': model, 'color': opponent_color}
                return False

        return True

    def group_has_liberty(self, group, balls=None):
        if balls is None:
            balls = self.balls
        if not group:
            return False
        liberties = [adj_pos for pos in group for adj_pos in self.get_adjacent_positions(pos)
                    if adj_pos not in balls and adj_pos not in group]
        return bool(liberties)

    def remove_group(self, group):
        removed_count = 0
        for pos in group:
            if pos in self.balls:
                self.balls[pos]['node'].removeNode()
                del self.balls[pos]
                removed_count += 1
        print(f"Removed {removed_count} stones from group {group}")

    def reset_camera(self):
        center = Point3((self.size - 1) / 2, (self.size - 1) / 2, (self.size - 1) / 2)
        self.camera_control.center = center
        self.camera_control.update_camera_position()

    def change_camera_center(self):
        if self.mouseWatcherNode.hasMouse():
            mpos = self.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(self.camNode, mpos.getX(), mpos.getY())
            self.cTrav.traverse(self.render)
            if self.pickerQueue.getNumEntries() > 0:
                self.pickerQueue.sortEntries()
                hit = self.pickerQueue.getEntry(0)
                vertex_node = hit.getIntoNodePath().getParent()
                pos = vertex_node.getPos(self.render)
                self.camera_control.center = pos
                self.camera_control.update_camera_position()

    def show_nothing(self):
        for node in self.nodes:
            node.setScale(0.0)
        for ball_data in self.balls.values():
            ball_data['node'].setScale(0.0)
        for line_node in self.line_nodes:
            line_node.hide()

    def show_everything(self):
        if self.size == 1:
            return
        for node in self.nodes:
            node.setScale(1.0)
        for ball_data in self.balls.values():
            ball_data['node'].setScale(0.5)
        for line_node in self.line_nodes:
            line_node.show()
        self.current_plane -= 1

    def show_one_floor(self, current_z=None):
        if current_z is None:
            self.current_plane = (self.current_plane + 1) % self.size if hasattr(self, 'current_plane') else 0
            z = self.current_plane
        else:
            z = current_z
            if not (0 <= z < self.size):
                return

        for node in self.nodes:
            name_parts = node.getName().split('_')
            if len(name_parts) > 1:
                coords = name_parts[1].split(',')
                x, y, z_pos = [float(coord) for coord in coords]
                if int(z_pos) == z:
                    node.setScale(1.0)
                else:
                    node.setScale(0.0)

        for pos, ball_data in list(self.balls.items()):
            x, y, z_pos = pos
            if z_pos == z:
                ball_data['node'].setScale(0.5)
            else:
                ball_data['node'].setScale(0.0)

        for i, line_node in enumerate(self.line_nodes):
            if i == z:
                line_node.show()
            else:
                line_node.hide()

# Create and run the application
app = GridDemo(0)
app.run()