import pygame
import numpy as np
import math
import sys
from datetime import datetime


class Camera:
    def __init__(self):
        self.position = np.array([-4.0, 3.0, 2.0])

        self.rot_x = 0.0
        self.rot_y = math.radians(90.0)
        self.rot_z = 0.0

        self.orientation = (
            self._rotation_matrix_x(self.rot_x)
            @ self._rotation_matrix_y(self.rot_y)
            @ self._rotation_matrix_z(self.rot_z)
        )

        self.focal_length = 500.0

    def get_view_matrix(self):
        return self.orientation.T

    def transform_vertex(self, vertex):
        v = vertex - self.position
        v = self.orientation.T @ v
        return v

    def project_vertex(self, vertex_3d):
        x, y, z = vertex_3d

        if z <= 0.1:
            return None

        screen_x = (x / z) * self.focal_length
        screen_y = (y / z) * self.focal_length

        return (screen_x, screen_y)

    def move_forward(self, distance):
        direction = self._get_forward_direction()
        self.position += direction * distance

    def move_backward(self, distance):
        direction = self._get_forward_direction()
        self.position -= direction * distance

    def move_left(self, distance):
        direction = self._get_right_direction()
        self.position -= direction * distance

    def move_right(self, distance):
        direction = self._get_right_direction()
        self.position += direction * distance

    def move_up(self, distance):
        direction = self._get_up_direction()
        self.position += direction * distance

    def move_down(self, distance):
        direction = self._get_up_direction()
        self.position -= direction * distance

    def _get_forward_direction(self):
        return self.orientation @ np.array([0, 0, -1])

    def _get_right_direction(self):
        return self.orientation @ np.array([1, 0, 0])

    def _get_up_direction(self):
        return self.orientation @ np.array([0, 1, 0])

    def rotate_x(self, angle):
        self.rot_x += angle
        self.orientation = self.orientation @ self._rotation_matrix_x(angle)

    def rotate_y(self, angle):
        self.rot_y += angle
        self.orientation = self.orientation @ self._rotation_matrix_y(angle)

    def rotate_z(self, angle):
        self.rot_z += angle
        self.orientation = self.orientation @ self._rotation_matrix_z(angle)

    def _rotation_matrix_x(self, angle):
        return np.array([
            [1, 0, 0],
            [0, math.cos(angle), -math.sin(angle)],
            [0, math.sin(angle), math.cos(angle)]
        ])

    def _rotation_matrix_y(self, angle):
        return np.array([
            [math.cos(angle), 0, math.sin(angle)],
            [0, 1, 0],
            [-math.sin(angle), 0, math.cos(angle)]
        ])

    def _rotation_matrix_z(self, angle):
        return np.array([
            [math.cos(angle), -math.sin(angle), 0],
            [math.sin(angle), math.cos(angle), 0],
            [0, 0, 1]
        ])

    def zoom_in(self, factor):
        self.focal_length *= factor

    def zoom_out(self, factor):
        self.focal_length /= factor


class Cuboid:
    def __init__(self, vertices):
        self.vertices = [np.array(v, dtype=float) for v in vertices]
        self.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]

    def project_vertices(self, camera):
        projected = []
        for vertex in self.vertices:
            v_camera = camera.transform_vertex(vertex)
            v_2d = camera.project_vertex(v_camera)
            projected.append(v_2d)
        return projected


def load_cuboids(filename):
    cuboids = []
    with open(filename, 'r') as f:
        n = int(f.readline().strip())
        for _ in range(n):
            vertices = []
            for _ in range(8):
                coords = list(map(float, f.readline().strip().split()))
                vertices.append(coords)
            cuboids.append(Cuboid(vertices))
    return cuboids


