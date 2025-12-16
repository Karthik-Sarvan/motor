from pymodbus.client import ModbusSerialClient
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import threading
import time

# ============== CONFIGURATION ==============
PORT = "/dev/ttyUSB0"
BAUD = 4800
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# ============== GLOBAL TILT DATA ==============
tilt_data = {'x': 0.0, 'y': 0.0, 'z': 0.0}
data_lock = threading.Lock()
running = True


def to_signed(v):
    """Convert unsigned 16-bit to signed."""
    return v - 65536 if v > 32767 else v


def read_tilt_sensor():
    """Thread function to continuously read tilt sensor."""
    global running, tilt_data
    
    client = ModbusSerialClient(
        port=PORT,
        baudrate=BAUD,
        parity='N',
        stopbits=1,
        bytesize=8,
        timeout=1
    )
    
    if not client.connect():
        print("❌ Cannot connect to tilt sensor")
        running = False
        return
    
    print("✅ Tilt sensor connected")
    
    while running:
        try:
            rx = client.read_holding_registers(0).registers[0]
            ry = client.read_holding_registers(1).registers[0]
            rz = client.read_holding_registers(2).registers[0]
            
            with data_lock:
                tilt_data['x'] = to_signed(rx) / 100.0
                tilt_data['y'] = to_signed(ry) / 100.0
                tilt_data['z'] = to_signed(rz) / 100.0
            
        except Exception as e:
            print(f"Read error: {e}")
        
        time.sleep(0.02)  # 50Hz update rate
    
    client.close()


def draw_cube():
    """Draw a colored cube."""
    vertices = [
        # Front face
        (-1, -1,  1), ( 1, -1,  1), ( 1,  1,  1), (-1,  1,  1),
        # Back face
        (-1, -1, -1), (-1,  1, -1), ( 1,  1, -1), ( 1, -1, -1),
    ]
    
    faces = [
        (0, 1, 2, 3),  # Front  - Red
        (4, 5, 6, 7),  # Back   - Green
        (3, 2, 6, 5),  # Top    - Blue
        (0, 7, 6, 1),  # Bottom - Yellow
        (0, 3, 5, 4),  # Left   - Magenta
        (1, 6, 2, 7),  # Right  - Cyan (fixed winding)
    ]
    
    colors = [
        (1, 0, 0),    # Red
        (0, 1, 0),    # Green
        (0, 0, 1),    # Blue
        (1, 1, 0),    # Yellow
        (1, 0, 1),    # Magenta
        (0, 1, 1),    # Cyan
    ]
    
    glBegin(GL_QUADS)
    for i, face in enumerate(faces):
        glColor3fv(colors[i])
        for vertex in face:
            glVertex3fv(vertices[vertex])
    glEnd()
    
def draw_axes():
    """Draw X, Y, Z axes for reference."""
    glLineWidth(3)
    glBegin(GL_LINES)
    # X axis - Red
    glColor3f(1, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(3, 0, 0)
    # Y axis - Green
    glColor3f(0, 1, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 3, 0)
    # Z axis - Blue
    glColor3f(0, 0, 1)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 0, 3)
    glEnd()


def draw_text(x, y, text, font, color=(255, 255, 255)):
    """Render text on screen."""
    text_surface = font.render(text, True, color)
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    
    glWindowPos2d(x, y)
    glDrawPixels(
        text_surface.get_width(),
        text_surface.get_height(),
        GL_RGBA,
        GL_UNSIGNED_BYTE,
        text_data
    )


def main():
    global running
    
    # Start sensor reading thread
    sensor_thread = threading.Thread(target=read_tilt_sensor, daemon=True)
    sensor_thread.start()
    
    # Initialize Pygame and OpenGL
    pygame.init()
    pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("3D Tilt Sensor Visualization")
    
    # Setup perspective
    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)
    
    # Enable depth testing
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Font for displaying angles
    font = pygame.font.SysFont('monospace', 24)
    
    clock = pygame.time.Clock()
    
    print("\n🎮 Controls:")
    print("   ESC or close window to exit\n")
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Get current tilt angles
        with data_lock:
            x_angle = tilt_data['x']
            y_angle = tilt_data['y']
            z_angle = tilt_data['z']
        
        # Clear screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Position camera
        glTranslatef(0, 0, -7)
        
        # Apply rotations from tilt sensor
        # Adjust these axes mapping based on your sensor orientation
        glRotatef(x_angle, 1, 0, 0)  # Pitch
        glRotatef(y_angle, 0, 1, 0)  # Roll
        glRotatef(z_angle, 0, 0, 1)  # Yaw
        
        # Draw the 3D object
        draw_cube()
        draw_axes()
        
        # Display angle values as text overlay
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)
        draw_text(10, WINDOW_HEIGHT - 30, f"X (Pitch): {x_angle:+7.2f}°", font, (255, 100, 100))
        draw_text(10, WINDOW_HEIGHT - 60, f"Y (Roll):  {y_angle:+7.2f}°", font, (100, 255, 100))
        draw_text(10, WINDOW_HEIGHT - 90, f"Z (Yaw):   {z_angle:+7.2f}°", font, (100, 100, 255))
        glEnable(GL_DEPTH_TEST)
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        pygame.display.flip()
        clock.tick(60)  # 60 FPS
    
    pygame.quit()
    print("👋 Goodbye!")


if __name__ == "__main__":
    main()