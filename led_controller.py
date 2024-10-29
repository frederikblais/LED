import numpy as np
from functools import lru_cache

class LEDController:
    def __init__(self, num_leds=24):
        """Initialisation du contrôleur LED avec pré-calculs pour optimisation"""
        self.num_leds = num_leds
        self.current_mode = 'off'
        self.is_powered = False
        # Pré-calcul des valeurs communes pour réduire les calculs en temps réel
        self.loading_tail = [pow(x, 0.5) for x in np.linspace(1, 0, 12)]
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
        """Animation de suivi - pulsation uniforme"""
        return [(brightness,) * 3] * self.num_leds

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
            # Remplissage progressif
            for i in range(step + 1):
                colors[i] = (0, 0.2, 0.4)
        elif phase == 'pulse':
            # Pulsation uniforme
            return [(0, 0.2 * step, 0.4 * step)] * self.num_leds
        elif phase == 'spin':
            # Rotation finale
            for t, brightness in enumerate(self.spin_tail):
                idx = (step + t) % self.num_leds
                colors[idx] = tuple(c * brightness for c in (0, 0.5, 1.0))
        return colors

    def get_shutdown_sequence_frame(self, phase, step):
        """Séquence d'arrêt avec effets de transition"""
        if phase == 'pulse':
            # Pulsation rapide
            return [(step,) * 3] * self.num_leds
        elif phase == 'wipe':
            # Effacement progressif
            colors = list(self._get_black_array())
            for i in range(step):
                colors[i] = (1, 1, 1)
            return colors
        else:  # fade
            # Fondu final
            return [(0.1 * step,) * 2 + (0.2 * step,)] * self.num_leds

    def set_mode(self, mode):
        """Change le mode d'animation actuel"""
        self.current_mode = mode
        
    def power_on(self):
        """Allume la bande LED"""
        self.is_powered = True
        
    def power_off(self):
        """Éteint la bande LED"""
        self.is_powered = False 