import threading
import random
import json
import time

class SnakeGame(threading.Thread):
    def __init__(self, width, height):
        threading.Thread.__init__(self)
        self.running = False
        self.snakes = []
        self.requests = []
        self.fruit = { 'x' : width/2, 'y' : height/2 }
        self.lock = threading.Lock()
        self.width = width
        self.height = height
        self.speed = 2;

        self.grid = []
        for i in range(0, self.width):
            self.grid.append([])
            for j in range(0, self.height):
                self.grid[i].append(-1)

        random.seed(2484901358)

    @staticmethod
    def opp_dir(dir):
        out = { 'dx' : 0, 'dy' : 0 }
        dx = dir['dx']
        dy = dir['dy']
        if dx != 0:
            out['dx'] = -dir['dx']
        if dy != 0:
            out['dy'] = -dir['dy']
        return out

    @staticmethod
    def dir_to_char(dir):
        dx = dir['dx']
        dy = dir['dy']
        if dx == 1:
            return 'r'
        elif dx == -1:
            return 'l'
        elif dy == 1:
            return 'd'
        elif dy == -1:
            return 'u'
        else:
            return ""

    @staticmethod
    def char_to_dir(ch):
        dx = 0
        dy = 0
        if ch == 'r':
            dx = 1
        elif ch == 'l':
            dx = -1
        elif ch == 'u':
            dy = -1
        elif ch == 'd':
            dy = 1
        return { 'dx' : dx, 'dy' : dy }

    def move_by_dir(self, p, d):
        return { 'x' : (p['x'] + d['dx'])%self.width, 'y' : (p['y'] + d['dy'])%self.height }

    def follow_tail(self, s):
        head = { 'x' : s['head']['x'], 'y' : s['head']['y'] }
        for i in range(0, len(s['tail'])):
            head = self.move_by_dir(head, SnakeGame.char_to_dir(s['tail'][i]))
        return head

    def new_fruit(self):
        self.fruit = {'x' : random.randint(0, self.width - 1), 'y' : random.randint(0, self.height - 1) }

    def move_snake(self, s):
        #FIXME order of movement matters (who dies)
        out = {'status': s['status'], 'score' : s['score'], 'id': s['id'], 'head' : {'x': -1, 'y': -1}, 'dir' : {'dx': s['dir']['dx'], 'dy': s['dir']['dy']}, 'tail' : ""}

        x = s['head']['x']
        y = s['head']['y']

        tail = self.follow_tail(s)
        self.grid[tail['x']][tail['y']] = -1

        x = out['head']['x'] = (x + s['dir']['dx']) % self.width
        y = out['head']['y'] = (y + s['dir']['dy']) % self.height
        if self.grid[x][y] != -1:
            print 'snake(', s['id'], ') died'
            out['status'] = 'dead'
            for i in range(0, self.width):
                for j in range(0, self.height):
                    if self.grid[x][y] == s['id']:
                        self.grid[x][y] = -1
            return out
        else:
            self.grid[x][y] = s['id']
            out['tail'] = SnakeGame.dir_to_char(SnakeGame.opp_dir(s['dir'])) + s['tail']

            if x == self.fruit['x'] and y == self.fruit['y']:
                self.grid[tail['x']][tail['y']] = s['id']
                print 'snake(', s['id'], ') scores!'
                out['score'] = s['score'] + 1
                self.new_fruit()
            else:
                out['tail'] = out['tail'][:-1]

        return out

    def run(self):
        self.running = True
        while self.running:
            start = time.time()

            out = []
            for snake in self.snakes:
                if snake['status'] == 'alive':
                    out.append(self.move_snake(snake))
                else:
                    out.append(snake)
            self.snakes = out
            for request in self.requests:
                tosend = json.dumps({'game': self.get_state()})
                request.ws_stream.send_message(tosend)
                
            end = time.time()
            if ((1.0/self.speed) - (end-start)) > 0:
                time.sleep((1.0/self.speed)-(end-start))

    def is_running(self):
        return self.running

    def acquire_lock(self):
        self.lock.acquire()

    def release_lock(self):
        self.lock.release()

    def add_player(self, request):
        id = len(self.requests)
        self.requests.append(request)
        self.snakes.append({'status': 'dead', 'score' : 0, 'id': id, 'head' : {'x': -1, 'y': -1}, 'dir' : {'dx': 0, 'dy': 0}, 'tail' : ""})
        return id

    def connect_player(self, id):
        if id >= len(self.snakes) or id < 0:
            return
        self.snakes[id]['head']['x'] = random.randint(0, self.width - 1)
        self.snakes[id]['head']['y'] = random.randint(0, self.height - 1)
        # TODO: check for collision right now
        self.snakes[id]['status'] = 'alive'

    def get_state(self):
        return { 'fruit' : self.fruit, 'snakes' : self.snakes, 'width' : self.width, 'height' : self.height }

    @staticmethod
    def is_bad_dir(dir):
        dx = dir['dx']
        dy = dir['dy']
        if dx > 1 or dx < -1 or dy > 1 or dy < -1:
            return True
        return False

    def set_direction_player(self, id, dir):
        dx = dir['dx']
        dy = dir['dy']
        if id >= len(self.snakes) or id < 0:
            return
        if SnakeGame.is_bad_dir(dir):
            return
        # FIXME this should be atomic w.r.t. sending data
        self.snakes[id]['dir']['dx'] = dx
        self.snakes[id]['dir']['dy'] = dy
        

def web_socket_do_extra_handshake(request):
    pass  # Always accept.

game = SnakeGame(15, 15)
def web_socket_transfer_data(request):
    global game
    id = 0

    game.acquire_lock()
    if game.is_running() == False:
        game.start()
    id = game.add_player(request)
    game.release_lock()

    while True:
        message = request.ws_stream.receive_message()
        if message is None:
            return
        print 'got msg: ', message
        if message == "connect":
            game.connect_player(id)
            tosend = json.dumps({'your_id': id, 'game': game.get_state()});
            request.ws_stream.send_message(tosend)
        else:
        # TODO: json verification
            packet = json.loads(message)
            game.set_direction_player(id, packet)
