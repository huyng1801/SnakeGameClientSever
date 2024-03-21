import socket
import threading
import time
import random
import json
import math
class Snake:
    fruit_position = [random.randrange(1, (720//10)) * 10, 
                  random.randrange(1, (480//10)) * 10]
    fruit_spawn = True
    fruit_size = 10
    small_fruit_count = 0
    def __init__(self, player_num, initial_position):
        self.player_num = player_num
        self.player_name = ""
        self.position = initial_position
        self.body = [
            initial_position.copy(),
            [initial_position[0] - 3, initial_position[1]],
            [initial_position[0] - 6, initial_position[1]],
            [initial_position[0] - 9, initial_position[1]],
            [initial_position[0] - 12, initial_position[1]],
            [initial_position[0] - 15, initial_position[1]],
            [initial_position[0] - 18, initial_position[1]]

        ]
        self.direction = 'RIGHT'
        self.change_to = self.direction
        self.score = 0
        self.game_over = False
    @staticmethod
    def position_generate():
        return [random.randrange(1, (720//10)) * 10, 
                  random.randrange(1, (480//10)) * 10]
    def to_dict(self):
        return {
            'player_num': self.player_num, 
            'player_name': self.player_name,
            'snake_position': self.position,
            'snake_body': self.body,
            'direction': self.direction,
            'change_to': self.change_to,
            'score': self.score,
            'fruit_position': Snake.fruit_position,
            'fruit_size': Snake.fruit_size
        }
    def check_head_collision(self, other_snake):
        x1, y1 = self.position
        x2, y2 = other_snake.position
        return abs(x1 - x2) < 10 and abs(y1 - y2) < 10

    def check_body_collision(self, other_snake):
        for segment in other_snake.body:
            if abs(self.position[0] - segment[0]) < Snake.fruit_size and abs(self.position[1] - segment[1]) < Snake.fruit_size:
                return True
        return False

    def check_collision(self, other_snake):
        return self.check_head_collision(other_snake) or self.check_body_collision(other_snake)

    def handle_collision(self, other_snake):
        if self.check_head_collision(other_snake):
            if self.score < other_snake.score:
                other_snake.score += self.score
                other_snake.body.extend(other_snake.body)
                self.game_over = True
                send_to_client(self.player_num, 'GAME_OVER') 
            elif self.score > other_snake.score: 
                self.score += other_snake.score
                self.body.extend(other_snake.body)
                other_snake.game_over = True
                send_to_client(other_snake.player_num, 'GAME_OVER') 
            else:
                self.game_over = True
                send_to_client(self.player_num, 'GAME_OVER')
                other_snake.game_over = True
                send_to_client(other_snake.player_num, 'GAME_OVER') 
        elif self.check_body_collision(other_snake):
            self.game_over = True
            send_to_client(self.player_num, 'GAME_OVER')

    def reset(self):
        self.position = Snake.position_generate()
        self.body = [
            self.position.copy(),
            [self.position[0] - 3, self.position[1]],
            [self.position[0] - 6, self.position[1]],
            [self.position[0] - 9, self.position[1]],
            [self.position[0] - 12, self.position[1]],
            [self.position[0] - 15, self.position[1]],
            [self.position[0] - 18, self.position[1]]

        ]
        self.direction = 'RIGHT'
        self.change_to = self.direction
        self.score = 0
        self.game_over = False
# Cấu hình server
host = '127.0.0.1'
port = 9999

# Tạo server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(4)
print(f"Server is listening on {host}:{port}")

# Các biến toàn cục ở server
clients = {}
snakes = {}
window_x = 720
window_y = 480

def send_to_client(player_num, message):
    try:
        clients[player_num].send(message.encode('utf-8'))
    except:
        print(f"Error sending message to Player {player_num}")

def send_to_all_clients(message):
    for player_num in clients.keys():
        if player_num <= len(snakes.keys()) and not snakes[player_num].game_over:
            send_to_client(player_num, message) 


def handle_client(client, player_num):
    global clients, snakes
    while True:
        try:
            data = client.recv(1024).decode('utf-8')
            
            if not data:
                print(f"Player {player_num} disconnected")
                del clients[player_num]
                del snakes[player_num]
                client.close()
                break
            if "PLAYER_NAME" in data:
                
                player_name = data.split(":")[1]
                snakes[player_num] = Snake(player_num, Snake.position_generate())
                snakes[player_num].player_name = player_name
                
                
                send_initial_state(client, player_num)
                
            if "PLAY_AGAIN" == data:
                snakes[player_num].reset() 
            if data in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
             
                snakes[player_num].change_to = data
        except:
            continue


def update_game_state():
    global snakes

    while True:
        for player_num, snake in snakes.items():
            if not snake.game_over and snake.player_name != "":
                # di chuyển rắn
                direction = snake.direction
                change_to = snake.change_to
                snake_position = snake.position
                snake_body = snake.body
                fruit_position = snake.fruit_position
                score = snake.score

                if change_to == 'UP' and direction != 'DOWN':
                    direction = 'UP'
                elif change_to == 'DOWN' and direction != 'UP':
                    direction = 'DOWN'
                elif change_to == 'LEFT' and direction != 'RIGHT':
                    direction = 'LEFT'
                elif change_to == 'RIGHT' and direction != 'LEFT':
                    direction = 'RIGHT'

                # Cập nhật vị trí và hướng
                if direction == 'UP':
                    snake_position[1] -= 3
                elif direction == 'DOWN':
                    snake_position[1] += 3
                elif direction == 'LEFT':
                    snake_position[0] -= 3
                elif direction == 'RIGHT':
                    snake_position[0] += 3
            
                # Kiểm tra va chạm với tường của trò chơi
                if snake_position[0] < 0 or snake_position[0] >= window_x or snake_position[1] < 0 or snake_position[1] >= window_y:
                    # Thông báo game over đến người chơi
                    send_to_client(player_num, 'GAME_OVER')  # Notify the client about game over
                    snakes[player_num].game_over = True
                else:
                    # tăng kích thước rắn
                    snake_body.insert(0, snake_position.copy())
                    # kiểm tra khoảng cách đầu rắn và thức ăn
                    distance = math.sqrt((snake_position[0] - fruit_position[0]) ** 2 + (snake_position[1] - fruit_position[1]) ** 2)
                    
                    if distance < 10: 
                        
                        Snake.fruit_spawn = False
                        dx, dy = 0, 0
                        if direction == 'UP':
                            dy = -3
                        elif direction == 'DOWN':
                            dy = 3
                        elif direction == 'LEFT':
                            dx = -3
                        elif direction == 'RIGHT':
                            dx = 3
                        # thêm các đoạn cho rắn
                        for i in range(3):
                            new_segment = [snake_body[-1][0] + dx, snake_body[-1][1] + dy]
                            snake_body.append(new_segment)
                        Snake.small_fruit_count += 1
                        # Trường hợp thức ăn to
                        if Snake.small_fruit_count == 4:
                        
                            score += 50
                            Snake.fruit_position = Snake.position_generate()
                            Snake.fruit_size = 10
                            Snake.small_fruit_count = 0
                        else:
                            score += 10
                            Snake.fruit_position = Snake.position_generate()
                            
                            if Snake.small_fruit_count == 3:
                                Snake.fruit_size = 20
                            else:
                                Snake.fruit_size = 10
                    else:
                        snake_body.pop()

                    if not Snake.fruit_spawn:
                        Snake.fruit_position = Snake.position_generate()

                    Snake.fruit_spawn = True
                    # cập nhật thông tin của rắn
                    snake.position = snake_position
                    snake.body = snake_body
                    snake.fruit_position = Snake.fruit_position
                    snake.direction = direction
                    snake.score = score
                    for other_player_num, other_snake in snakes.items():
                        if player_num != other_player_num and snake.check_collision(other_snake):
                            # Xử lý va chạm của rắn
                            snake.handle_collision(other_snake)

        snakes_info = {
            'snakes': [json.dumps(snake.to_dict()) for player_num, snake in snakes.items() if (not snake.game_over and snake.player_name != "")]
        }
        if len(snakes_info["snakes"]) != 0:
            send_to_all_clients(json.dumps(snakes_info))

        # Khung hình
        time.sleep(0.016)


def send_initial_state(client, player_num):
    initial_state = {
        'player_num': player_num,
        'snake_position': snakes[player_num].position,
        'snake_body': snakes[player_num].body,
        'fruit_position': Snake.fruit_position,
        'score': snakes[player_num].score
    }
    client.send(json.dumps(initial_state).encode('utf-8'))

# Bắt đầu luồng để cập nhật trạng thái game liên tục
update_thread = threading.Thread(target=update_game_state)
update_thread.start()

while True:
    client, addr = server_socket.accept()
    print(f"Connection from {addr}")
    player_num = len(clients) + 1

    clients[player_num] = client
    
    
    thread = threading.Thread(target=handle_client, args=(client, player_num))
    thread.start()
