from plan_tools.entry_point import EntryPoint


def configure_cli() -> None:
    source_dir = "energyplus_pet"
    name = "energyplus_pet_gui"
    description = "An EnergyPlus Parameter Estimation Tool"
    nice_name = "EnergyPlus P.E.T."
    s = EntryPoint(source_dir, name, nice_name, description, name)
    s.run()
