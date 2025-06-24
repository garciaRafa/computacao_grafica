#version 330 core
layout(location = 0) in vec2 position;
uniform vec2 resolution;

void main() {
    vec2 normPos = position / resolution * 2.0 - 1.0;
    normPos.y *= -1.0;
    gl_Position = vec4(normPos, 0.0, 1.0);
}
