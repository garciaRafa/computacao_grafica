#version 330 core

layout(location = 0) in vec2 position;

void main()
{
    float x = position.x / 400.0 - 1.0;
    float y = position.y / 300.0 - 1.0;
    gl_Position = vec4(x, y, 0.0, 1.0);
}
