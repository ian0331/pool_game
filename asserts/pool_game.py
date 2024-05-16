# -*- coding:utf-8 -*-
"""
作者:Yukio
日期:2024年05月13日
"""
import pygame
import pymunk
import pymunk.pygame_util
import math

pygame.init()
#定义游戏变量
lives =3
dia = 36
pocket_dia = 66
taking_shot = True
FPS = 120
game_running = True
cue_ball_potted = False
powering_up = False
potted_ball = False
potted_balls = []

#定义颜色
BG = (50, 50, 50)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

#定义字体
font = pygame.font.SysFont("microsoftsansserif", 30)
large_font = pygame.font.SysFont("microsoftsansserif", 100)
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 672
BOTTOM_PAMEL = 50

#游戏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT + BOTTOM_PAMEL))
pygame.display.set_caption("台球游戏")
#pymunk空间
space = pymunk.Space()
# 创建静态体
static_body = space.static_body
draw_options = pymunk.pygame_util.DrawOptions(screen)#把space画到屏幕上
#时钟
clock = pygame.time.Clock()
#加载图片
table_image = pygame.image.load("asserts/images/table.png").convert_alpha()
cue_image = pygame.image.load("asserts/images/cue.png").convert_alpha()
ball_images = []
for i in range(1, 17):
    ball_image = pygame.image.load(f"asserts/images/ball_{i}.png").convert_alpha()
    ball_images.append(ball_image)

#绘制文本
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

