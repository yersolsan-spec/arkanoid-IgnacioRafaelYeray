"""Plantilla del juego Arkanoid para el hito M2.

Completa los métodos marcados con TODO respetando las anotaciones de tipo y la
estructura de la clase. El objetivo es construir un prototipo jugable usando
pygame que cargue bloques desde un fichero de nivel basado en caracteres.
"""
import os
if os.name == "nt":  # Windows
    os.environ["SDL_VIDEODRIVER"] = "windows"

from arkanoid_core import *

# --------------------------------------------------------------------- #
# Métodos a completar por el alumnado
# --------------------------------------------------------------------- #

@arkanoid_method
def cargar_nivel(self) -> list[str]:
    """Lee el fichero de nivel y devuelve la cuadrícula como lista de filas."""
    # El fichero tiene que existir
    if not self.level_path.is_file():
        raise FileNotFoundError(f"No existe el nivel: {self.level_path}")

    # Leemos las filas y quitamos las líneas vacías
    filas = []
    for linea in self.level_path.read_text(encoding="utf-8").splitlines():
        if linea.strip() != "":
            filas.append(linea.strip())

    if len(filas) == 0:
        raise ValueError("El nivel está vacío")

    # Todas las filas deben medir lo mismo
    for fila in filas:
        if len(fila) != len(filas[0]):
            raise ValueError("Las filas del nivel tienen distinta longitud")

    self.layout = filas
    return self.layout


@arkanoid_method
def preparar_entidades(self) -> None:
    """Posiciona paleta y bola, y reinicia puntuación y vidas."""
    # Paleta centrada abajo
    self.paddle.size = self.PADDLE_SIZE
    self.paddle.midbottom = (self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT - self.PADDLE_OFFSET)

    self.score = 0
    self.lives = 3
    self.end_message = ""

    # Bola sobre la paleta, saliendo en diagonal hacia arriba
    self.reiniciar_bola((1, -1))


@arkanoid_method
def crear_bloques(self) -> None:
    """Genera los rectángulos de los bloques en base a la cuadrícula."""
    self.blocks.clear()
    self.block_colors.clear()
    self.block_symbols.clear()

    for fila in range(len(self.layout)):
        for columna in range(len(self.layout[fila])):
            simbolo = self.layout[fila][columna]
            if simbolo in self.BLOCK_COLORS:
                self.blocks.append(self.calcular_posicion_bloque(fila, columna))
                self.block_colors.append(self.BLOCK_COLORS[simbolo])
                self.block_symbols.append(simbolo)


@arkanoid_method
def procesar_input(self) -> None:
    """Gestiona la entrada de teclado para mover la paleta."""
    teclas = self.obtener_estado_teclas()

    if teclas[self.KEY_LEFT] or teclas[self.KEY_A]:
        self.paddle.x -= self.PADDLE_SPEED
    if teclas[self.KEY_RIGHT] or teclas[self.KEY_D]:
        self.paddle.x += self.PADDLE_SPEED

    # No salirse de la pantalla
    if self.paddle.left < 0:
        self.paddle.left = 0
    if self.paddle.right > self.SCREEN_WIDTH:
        self.paddle.right = self.SCREEN_WIDTH


@arkanoid_method
def actualizar_bola(self) -> None:
    """Actualiza la posición de la bola y resuelve colisiones."""
    # Mover la bola
    self.ball_pos += self.ball_velocity
    ball_rect = self.obtener_rect_bola()

    # Rebote con paredes izquierda, derecha y techo
    if ball_rect.left <= 0 or ball_rect.right >= self.SCREEN_WIDTH:
        self.ball_velocity.x = -self.ball_velocity.x
    if ball_rect.top <= 0:
        self.ball_velocity.y = -self.ball_velocity.y

    # Rebote con la paleta (solo si la bola baja)
    if ball_rect.colliderect(self.paddle) and self.ball_velocity.y > 0:
        self.ball_velocity.y = -self.ball_velocity.y

    # Rebote con los bloques
    for i in range(len(self.blocks)):
        if ball_rect.colliderect(self.blocks[i]):
            self.ball_velocity.y = -self.ball_velocity.y
            self.score += self.BLOCK_POINTS[self.block_symbols[i]]
            self.blocks.pop(i)
            self.block_colors.pop(i)
            self.block_symbols.pop(i)
            break  # solo un bloque por fotograma

    # Victoria: no quedan bloques
    if len(self.blocks) == 0:
        self.end_message = "¡Victoria!"

    # La bola cae por abajo: se pierde una vida
    if ball_rect.top > self.SCREEN_HEIGHT:
        self.lives -= 1
        if self.lives == 0:
            self.end_message = "Derrota"
        else:
            self.reiniciar_bola((1, -1))


@arkanoid_method
def dibujar_escena(self) -> None:
    """Renderiza fondo, bloques, paleta, bola y HUD."""
    self.screen.fill(self.BACKGROUND_COLOR)

    for i in range(len(self.blocks)):
        self.dibujar_rectangulo(self.blocks[i], self.block_colors[i])

    self.dibujar_rectangulo(self.paddle, self.PADDLE_COLOR)
    self.dibujar_circulo((int(self.ball_pos.x), int(self.ball_pos.y)), self.BALL_RADIUS, self.BALL_COLOR)

    self.dibujar_texto(f"Puntos: {self.score}", (16, 16))
    self.dibujar_texto(f"Vidas: {self.lives}", (self.SCREEN_WIDTH - 110, 16))

    if self.end_message != "":
        self.dibujar_texto(self.end_message, (self.SCREEN_WIDTH // 2 - 80, self.SCREEN_HEIGHT // 2), grande=True)


@arkanoid_method
def run(self) -> None:
    """Ejecuta el bucle principal del juego."""
    # Primero el nivel: si falla, no se abre la ventana
    self.cargar_nivel()

    self.inicializar_pygame()
    self.preparar_entidades()
    self.crear_bloques()
    self.running = True

    while self.running:
        # Eventos: cerrar ventana o pulsar Escape
        for evento in self.iterar_eventos():
            if evento.type == self.EVENT_QUIT:
                self.running = False
            elif evento.type == self.EVENT_KEYDOWN and evento.key == self.KEY_ESCAPE:
                self.running = False

        self.procesar_input()
        self.actualizar_bola()
        self.dibujar_escena()
        self.actualizar_pantalla()

        # Fin de partida: se enseña el mensaje 2 segundos y se sale
        if self.end_message != "":
            self.esperar(2000)
            self.running = False

        self.clock.tick(self.FPS)

    self.finalizar_pygame()


def main() -> None:
    """Permite ejecutar el juego desde la línea de comandos."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Plantilla del hito M2: Arkanoid con pygame.",
    )
    parser.add_argument(
        "level",
        type=str,
        help="Ruta al fichero de nivel (texto con # para bloques y . para huecos).",
    )
    args = parser.parse_args()

    game = ArkanoidGame(args.level)
    game.run()


if __name__ == "__main__":
    main()