def main():
    pygame.init()

    WIDTH, HEIGHT = 1200, 900
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Grafika Komputerowa - Wirtualna Kamera")
    clock = pygame.time.Clock()

    camera = Camera()
    cuboids = load_cuboids('cuboids.txt')

    move_speed = 0.1
    rotation_speed = 0.025
    zoom_factor = 1.05

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_l:
                    save_screenshot(screen)

        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            camera.move_backward(move_speed)
        if keys[pygame.K_s]:
            camera.move_forward(move_speed)
        if keys[pygame.K_a]:
            camera.move_left(move_speed)
        if keys[pygame.K_d]:
            camera.move_right(move_speed)

        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            camera.move_down(move_speed)
        if keys[pygame.K_SPACE]:
            camera.move_up(move_speed)

        if keys[pygame.K_UP]:
            camera.rotate_x(-rotation_speed)
        if keys[pygame.K_DOWN]:
            camera.rotate_x(rotation_speed)
        if keys[pygame.K_LEFT]:
            camera.rotate_y(-rotation_speed)
        if keys[pygame.K_RIGHT]:
            camera.rotate_y(rotation_speed)

        if keys[pygame.K_q]:
            camera.rotate_z(rotation_speed)
        if keys[pygame.K_e]:
            camera.rotate_z(-rotation_speed)

        if keys[pygame.K_h]:
            camera.zoom_in(zoom_factor)
        if keys[pygame.K_j]:
            camera.zoom_out(zoom_factor)

        screen.fill((20, 20, 30))

        for cuboid in cuboids:
            projected = cuboid.project_vertices(camera)
            draw_cuboid(screen, projected, cuboid.edges, WIDTH, HEIGHT)

        font = pygame.font.Font(None, 24)
        info_text = [
            f"Pos: ({camera.position[0]:.2f}, {camera.position[1]:.2f}, {camera.position[2]:.2f})",
            f"Rot: X={math.degrees(camera.rot_x):.1f}° Y={math.degrees(camera.rot_y):.1f}° Z={math.degrees(camera.rot_z):.1f}°",
            f"Focal: {camera.focal_length:.1f}",
            "WSAD: Move | Shift/Space: Up/Down | Arrows: Rotate XY | Q/E: Rotate Z | H/J: Zoom"
        ]

        for i, text in enumerate(info_text):
            surface = font.render(text, True, (200, 200, 200))
            screen.blit(surface, (10, 10 + i * 25))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


def save_screenshot(screen):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    pygame.image.save(screen, filename)


def draw_axes(screen, camera, width, height):
    origin = np.array([0, 0, 0])

    axis_points = {
        'X': np.array([1, 0, 0]),
        'Y': np.array([0, 1, 0]),
        'Z': np.array([0, 0, 1])
    }

    colors = {
        'X': (255, 0, 0),
        'Y': (0, 255, 0),
        'Z': (0, 0, 255)
    }

    center_x, center_y = width // 2, height // 2

    for axis, point in axis_points.items():
        p1 = camera.transform_vertex(origin)
        p2 = camera.transform_vertex(origin + point * 2)

        p1_2d = camera.project_vertex(p1)
        p2_2d = camera.project_vertex(p2)

        if p1_2d and p2_2d:
            pygame.draw.line(
                screen,
                colors[axis],
                (center_x + p1_2d[0], center_y - p1_2d[1]),
                (center_x + p2_2d[0], center_y - p2_2d[1]),
                2
            )


def draw_cuboid(screen, projected, edges, width, height):
    center_x, center_y = width // 2, height // 2

    for edge in edges:
        v1_idx, v2_idx = edge
        p1 = projected[v1_idx]
        p2 = projected[v2_idx]

        if p1 is not None and p2 is not None:
            screen_p1 = (center_x + p1[0], center_y - p1[1])
            screen_p2 = (center_x + p2[0], center_y - p2[1])
            pygame.draw.line(screen, (100, 200, 255), screen_p1, screen_p2, 1)

    for p in projected:
        if p is not None:
            screen_p = (center_x + p[0], center_y - p[1])
            pygame.draw.circle(screen, (255, 255, 255), screen_p, 3)


if __name__ == "__main__":
    main()