#创建球杆类
class Cue():
    def __init__(self, pos):
        self.original = cue_image
        self.angle = 0
        self.image = pygame.transform.rotate(self.original, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.force = 0#力量
        self.max_force = 10000#最大力量
        self.force_direction = 1#力量方向
        self.power_bar = pygame.Surface((10, 30))#力量条
        self.power_bar.fill(RED)

    def update(self, angle, powering_up):
        self.angle = angle
        if powering_up:
            self.force += 100 * self.force_direction
            if self.force >= self.max_force:
                self.force = self.max_force
            elif self.force <= 0:
                self.force = 0
                self.force_direction *= -1

    def draw(self, surface):
        #绘制球杆
        self.image = pygame.transform.rotate(self.original, self.angle)
        surface.blit(self.image, (self.rect.centerx - self.image.get_width() / 2, self.rect.centery - self.image.get_height() / 2))
        #绘制力量条
        if powering_up:
            for b in range(math.ceil(self.force / 1500)):
                surface.blit(self.power_bar, (self.rect.centerx - 30 + (b * 15), self.rect.centery + 30))

    def update_position_and_angle(self, ball_position, mouse_pos):
        #更新球杆的位置和角度
        self.rect.center = ball_position
        x_dist = ball_position[0] - mouse_pos[0]
        y_dist = -(ball_position[1] - mouse_pos[1])
        self.angle = math.degrees(math.atan2(y_dist, x_dist))
        self.update(self.angle, powering_up)

    def power_up(self):
        """增加力量条，更平滑地处理力量值的增减"""
        increment = 100  # 可以根据需要调整这个值
        if self.force_direction > 0:
            if self.force + increment > self.max_force:
                self.force = self.max_force
                self.force_direction = -1
            else:
                self.force += increment
        else:
            if self.force - increment < 0:
                self.force = 0
                self.force_direction = 1
            else:
                self.force -= increment

    def apply_impulse(self, cue_ball):
        """对母球施加冲击力"""
        x_impulse = math.cos(math.radians(self.angle))
        y_impulse = math.sin(math.radians(self.angle))
        cue_ball.body.apply_impulse_at_local_point((self.force * -x_impulse, self.force * y_impulse), (0, 0))
        self.force = 0
        self.force_direction = 1

    def reset_force(self):
        """重置力量和方向"""
        self.force = 0
        self.force_direction = 1
#创建球类
class Ball():
    def __init__(self, image, radius, pos):
        self.image = image
        self.radius = radius
        self.body = pymunk.Body()
        self.body.position = pos
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.mass = 5
        self.shape.elasticity = 0.8
        pivot = pymunk.PivotJoint(static_body, self.body, (0, 0), (0, 0))
        pivot.max_bias = 0
        pivot.max_force = 100
        space.add(self.body, self.shape, pivot)

    def is_potted(self, pocket, pocket_dia):
        """检查球是否进入指定的球袋"""
        ball_x_dist = abs(self.body.position[0] - pocket[0])
        ball_y_dist = abs(self.body.position[1] - pocket[1])
        ball_dist = math.sqrt((ball_x_dist ** 2) + (ball_y_dist ** 2))
        return ball_dist <= pocket_dia / 2

    def reset_position(self, position):
        """重置球的位置"""
        self.body.position = position
        self.body.velocity = (0.0, 0.0)

    def is_stationary(self):
        """检查球是否静止"""
        return int(self.body.velocity[0]) == 0 and int(self.body.velocity[1]) == 0

    def draw(self, surface):
        """绘制球体"""
        surface.blit(self.image, (self.body.position[0] - self.radius, self.body.position[1] - self.radius))
#创建台球桌类
class Table:
    def __init__(self, image, pockets, cushions):
        self.image = image
        self.pockets = pockets
        self.cushions = cushions
        self.create_cushions()

    def draw(self, surface):
        surface.blit(self.image, (0, 0))
        
    #创建缓冲函数
    def create_cushion(self, poly_dims):
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = ((0, 0))
        shape = pymunk.Poly(body, poly_dims)
        shape.elasticity = 0.8  # 给缓冲垫添加弹性
        space.add(body, shape)
    #创建缓冲垫
    def create_cushions(self):
        for c in self.cushions:
            self.create_cushion(c)


#创建初始游戏球体
balls = []
rows = 5
i=1
for col in range(5):
    for row in range(rows):
        pos = (250 + (col * (dia + 1)), 267 + (row * (dia + 1)) + (col * dia)/ 2)
        new_ball = Ball(image = ball_images[i-1],radius= dia / 2, pos = pos)
        balls.append(new_ball)
        i += 1
    rows -= 1

#创建初始母球
pos = (888, SCREEN_HEIGHT / 2)
cue_ball = Ball(image= ball_images[15], radius= dia / 2, pos= pos)
balls.append(cue_ball)

# 创建球杆
cue = Cue((balls[-1].body.position.x, balls[-1].body.position.y))

#创建球洞
pockets = [
    (35, 34),
    (599, 34),
    (1163, 34),
    (35, 632),
    (599, 632),
    (1163, 632)
]

#创建台球缓冲区域
cushions = [[(55, 32),(86, 55),(536, 55),(562, 32)],
            [(631, 32), (1138, 32), (658, 55), (1109, 55)],
            [(31,62), (54,91), (31,603), (54,576)],
            [(1166, 63), (1143, 91), (1143, 576), (1166, 603)],
            [(84, 613), (56, 636), (537, 613), (565, 635)],
            [(658, 613), (630, 636), (1111, 613), (1139, 636)]]

#创建台球桌
table = Table(table_image, pockets, cushions)
#画底部面板
pygame.draw.rect(screen, BG, (0, SCREEN_HEIGHT, SCREEN_WIDTH, BOTTOM_PAMEL))
#游戏循环
run = True
while run:
    clock.tick(FPS)
    space.step(1/FPS)
    screen.fill(BG)  # 填充背景色
    table.draw(screen)  # 绘制台球桌

    # 判断是否进球
    balls_to_remove = []
    for ball in balls:
        for pocket in pockets:
            if ball.is_potted(pocket, pocket_dia):
                if ball == cue_ball:
                    lives -= 1
                    cue_ball_potted = True
                    ball.reset_position((-100, -100))  # 暂时移除母球
                else:
                    space.remove(ball.body)
                    balls_to_remove.append(ball)
                    potted_balls.append(ball.image)

    for ball in balls_to_remove: # 确保同时移除物理体和形状
        balls.remove(ball)
    # 绘制球体
    for ball in balls:
        ball.draw(screen)
    # 如果所有球静止，允许击球
    if all(ball.is_stationary() for ball in balls):
        taking_shot = True
    else:
        taking_shot = False

    # 重新定位球杆
    if taking_shot and game_running:
        if cue_ball_potted:
            cue_ball.reset_position((888, SCREEN_HEIGHT / 2))
            cue_ball_potted = False

        mouse_pos = pygame.mouse.get_pos()
        cue.update_position_and_angle(balls[-1].body.position, mouse_pos)
        cue.draw(screen)

    # 台球杆蓄力
    if powering_up and game_running:
        cue.power_up()

    elif not powering_up and taking_shot:
        cue.apply_impulse(cue_ball)
        cue.reset_force()


    #绘制生命值
    draw_text(f"Lives: {lives}", font, RED, SCREEN_WIDTH - 200, SCREEN_HEIGHT + 10)
    #画进入球洞的球体
    for i, ball in enumerate(potted_balls):
        screen.blit(ball, (10 + (i * 50), SCREEN_HEIGHT + 10))
     #检查游戏是否结束
    if lives <= 0:
        draw_text("Game Over!", large_font, WHITE, SCREEN_WIDTH / 2 - 200, SCREEN_HEIGHT / 2 - 60)
        game_running = False
    # 检查所有的球体是否都进了球洞
    if len(balls) == 1:
        draw_text("You Won!", large_font, WHITE, SCREEN_WIDTH / 2 - 160, SCREEN_HEIGHT / 2 - 100)
        game_running = False

    # 事件处理器
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN and taking_shot:
            powering_up = True
        if event.type == pygame.MOUSEBUTTONUP and taking_shot:
            powering_up = False
        if event.type == pygame.QUIT:
            run = False
            pygame.quit()
            exit()

    pygame.display.update()