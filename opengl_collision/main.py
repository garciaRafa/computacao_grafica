import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import math
import random

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
SPEED_SCALE = 0.2
FORCE_SCALE = 0.05

shapes = []
shader = None
resolution_location = None


class Shape:
    def __init__(self, vertices, color, velocity, shape_type, w=0, h=0):
        self.type = shape_type  # 'circle' ou 'rectangle'
        self.vertices = np.array(vertices, dtype=np.float32)
        self.color = color
        self.velocity = np.array(velocity, dtype=np.float32) * SPEED_SCALE
        self.w = w
        self.h = h
        self.radius = 0

        self.vbo = glGenBuffers(1)
        self.vao = glGenVertexArrays(1)

        self.update_position()

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_DYNAMIC_DRAW)

        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)

    def update_position(self):
        self.x = np.mean(self.vertices[::2])
        self.y = np.mean(self.vertices[1::2])
        if self.type == 'circle':
            self.radius = max(math.hypot(self.x - vx, self.y - vy)
                              for vx, vy in zip(self.vertices[::2], self.vertices[1::2]))

    def update(self):
        self.vertices[::2] += self.velocity[0]
        self.vertices[1::2] += self.velocity[1]

        self.update_position()

        if np.any(self.vertices[::2] < 0) or np.any(self.vertices[::2] > WINDOW_WIDTH):
            self.velocity[0] *= -1
        if np.any(self.vertices[1::2] < 0) or np.any(self.vertices[1::2] > WINDOW_HEIGHT):
            self.velocity[1] *= -1

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.vertices.nbytes, self.vertices)

    def draw(self):
        glUniform3f(glGetUniformLocation(shader, "inColor"), *self.color)
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLE_FAN, 0, len(self.vertices) // 2)


def create_circle(x, y, radius=30, segments=36):
    verts = [(x, y)]
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        verts.append((x + math.cos(angle) * radius, y + math.sin(angle) * radius))
    return [coord for v in verts for coord in v]


def create_rectangle(x, y, w, h):
    half_w, half_h = w / 2, h / 2
    verts = [
        x - half_w, y - half_h,
        x + half_w, y - half_h,
        x + half_w, y + half_h,
        x - half_w, y + half_h,
        x - half_w, y - half_h
    ]
    return verts


def collide(a, b):
    if a.type == b.type == 'circle':
        dist = math.hypot(a.x - b.x, a.y - b.y)
        return dist < a.radius + b.radius
    elif a.type == b.type == 'rectangle':
        return not (
            a.x + a.w / 2 < b.x - b.w / 2 or a.x - a.w / 2 > b.x + b.w / 2 or
            a.y + a.h / 2 < b.y - b.h / 2 or a.y - a.h / 2 > b.y + b.h / 2
        )
    elif a.type == 'circle' and b.type == 'rectangle':
        return collide_circle_rect(a, b)
    elif a.type == 'rectangle' and b.type == 'circle':
        return collide_circle_rect(b, a)
    return False


def collide_circle_rect(circle, rect):
    closest_x = max(rect.x - rect.w / 2, min(circle.x, rect.x + rect.w / 2))
    closest_y = max(rect.y - rect.h / 2, min(circle.y, rect.y + rect.h / 2))
    dx = circle.x - closest_x
    dy = circle.y - closest_y
    return dx * dx + dy * dy < circle.radius ** 2


def repel(a, b):
    dx, dy = a.x - b.x, a.y - b.y
    dist = math.hypot(dx, dy)
    if dist == 0:
        dx, dy = random.uniform(-1, 1), random.uniform(-1, 1)
        dist = 1
    force = FORCE_SCALE
    impulse = np.array([(dx / dist) * force, (dy / dist) * force])
    a.velocity += impulse
    b.velocity -= impulse  # Simétrico


def mouse_button_callback(win, button, action, mods):
    if action == glfw.PRESS:
        x, y = glfw.get_cursor_pos(win)
        fb_w, fb_h = glfw.get_framebuffer_size(win)
        x = x * WINDOW_WIDTH / fb_w
        y = WINDOW_HEIGHT - y * WINDOW_HEIGHT / fb_h

        if button == glfw.MOUSE_BUTTON_LEFT:
            shapes.append(Shape(create_circle(x, y), (1, 0, 0), (random.uniform(-1, 1), random.uniform(-1, 1)), 'circle'))
        elif button == glfw.MOUSE_BUTTON_RIGHT:
            w, h = random.randint(30, 70), random.randint(30, 70)
            shapes.append(Shape(create_rectangle(x, y, w, h), (0, 0, 1), (random.uniform(-1, 1), random.uniform(-1, 1)), 'rectangle', w, h))


def framebuffer_size_callback(win, width, height):
    global WINDOW_WIDTH, WINDOW_HEIGHT
    WINDOW_WIDTH, WINDOW_HEIGHT = width, height
    glViewport(0, 0, width, height)


def main():
    global shader, resolution_location

    if not glfw.init():
        return

    window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, "Simulação Melhorada", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)
    glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)
    glfw.set_mouse_button_callback(window, mouse_button_callback)

    with open("vertex_shader.glsl") as f:
        vertex = f.read()
    with open("fragment_shader.glsl") as f:
        fragment = f.read()

    shader = OpenGL.GL.shaders.compileProgram(
        OpenGL.GL.shaders.compileShader(vertex, GL_VERTEX_SHADER),
        OpenGL.GL.shaders.compileShader(fragment, GL_FRAGMENT_SHADER)
    )
    glUseProgram(shader)

    resolution_location = glGetUniformLocation(shader, "resolution")
    glUniform2f(resolution_location, WINDOW_WIDTH, WINDOW_HEIGHT)

    for _ in range(5):
        x, y = random.randint(100, 700), random.randint(100, 500)
        shapes.append(Shape(create_circle(x, y), (1, 0, 0), (random.uniform(-1, 1), random.uniform(-1, 1)), 'circle'))

    for _ in range(5):
        x, y = random.randint(100, 700), random.randint(100, 500)
        w, h = random.randint(40, 70), random.randint(40, 70)
        shapes.append(Shape(create_rectangle(x, y, w, h), (0, 0, 1), (random.uniform(-1, 1), random.uniform(-1, 1)), 'rectangle', w, h))

    while not glfw.window_should_close(window):
        glfw.poll_events()
        glClearColor(1, 1, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)

        glUniform2f(resolution_location, WINDOW_WIDTH, WINDOW_HEIGHT)

        for shape in shapes:
            shape.update()
            shape.draw()

        for i in range(len(shapes)):
            for j in range(i + 1, len(shapes)):
                if collide(shapes[i], shapes[j]):
                    repel(shapes[i], shapes[j])

        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
