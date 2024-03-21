import pygame
import socket
import json
import threading
window_x = 720
window_y = 480

black = (0, 0, 0)
white = (255, 255, 255)
green = (0, 255, 0)
pygame.init()

game_window = pygame.display.set_mode((window_x, window_y))
pygame.display.set_caption('Multiplayer Snake Game')

fps = pygame.time.Clock()
font = pygame.font.SysFont('times new roman', 20)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 9999))


def draw_name_input(name_input, name_rect, submit_rect):
    pygame.draw.rect(game_window, white, name_rect)
    pygame.draw.rect(game_window, white, submit_rect)
    name_surface = font.render(name_input, True, black)
    game_window.blit(name_surface, (name_rect.x + 10, name_rect.y + 5))

    submit_surface = font.render("Submit", True, black)
    game_window.blit(submit_surface, (submit_rect.x + 10, submit_rect.y + 5))

    pygame.display.update()

name_input = ""
name_rect = pygame.Rect(250, 200, 200, 30)
submit_rect = pygame.Rect(250, 250, 100, 30)
submit_clicked = False

def name_input_thread():
    global name_input
    global submit_clicked
    while not submit_clicked:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    submit_clicked = True
                elif event.key == pygame.K_BACKSPACE:
                    name_input = name_input[:-1]
                else:
                    name_input += event.unicode

        draw_name_input(name_input, name_rect, submit_rect)
        pygame.time.delay(10)  # Add a small delay to avoid high CPU usage

name_input_thread()
name_input = "PLAYER_NAME:" + name_input
client.send(name_input.encode('utf-8')) 

initial_state_str = client.recv(1024).decode('utf-8')
initial_state = json.loads(initial_state_str)
player_num = initial_state['player_num']
snake_position = initial_state['snake_position']
snake_body = initial_state['snake_body']
fruit_position = initial_state['fruit_position']
score = initial_state['score']

def draw_game(snake_info):
    game_window.fill(black)
    print(snake_info)
    try:
        snake_info = json.loads(snake_info)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return

    all_snakes = snake_info.get('snakes', [])

    # Định nghĩa thuộc tính trên bảng điểm
    score_table_x = 10
    score_table_y = 10
    score_table_spacing = 20

    for index, snake_data in enumerate(all_snakes):
        snake_data = json.loads(snake_data)
        current_player_num = snake_data['player_num']
        current_snake_body = snake_data['snake_body']
        current_player_name = snake_data['player_name']
        current_score = snake_data['score']
        current_fruit_position = snake_data['fruit_position']
        current_fruit_size = snake_data.get('fruit_size', 10)  # Kích cỡ thức ăn mặc định là 10

        if current_player_num == player_num:
            snake_head_color = pygame.Color('red')
            snake_body_color = pygame.Color('green')
            score_surface = font.render(f'{current_player_name}: {current_score}', True, green)
            score_rect = score_surface.get_rect()
            score_rect.topleft = (score_table_x, score_table_y + index * score_table_spacing)
        else:
            snake_head_color = pygame.Color('blue')
            snake_body_color = pygame.Color('lightblue')
            score_surface = font.render(f'{current_player_name}: {current_score}', True, white)
            score_rect = score_surface.get_rect()
            score_rect.topleft = (score_table_x, score_table_y + index * score_table_spacing)

        # Vẽ đầu và thân rắn
        

        for pos in current_snake_body[1:]:
            pygame.draw.rect(game_window, snake_body_color, pygame.Rect(pos[0], pos[1], 10, 10))
        pygame.draw.rect(game_window, snake_head_color, pygame.Rect(current_snake_body[0][0], current_snake_body[0][1], 10, 10))
        # Vẽ thức ăn
        fruit_radius = current_fruit_size // 2
        pygame.draw.circle(game_window, pygame.Color('white'), (current_fruit_position[0] + fruit_radius, current_fruit_position[1] + fruit_radius), fruit_radius)

        game_window.blit(score_surface, score_rect)

    pygame.display.update()





def send_player_input():
    while True:
        keys = pygame.key.get_pressed()
        
        if pygame.event.get(pygame.QUIT) or pygame.key.get_pressed()[pygame.K_ESCAPE]:
            break
        if keys[pygame.K_UP]:
            client.send('UP'.encode('utf-8'))
        elif keys[pygame.K_DOWN]:
            client.send('DOWN'.encode('utf-8'))
        elif keys[pygame.K_LEFT]:
            client.send('LEFT'.encode('utf-8'))
        elif keys[pygame.K_RIGHT]:
            client.send('RIGHT'.encode('utf-8'))
        fps.tick(1000)


input_thread = threading.Thread(target=send_player_input)
input_thread.start()

# Hàm hiển thị game over
def show_game_over_screen():
    game_window.fill(black)
    game_over_font = pygame.font.SysFont('times new roman', 50)
    game_over_surface = game_over_font.render('Game Over', True, white)
    game_over_rect = game_over_surface.get_rect(center=(window_x / 2, window_y / 2 - 50))
    game_window.blit(game_over_surface, game_over_rect)

    play_again_font = pygame.font.SysFont('times new roman', 30)
    play_again_surface = play_again_font.render('Press R to Play Again', True, white)
    play_again_rect = play_again_surface.get_rect(center=(window_x / 2, window_y / 2 + 50))
    game_window.blit(play_again_surface, play_again_rect)

    pygame.display.update()

    # chờ đến khi nhấn phím R
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                # Send a play-again signal to the server
                client.send("PLAY_AGAIN".encode('utf-8'))
                return
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()


# Thực hiện vòng lặp để lấy dữ liệu cập nhật cho game
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

    snake_info = client.recv(1024).decode('utf-8')
    if snake_info == "GAME_OVER":
        show_game_over_screen()
    elif name_input != "":
        draw_game(snake_info)

