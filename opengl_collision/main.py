import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import math
import random

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

shapes = []

class Shape:
    def __init__(self, vertices, color, velocity):
        self.vertices = np.array(vertices, dtype=np.float32)
        self.color = color
        self.velocity = velocity
        self.vbo = glGenBuffers(1)
        self.vao = glGenVertexArrays(1)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_DYNAMIC_DRAW)

        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)

    def draw(self, shader):
        glUniform3f(glGetUniformLocation(shader, "inColor"), *self.color)
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLE_FAN, 0, len(self.vertices)//2)

    def update(self):
        dx, dy = self.velocity
        self.vertices[::2] += dx
        self.vertices[1::2] += dy

        # Bounce on window border
        if np.any(self.vertices[::2] < 0) or np.any(self.vertices[::2] > WINDOW_WIDTH):
            self.velocity = (-self.velocity[0], self.velocity[1])
        if np.any(self.vertices[1::2] < 0) or np.any(self.vertices[1::2] > WINDOW_HEIGHT):
            self.velocity = (self.velocity[0], -self.velocity[1])

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.vertices.nbytes, self.vertices)

def create_circle(x, y, radius=30, segments=36):
    vertices = [(x, y)]
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        vx = x + math.cos(angle) * radius
        vy = y + math.sin(angle) * radius
        vertices.append((vx, vy))
    flat = [coord for vertex in vertices for coord in vertex]
    return flat

def create_square(x, y, size=40):
    half = size / 2
    vertices = [
        x - half, y - half,
        x + half, y - half,
        x + half, y + half,
        x - half, y + half,
        x - half, y - half,
    ]
    return vertices

def main():
    if not glfw.init():
        return

    window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, "Pipeline Programável", None, None)
    if not window:
        glfw.terminate()
        return

    glfw.make_context_current(window)

    # Load shaders
    with open("vertex_shader.glsl") as f:
        vertex_shader = f.read()
    with open("fragment_shader.glsl") as f:
        fragment_shader = f.read()

    shader = OpenGL.GL.shaders.compileProgram(
        OpenGL.GL.shaders.compileShader(vertex_shader, GL_VERTEX_SHADER),
        OpenGL.GL.shaders.compileShader(fragment_shader, GL_FRAGMENT_SHADER)
    )

    glUseProgram(shader)

    # Criar algumas formas
    for _ in range(5):
        x, y = random.randint(100, 700), random.randint(100, 500)
        vel = (random.uniform(-2, 2), random.uniform(-2, 2))
        shape = Shape(create_circle(x, y), (1.0, 0.0, 0.0), vel)
        shapes.append(shape)

    for _ in range(5):
        x, y = random.randint(100, 700), random.randint(100, 500)
        vel = (random.uniform(-2, 2), random.uniform(-2, 2))
        shape = Shape(create_square(x, y), (0.0, 0.0, 1.0), vel)
        shapes.append(shape)

    # Loop principal
    while not glfw.window_should_close(window):
        glfw.poll_events()
        glClearColor(1, 1, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)

        for shape in shapes:
            shape.update()
            shape.draw(shader)

        glfw.swap_buffers(window)

    glfw.terminate()

if __name__ == "__main__":
    main()
