import numpy as np
import matplotlib.pyplot as plt
from led_controller import LEDController

class LEDVisualizer:
    def __init__(self, num_leds=24):
        """Initialisation du visualiseur avec configuration de l'interface graphique"""
        self.controller = LEDController(num_leds)
        
        # Configuration de base de matplotlib
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(8, 10))
        plt.rcParams['toolbar'] = 'None'
        
        # Configuration du graphique polaire
        self.ax = self.fig.add_subplot(111, projection='polar')
        angles = np.linspace(0, 2*np.pi, num_leds, endpoint=False)
        radius = [1] * num_leds
        self.scatter = self.ax.scatter(angles, radius, c=[(0,0,0)]*num_leds, s=300)
        
        # Nettoyage de l'interface
        self._clean_display()
        
        # Configuration plein écran
        self._setup_fullscreen()
        
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        plt.ion()

    def _clean_display(self):
        """Nettoie l'affichage des éléments non nécessaires"""
        self.ax.set_rticks([])
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_frame_on(False)
        self.fig.tight_layout(pad=0)

    def _setup_fullscreen(self):
        """Configure le mode plein écran selon le système"""
        try:
            manager = plt.get_current_fig_manager()
            if hasattr(manager, 'window'):
                manager.window.attributes('-fullscreen', True)
                manager.toolbar.pack_forget()
            elif hasattr(manager, 'full_screen_toggle'):
                manager.full_screen_toggle()
            else:
                manager.window.showMaximized()
        except Exception as e:
            print(f"Erreur de configuration plein écran: {e}")

    def clear_display(self):
        """Efface l'affichage des LEDs"""
        self.scatter.set_color([(0,0,0)] * self.controller.num_leds)
        plt.title('')

    def on_key_press(self, event):
        """Gestion des entrées clavier"""
        if event.key == 'escape':
            plt.close('all')
            return
            
        if not self.controller.is_powered and event.key != 'b':
            return
            
        if event.key in ['left', 'right'] and self.controller.is_powered:
            self._handle_mode_change(event.key)
        elif event.key == 'b' and not self.controller.is_powered:
            self.controller.power_on()
            self.boot_sequence()
        elif event.key == 'v' and self.controller.is_powered:
            self.shutdown_sequence()

    def _handle_mode_change(self, key):
        """Gère le changement de mode d'animation"""
        modes = ['loading', 'tracking', 'error', 'success']
        current_idx = modes.index(self.controller.current_mode) if self.controller.current_mode in modes else 0
        new_idx = (current_idx + (1 if key == 'right' else -1)) % len(modes)
        self.controller.set_mode(modes[new_idx])

    def run(self):
        """Boucle principale d'animation"""
        print("Starting LED Visualizer...\nControls:\n← → : Change animation\nb   : Boot sequence\nv   : Shutdown sequence\nESC : Exit program")
        self.clear_display()
        
        # Initialisation des variables d'animation
        self.position = 0  # Converti en variable d'instance
        self.tracking_brightness = 1.0
        self.error_brightness = 1.0
        self.success_brightness = 1.0
        self.success_direction = -0.05
        
        try:
            while plt.fignum_exists(self.fig.number):
                if not self.controller.is_powered:
                    plt.title('System OFF (Press B to boot)', color='white', pad=20, y=1.05)
                    plt.pause(0.1)
                    continue
                
                mode = self.controller.current_mode
                if mode == 'loading':
                    colors = self.controller.get_loading_frame(self.position)
                    self.position = (self.position - 1) % self.controller.num_leds
                elif mode == 'tracking':
                    self.tracking_brightness = 1.0 if self.tracking_brightness == 0.3 else 0.3
                    colors = self.controller.get_tracking_frame(self.tracking_brightness)
                elif mode == 'error':
                    self.error_brightness = max(0, self.error_brightness - 0.05)
                    if self.error_brightness <= 0:
                        self.error_brightness = 1.0
                    colors = self.controller.get_error_frame(self.error_brightness)
                elif mode == 'success':
                    self.success_brightness += self.success_direction
                    if self.success_brightness <= 0.3:
                        self.success_brightness = 0.3
                        self.success_direction = 0.05
                    elif self.success_brightness >= 1.0:
                        self.success_brightness = 1.0
                        self.success_direction = -0.05
                    colors = self.controller.get_success_frame(self.success_brightness)
                
                # Mise à jour du titre
                title_color = 'red' if mode == 'error' else 'green' if mode == 'success' else 'white'
                plt.title(f'{mode.title()} Animation (← → pour changer)', 
                         color=title_color, pad=20, y=1.05)
                
                # Mise à jour de l'affichage
                self.scatter.set_color(colors)
                plt.pause(0.03)  # Contrôle la vitesse de l'animation
                
        except Exception as e:
            print(f"Erreur d'animation: {e}")
        finally:
            plt.close('all')

    def boot_sequence(self):
        """Séquence de démarrage avec animations progressives"""
        self.clear_display()
        plt.title('Démarrage du système...', color='white', pad=20, y=1.05)
        
        try:
            # Phase 1: Remplissage progressif
            for step in range(self.controller.num_leds):
                colors = self.controller.get_boot_sequence_frame('fill', step)
                self.scatter.set_color(colors)
                plt.pause(0.03)
            
            # Phase 2: Double pulsation
            for _ in range(2):
                # Fondu sortant
                for brightness in np.linspace(1, 0, 20):
                    colors = self.controller.get_boot_sequence_frame('pulse', brightness)
                    self.scatter.set_color(colors)
                    plt.pause(0.02)
                
                # Fondu entrant
                for brightness in np.linspace(0, 1, 20):
                    colors = self.controller.get_boot_sequence_frame('pulse', brightness)
                    self.scatter.set_color(colors)
                    plt.pause(0.02)
            
            # Phase 3: Rotation finale
            for step in range(self.controller.num_leds * 2):
                colors = self.controller.get_boot_sequence_frame('spin', step)
                self.scatter.set_color(colors)
                plt.pause(0.02)
            
            self.controller.set_mode('loading')
            plt.title('Système prêt (← → pour changer)', color='white', pad=20, y=1.05)
            
        except Exception as e:
            print(f"Erreur séquence démarrage: {e}")
            self.controller.power_off()
            self.clear_display()

    def shutdown_sequence(self):
        """Séquence d'arrêt avec effets de transition"""
        plt.title('Arrêt du système...', color='white', pad=20, y=1.05)
        
        try:
            # Phase 1: Pulsation rapide
            for _ in range(3):
                colors = self.controller.get_shutdown_sequence_frame('pulse', 0)
                self.scatter.set_color(colors)
                plt.pause(0.1)
                colors = self.controller.get_shutdown_sequence_frame('pulse', 1)
                self.scatter.set_color(colors)
                plt.pause(0.1)
            
            # Phase 2: Effacement progressif
            for step in range(self.controller.num_leds):
                colors = self.controller.get_shutdown_sequence_frame('wipe', step)
                self.scatter.set_color(colors)
                plt.pause(0.05)
            
            # Phase 3: Fondu final
            for brightness in np.linspace(1, 0, 30):
                colors = self.controller.get_shutdown_sequence_frame('fade', brightness)
                self.scatter.set_color(colors)
                plt.pause(0.02)
            
            self.clear_display()
            self.controller.power_off()
            plt.title('Système éteint (B pour démarrer)', color='white', pad=20, y=1.05)
            
        except Exception as e:
            print(f"Erreur séquence arrêt: {e}")
            self.controller.power_off()
            self.clear_display()

if __name__ == "__main__":
    visualizer = LEDVisualizer()
    visualizer.run()