import glob
from consolemenu import SelectionMenu
import os

class AVDSelector:
    """Class to select an Android Virtual Device (AVD) configuration file."""

    def select_avd(self):
        """Prompts the user to select an AVD config file from the available templates.

        Returns:
            The path to the selected AVD config file, or None if no selection is made.
        """
        files = glob.glob('emu/templates/avd/*.ini')
        if not files:
            print("No AVD config files found in emu/templates/avd/")
            return None

        display = [os.path.basename(f) for f in files]

        selection = SelectionMenu.get_selection(
            display, title="Select the AVD config file you wish to use:"
        )

        if selection < len(files):
            return files[selection]
        else:
            return None
