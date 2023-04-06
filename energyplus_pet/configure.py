from plan_tools.entry_point import EntryPoint
from energyplus_pet import NAME, NICE_NAME


def configure_cli() -> None:
    source_dir = "energyplus_pet"
    name = "energyplus_pet_gui"
    description = "An EnergyPlus Parameter Estimation Tool"
    s = EntryPoint(source_dir, name, NICE_NAME, description, NAME)
    s.run()
