#!/usr/bin/env python3

import board
import neopixel
import time
import sys
import tty
import termios
import threading
from queue import Queue
import math
from led_controller import LEDController

class LEDAnimationRunner:
    """
    Gère l'exécution des animations sur un anneau LED physique.
    Utilise la bibliothèque neopixel pour contrôler les LEDs.
    """

    def __init__(self):
        """Initialise le contrôleur LED avec 24 LEDs sur le pin D18"""
        self.pixels = neopixel.NeoPixel(
            board.D18,
            24,
            brightness=0.3,
            auto_write=False
        )
        self.controller = LEDController(num_leds=24)
        self.running = True
        self.current_animation = None

    def _update_pixels(self, colors):
        """
        Applique les couleurs aux LEDs.
        Args:
            colors: Liste de tuples (r,g,b) avec valeurs entre 0-1
        """
        for i, (r, g, b) in enumerate(colors):
            self.pixels[i] = (int(r * 255), int(g * 255), int(b * 255))
        self.pixels.show()

    def clear(self):
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

    def loading_animation(self):
        """Animation de chargement rotative bleue à 60fps"""
        position = 0
        while self.current_animation == 'loading':
            colors = self.controller.get_loading_frame(position)
            self._update_pixels(colors)
            position = (position + 1) % 24
            time.sleep(0.016)

    def tracking_animation(self):
        """Animation stroboscopique blanche à 30Hz"""
        frame_time = 1/30  # 30Hz = 1/30 second per frame
        while self.current_animation == 'tracking':
            # On frame
            colors = self.controller.get_tracking_frame(1.0)  # Full brightness
            self._update_pixels(colors)
            time.sleep(frame_time/2)  # Half time on
            
            # Off frame
            colors = self.controller.get_tracking_frame(0.0)  # Zero brightness
            self._update_pixels(colors)
            time.sleep(frame_time/2)  # Half time off

    def boot_sequence(self):
        """
        Séquence de démarrage en 5 phases:
        1. Remplissage progressif
        2. Pulsation
        3. Rotation rapide
        4. Vague verte
        5. Transition vers blanc
        """
        # Fill phase
        for step in range(24):
            if self.current_animation != 'boot':
                break
            colors = self.controller.get_boot_sequence_frame('fill', step)
            self._update_pixels(colors)
            time.sleep(0.05)
        
        # Pulse phase
        for step in range(10):
            if self.current_animation != 'boot':
                break
            brightness = step / 10
            colors = self.controller.get_boot_sequence_frame('pulse', brightness)
            self._update_pixels(colors)
            time.sleep(0.05)
        
        # Spin phase (blue spinner) - faster like loading animation
        for step in range(168):  # Seven full rotations (24 * 7)
            if self.current_animation != 'boot':
                break
            colors = self.controller.get_boot_sequence_frame('spin', step)
            self._update_pixels(colors)
            time.sleep(0.016)  # Matched to loading animation speed
        
        # Green completion wave
        last_spinner_colors = self.controller.get_boot_sequence_frame('spin', 167)
        for step in range(24):  # One full rotation to complete the circle
            if self.current_animation != 'boot':
                break
            colors = list(last_spinner_colors)  # Keep the blue spinner tail
            # Add green wave following the spinner
            for i in range(step + 1):
                pos = (167 + i) % 24  # Start from where spinner ended
                colors[pos] = (0, 1, 0)  # Bright green
            self._update_pixels(colors)
            time.sleep(0.03)
        
        # Success animation - three quick green waves
        for _ in range(3):
            for step in range(24):
                if self.current_animation != 'boot':
                    break
                colors = self.controller.get_boot_sequence_frame('success', step)
                self._update_pixels(colors)
                time.sleep(0.02)
        
        # Final fade from green to white
        if self.current_animation == 'boot':
            for step in range(20):
                progress = step / 20
                green = [(0, 1-progress, 0)] * self.controller.num_leds
                white = [(progress, progress, progress)] * self.controller.num_leds
                blended = [(g[0] + w[0], g[1] + w[1], g[2] + w[2]) 
                          for g, w in zip(green, white)]
                self._update_pixels(blended)
                time.sleep(0.03)
            
            colors = self.controller.get_boot_sequence_frame('final', 0)
            self._update_pixels(colors)
            time.sleep(1)

    def shutdown_sequence(self):
        """
        Séquence d'arrêt en 4 phases:
        1. Atténuation du blanc
        2. Flash rouge d'alerte
        3. Rotation ralentissante
        4. Fondu final
        """
        # Initial white pulse down
        for step in range(20):
            if self.current_animation != 'shutdown':
                break
            progress = (20 - step) / 20
            colors = [(progress, progress, progress)] * self.controller.num_leds
            self._update_pixels(colors)
            time.sleep(0.03)
        
        # Red warning flash (three quick pulses)
        for _ in range(3):
            if self.current_animation != 'shutdown':
                break
            # Flash on
            colors = [(0.8, 0, 0)] * self.controller.num_leds
            self._update_pixels(colors)
            time.sleep(0.1)
            # Flash off
            colors = [(0, 0, 0)] * self.controller.num_leds
            self._update_pixels(colors)
            time.sleep(0.1)
        
        # Spin down animation (red spinner that slows down)
        position = 0
        speed = 0.016  # Start fast
        for step in range(48):  # Two rotations
            if self.current_animation != 'shutdown':
                break
            colors = self.controller.get_shutdown_sequence_frame('spin', position)
            self._update_pixels(colors)
            position = (position + 1) % 24
            speed = 0.016 + (step * 0.004)  # Gradually slow down
            time.sleep(speed)
        
        # Final fade out
        for step in range(20):
            if self.current_animation != 'shutdown':
                break
            progress = (20 - step) / 20
            colors = self.controller.get_shutdown_sequence_frame('fade', progress)
            self._update_pixels(colors)
            time.sleep(0.05)
        
        # Ensure all LEDs are off
        self.clear()

    def success_animation(self):
        """Animation verte avec effet d'étincelles"""
        # Initial flash of green
        colors = self.controller.get_success_frame(1.0)
        self._update_pixels(colors)
        time.sleep(0.5)
        
        # Three sparkle waves
        for _ in range(3):
            for step in range(20):  # Sparkle animation frames
                if self.current_animation != 'success':
                    break
                brightness = 0.7 + (math.sin(step * 0.3) * 0.3)  # Oscillate between 0.4 and 1.0
                colors = self.controller.get_success_frame(brightness)
                self._update_pixels(colors)
                time.sleep(0.05)

    def error_animation(self):
        """Pulsation rouge avec attaque rapide et déclin lent"""
        while self.current_animation == 'error':
            # Pulse from dim to bright red
            for step in range(20):
                if self.current_animation != 'error':
                    break
                # Sharp attack, slow decay
                brightness = math.pow(1 - (step / 20), 2)  # Quadratic falloff
                colors = self.controller.get_error_frame(brightness)
                self._update_pixels(colors)
                time.sleep(0.02 if step < 5 else 0.04)  # Faster rise, slower fall
            time.sleep(0.2)  # Pause between pulses

