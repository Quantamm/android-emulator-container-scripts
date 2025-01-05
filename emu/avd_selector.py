import glob
from consolemenu import SelectionMenu
import os

class AVDSelector:
    """Class to select an Android Virtual Device (AVD) configuration file."""

    def select_avd(self):
        """Prompts the user to select an AVD config file from the available templates.

        Returns:
            The basename of the selected AVD config file (without .ini extension), or None if no selection is made.
        """
        # Get the directory of the current script
        script_dir = os.path.dirname(__file__)
        avd_path = os.path.join(script_dir, 'templates/avd/*.ini')

        files = glob.glob(avd_path)
        if not files:
            print("No AVD config files found in emu/templates/avd/")
            return None

        display = [os.path.splitext(os.path.basename(f))[0] for f in files]

        selection = SelectionMenu.get_selection(
            display, title="Select the AVD config file you wish to use:"
        )

        if selection < len(display):
            return display[selection]
        else:
            return None
