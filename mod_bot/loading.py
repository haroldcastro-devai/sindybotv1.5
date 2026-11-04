import logging
import pygame
import sys
import win32gui
import win32con
import win32api

logger = logging.getLogger(__name__)

class PreloaderAnimation:
    def __init__(self):
        pygame.init()

        # Configuración de la ventana
        self.width = 400
        self.height = 400

        # Inicializar la ventana sin el flag SRCALPHA
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.NOFRAME)
        pygame.display.set_caption('')

        # Obtener el handle de la ventana
        self.hwnd = pygame.display.get_wm_info()['window']

        # Hacer la ventana transparente y clickeable
        win32gui.SetWindowLong(
            self.hwnd,
            win32con.GWL_EXSTYLE,
            win32con.WS_EX_LAYERED
        )

        # Color clave para transparencia (negro)
        win32gui.SetLayeredWindowAttributes(
            self.hwnd,
            win32api.RGB(0, 0, 0),
            0,
            win32con.LWA_COLORKEY
        )

        # Ocultar el icono de la ventana
        win32gui.SetWindowLong(
            self.hwnd,
            win32con.GWL_EXSTYLE,
            win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_DLGMODALFRAME
        )

        # Ocultar la ventana de la barra de tareas
        win32gui.SetWindowLong(
            self.hwnd,
            win32con.GWL_EXSTYLE,
            win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_TOOLWINDOW
        )

        # Configuración de los colores (usando RGBA)
        self.TRANSPARENT = (0, 0, 0, 0)
        self.PURPLE = (155, 89, 182, 255)  # #9b59b6
        self.BLUE = (52, 152, 219, 255)    # #3498db
        self.YELLOW = (241, 196, 15, 255)  # #f1c40f
        self.GREEN = (46, 204, 113, 255)   # #2ecc71
        self.RED = (231, 76, 60, 255)      # #e74c3c
        self.TEXT_COLOR = (255, 255, 255)  # Blanco para el texto
        self.TEXT_SHADOW_COLOR = (0, 0, 0) # Negro para la sombra del texto

        # Configuración de los cuadrados
        self.square_size = 40
        self.center_x = self.width // 2 - self.square_size
        self.center_y = self.height // 2 - self.square_size

        # Configuración de la animación
        self.animation_time = 5000
        self.start_time = pygame.time.get_ticks()

        # Configuración del texto
        # Intentar cargar una fuente más gruesa
        _font_errors = (OSError, TypeError, pygame.error)
        try:
            self.font = pygame.font.SysFont('Arial Black', 18, bold=True)
        except _font_errors as exc:
            logger.debug("Fuente Arial Black no disponible: %s", exc)
            try:
                self.font = pygame.font.SysFont('Impact', 18, bold=True)
            except _font_errors as exc2:
                logger.debug("Fuente Impact no disponible: %s", exc2)
                try:
                    self.font = pygame.font.SysFont('Arial', 18, bold=True)
                except _font_errors as exc3:
                    logger.debug("Fuente Arial no disponible: %s", exc3)
                    self.font = pygame.font.Font(None, 18)

        # Colores ajustados para máxima visibilidad
        self.TEXT_COLOR = (100, 100, 100)      # Negro puro
        self.TEXT_SHADOW_COLOR = (10, 10, 10)  # Blanco puro
        self.TEXT_BACKGROUND_COLOR = (128, 128, 128, 230)  # Gris más opaco


        self.font = pygame.font.SysFont('Arial', 22, bold=True)
        self.text1 = "Procesando Auditoría..."
        self.text2 = "Espera Por favor..."

        # Estado de los textos
        self.current_text = self.text1
        self.text_alpha = 255

        # Variables para el arrastre
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0

        # Hacer la ventana TOPMOST al inicio
        win32gui.SetWindowPos(
            self.hwnd,
            win32con.HWND_TOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )

    def ease_in_out_cubic(self, x):
        if x < 0.5:
            return 4 * x * x * x
        else:
            return 1 - pow(-2 * x + 2, 3) / 2

    def ease_in_out_quint(self, x):
        if x < 0.5:
            return 16 * x * x * x * x * x
        else:
            return 1 - pow(-2 * x + 2, 5) / 2

    def interpolate_color(self, color1, color2, factor):
        factor = self.ease_in_out_quint(factor)
        return tuple(int(c1 + (c2 - c1) * factor) for c1, c2 in zip(color1, color2))

    def render_text_with_shadow(self, text, color, shadow_color):
        """Renderiza texto negro sólido con sombra blanca sin fondo"""
        # Renderizar el texto principal y la sombra
        shadow_surface = self.font.render(text, True, shadow_color)
        text_surface = self.font.render(text, True, (0, 0, 0))  # Negro sólido

        # Calcular el tamaño total necesario con padding
        padding = 10
        width = text_surface.get_width() + padding * 2
        height = text_surface.get_height() + padding * 2

        # Crear superficie final con soporte para transparencia
        final_surface = pygame.Surface((width, height), pygame.SRCALPHA)

        # Dibujar múltiples capas de sombra blanca
        shadow_offsets = [
            # Capa externa (más gruesa)
            (2,2), (-2,-2), (2,-2), (-2,2),
            (2,0), (-2,0), (0,2), (0,-2),
            # Capa media
            (1,1), (-1,-1), (1,-1), (-1,1),
            # Capa interna
            (1,0), (-1,0), (0,1), (0,-1),
        ]

        # Dibujar cada capa de sombra blanca
        for offset_x, offset_y in shadow_offsets:
            pos_x = padding + offset_x
            pos_y = padding + offset_y
            final_surface.blit(shadow_surface, (pos_x, pos_y))

        # Dibujar el texto negro principal múltiples veces para hacerlo más sólido
        for _ in range(3):  # Triple capa de texto negro
            final_surface.blit(text_surface, (padding, padding))

        return final_surface



    def calculate_square_positions(self, progress):
        positions = []
        colors = []
        rotations = []
        radiuses = []

        norm_progress = progress / self.animation_time

        if norm_progress < 0.35:
            move_factor = self.ease_in_out_quint(norm_progress / 0.35)
            shape_factor = self.ease_in_out_quint(norm_progress / 0.35)

            for i in range(4):
                if i == 0:
                    x = self.center_x - (40 * move_factor)
                    y = self.center_y - (20 * move_factor)
                    color = self.interpolate_color(self.PURPLE, self.BLUE, shape_factor)
                elif i == 1:
                    x = self.center_x + self.square_size + (40 * move_factor)
                    y = self.center_y - (20 * move_factor)
                    color = self.interpolate_color(self.PURPLE, self.YELLOW, shape_factor)
                elif i == 2:
                    x = self.center_x - (40 * move_factor)
                    y = self.center_y + self.square_size + (20 * move_factor)
                    color = self.interpolate_color(self.PURPLE, self.GREEN, shape_factor)
                else:
                    x = self.center_x + self.square_size + (40 * move_factor)
                    y = self.center_y + self.square_size + (20 * move_factor)
                    color = self.interpolate_color(self.PURPLE, self.RED, shape_factor)

                rotation = 180 * self.ease_in_out_cubic(move_factor) * (-1 if i in [0, 2] else 1)
                radius = int(40 * self.ease_in_out_quint(shape_factor))

                positions.append((x, y))
                colors.append(color)
                rotations.append(rotation)
                radiuses.append(radius)

        elif norm_progress < 0.55:
            move_factor = self.ease_in_out_quint(1 - ((norm_progress - 0.35) / 0.2))
            shape_factor = self.ease_in_out_quint(1 - ((norm_progress - 0.35) / 0.2))

            for i in range(4):
                if i == 0:
                    x = self.center_x - (40 * move_factor)
                    y = self.center_y - (20 * move_factor)
                elif i == 1:
                    x = self.center_x + self.square_size + (40 * move_factor)
                    y = self.center_y - (20 * move_factor)
                elif i == 2:
                    x = self.center_x - (40 * move_factor)
                    y = self.center_y + self.square_size + (20 * move_factor)
                else:
                    x = self.center_x + self.square_size + (40 * move_factor)
                    y = self.center_y + self.square_size + (20 * move_factor)

                positions.append((x, y))
                colors.append(self.PURPLE)
                rotations.append(0)
                radiuses.append(int(40 * shape_factor))

        else:
            for i in range(4):
                x = self.center_x + (self.square_size if i in [1, 3] else 0)
                y = self.center_y + (self.square_size if i in [2, 3] else 0)
                positions.append((x, y))
                colors.append(self.PURPLE)
                rotations.append(0)
                radiuses.append(0)

        return positions, colors, rotations, radiuses

    def draw_rounded_rect(self, surface, color, rect, radius, rotation=0):
        if rotation != 0 or radius > 0:
            temp_surface = pygame.Surface((self.square_size * 3, self.square_size * 3), pygame.SRCALPHA)
            if radius > 0:
                pygame.draw.rect(temp_surface, color,
                               (self.square_size, self.square_size,
                                self.square_size, self.square_size),
                               border_radius=radius)
            else:
                pygame.draw.rect(temp_surface, color,
                               (self.square_size, self.square_size,
                                self.square_size, self.square_size))

            if rotation != 0:
                rotated_surface = pygame.transform.rotozoom(temp_surface, rotation, 1)
                rot_rect = rotated_surface.get_rect(center=rect.center)
                surface.blit(rotated_surface, rot_rect)
            else:
                blit_rect = temp_surface.get_rect(center=rect.center)
                surface.blit(temp_surface, blit_rect)
        else:
            pygame.draw.rect(surface, color, rect)



    def update_text_state(self, current_time):
        text_progress = (current_time % (self.animation_time * 2)) / (self.animation_time * 2)

        if text_progress < 0.45:
            self.current_text = self.text1
            self.text_alpha = 255
        elif text_progress < 0.48:
            self.current_text = self.text1
            fade_factor = self.ease_in_out_quint((0.48 - text_progress) / 0.03)
            self.text_alpha = int(255 * fade_factor)
        elif text_progress < 0.52:
            self.text_alpha = 0
        elif text_progress < 0.55:
            self.current_text = self.text2
            fade_factor = self.ease_in_out_quint((text_progress - 0.52) / 0.03)
            self.text_alpha = int(255 * fade_factor)
        elif text_progress < 0.9:
            self.current_text = self.text2
            self.text_alpha = 255
        else:
            self.current_text = self.text2
            fade_factor = self.ease_in_out_quint((1 - text_progress) / 0.1)
            self.text_alpha = int(255 * fade_factor)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # Iniciar arrastre
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Obtener posición actual de la ventana y del mouse
                window_rect = win32gui.GetWindowRect(self.hwnd)
                mouse_pos = win32gui.GetCursorPos()

                # Calcular el offset
                self.offset_x = window_rect[0] - mouse_pos[0]
                self.offset_y = window_rect[1] - mouse_pos[1]
                self.dragging = True

            # Terminar arrastre
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False

            # Procesar arrastre
            elif event.type == pygame.MOUSEMOTION and self.dragging:
                # Obtener posición actual del mouse
                mouse_pos = win32gui.GetCursorPos()

                # Calcular nueva posición
                new_x = mouse_pos[0] + self.offset_x
                new_y = mouse_pos[1] + self.offset_y

                # Mover la ventana y mantenerla como TOPMOST
                win32gui.SetWindowPos(
                    self.hwnd,
                    win32con.HWND_TOPMOST,
                    new_x,
                    new_y,
                    0, 0,
                    win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
                )

        return True

    def run(self):
        clock = pygame.time.Clock()
        running = True

        while running:
            running = self.handle_events()

            current_time = pygame.time.get_ticks()
            animation_progress = (current_time - self.start_time) % self.animation_time

            # Limpiar pantalla con negro (que será transparente)
            self.screen.fill((0, 0, 0))

            # Dibujar cuadrados animados
            positions, colors, rotations, radiuses = self.calculate_square_positions(animation_progress)

            for (x, y), color, rotation, radius in zip(positions, colors, rotations, radiuses):
                rect = pygame.Rect(x, y, self.square_size, self.square_size)
                self.draw_rounded_rect(self.screen, color, rect, radius, rotation)

            # Actualizar y dibujar texto
            self.update_text_state(current_time)
            text_surface = self.render_text_with_shadow(self.current_text, self.TEXT_COLOR, self.TEXT_SHADOW_COLOR)
            text_surface.set_alpha(self.text_alpha)
            text_rect = text_surface.get_rect(center=(self.width // 2, self.height // 2 + 80))
            self.screen.blit(text_surface, text_rect)

            pygame.display.flip()
            clock.tick(120)

# Código principal
if __name__ == "__main__":
    try:
        # Verificar que pywin32 está instalado
        import win32gui
        import win32con
        import win32api
    except ImportError:
        print("Error: pywin32 no está instalado")
        print("Por favor, instala pywin32 usando:")
        print("pip install pywin32")
        sys.exit(1)

    try:
        # Iniciar la animación
        animation = PreloaderAnimation()
        animation.run()
    except Exception as e:
        print(f"Error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Asegurar que pygame se cierre correctamente
        pygame.quit()
        sys.exit()