def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def print_menu():
    print("\n=== LED Animation Controller ===")
    print("1: Boot Sequence")
    print("2: Tracking Animation (30Hz)")
    print("3: Loading Animation")
    print("4: Success Animation")
    print("5: Error Animation")
    print("6: Shutdown Sequence")
    print("c: Clear LEDs")
    print("q: Quit")
    print("\nCurrent animation will loop until you press another key.")
    print("=========================")

def main():
    runner = LEDAnimationRunner()
    animation_thread = None

    print_menu()

    while True:
        key = get_key()

        if key == 'q':
            runner.current_animation = None
            if animation_thread and animation_thread.is_alive():
                animation_thread.join()
            runner.clear()
            print("\nExiting...")
            break
        
        elif key == 'c':
            runner.current_animation = None
            if animation_thread and animation_thread.is_alive():
                animation_thread.join()
            runner.clear()
            print("\nLEDs cleared")
            print_menu()

        elif key in ['1', '2', '3', '4', '5', '6']:
            runner.current_animation = None
            if animation_thread and animation_thread.is_alive():
                animation_thread.join()

            if key == '1':
                print("\nRunning boot sequence...")
                runner.current_animation = 'boot'
                animation_thread = threading.Thread(target=runner.boot_sequence)
            elif key == '2':
                print("\nRunning tracking animation...")
                runner.current_animation = 'tracking'
                animation_thread = threading.Thread(target=runner.tracking_animation)
            elif key == '3':
                print("\nRunning loading animation...")
                runner.current_animation = 'loading'
                animation_thread = threading.Thread(target=runner.loading_animation)
            elif key == '4':
                print("\nRunning success animation...")
                runner.current_animation = 'success'
                animation_thread = threading.Thread(target=runner.success_animation)
            elif key == '5':
                print("\nRunning error animation...")
                runner.current_animation = 'error'
                animation_thread = threading.Thread(target=runner.error_animation)
            elif key == '6':
                print("\nRunning shutdown sequence...")
                runner.current_animation = 'shutdown'
                animation_thread = threading.Thread(target=runner.shutdown_sequence)

            animation_thread.start()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)