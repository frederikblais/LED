import numpy as np
from functools import lru_cache

class LEDController:
    def __init__(self, num_leds=24):
        """Initialisation du contrôleur LED avec pré-calculs pour optimisation"""
        self.num_leds = num_leds
        self.current_mode = 'off'
        self.is_powered = False
        # Pré-calcul des valeurs communes pour réduire les calculs en temps réel
        self.loading_tail = [pow(x, 0.5) for x in np.linspace(1, 0, 8)]
        self.spin_tail = [pow(x, 0.5) for x in np.linspace(1, 0, 6)]
        
    @lru_cache(maxsize=128)
    def _get_black_array(self):
        """Cache des couleurs noires pour réduire l'allocation mémoire"""
        return [(0, 0, 0)] * self.num_leds

    def get_loading_frame(self, position):
        """Animation de chargement - rotation dans le sens horaire"""
        colors = list(self._get_black_array())
        for t, brightness in enumerate(self.loading_tail):
            idx = (position - t) % self.num_leds
            colors[idx] = tuple(c * brightness for c in (0, 0.5, 1.0))
        return colors

    def get_tracking_frame(self, brightness):
        """Animation de suivi - stroboscope à 30Hz"""
        return [(brightness, brightness, brightness)] * self.num_leds

    def get_error_frame(self, brightness):
        """Animation d'erreur - pulsation rouge"""
        return [(brightness, 0, 0)] * self.num_leds

    def get_success_frame(self, brightness):
        """Animation de succès - vert avec effet d'étincelles"""
        base = (0, brightness, 0)
        sparkle = (0, min(1.0, brightness + 0.3), 0)
        return [sparkle if np.random.random() < 0.2 else base for _ in range(self.num_leds)]

    def get_boot_sequence_frame(self, phase, step):
        """Séquence de démarrage avec plusieurs phases"""
        colors = list(self._get_black_array())
        
        if phase == 'fill':
            for i in range(step + 1):
                colors[i] = (0, 0.2, 0.4)
        elif phase == 'pulse':
            return [(0, 0.2 * step, 0.4 * step)] * self.num_leds
        elif phase == 'spin':
            # Use same tail length as loading animation
            for t, brightness in enumerate(self.loading_tail):
                idx = (step + t) % self.num_leds
                colors[idx] = tuple(c * brightness for c in (0, 0.5, 1.0))
        elif phase == 'success':
            wave_width = 8
            wave_position = step % self.num_leds
            for i in range(self.num_leds):
                distance = min((i - wave_position) % self.num_leds, 
                             (wave_position - i) % self.num_leds)
                if distance < wave_width:
                    brightness = 1 - (distance / wave_width)
                    colors[i] = (0, brightness, 0)
        elif phase == 'final':
            return [(1.0, 1.0, 1.0)] * self.num_leds
        
        return colors

    def get_shutdown_sequence_frame(self, phase, step):
        """Séquence d'arrêt améliorée"""
        colors = list(self._get_black_array())
        
        if phase == 'spin':
            # Red spinner with tail
            for t, brightness in enumerate(self.loading_tail):
                idx = (step + t) % self.num_leds
                colors[idx] = (brightness, 0, 0)  # Red spinner
        elif phase == 'fade':
            # Final fade to black
            return [(step * 0.3, 0, 0)] * self.num_leds  # Dim red fade
        
        return colors

    def set_mode(self, mode):
        """Change le mode d'animation actuel"""
        self.current_mode = mode
        
    def power_on(self):
        """Allume la bande LED"""
        self.is_powered = True
        
    def power_off(self):
        """Éteint la bande LED"""
        self.is_powered = False 