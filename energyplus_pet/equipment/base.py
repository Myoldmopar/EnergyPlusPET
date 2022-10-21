from abc import abstractmethod
from typing import Callable, List, Tuple

from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.equipment.column_header import ColumnHeaderArray
from energyplus_pet.units import BaseValueWithUnit


# Note: Abstract methods are not being tested for coverage here

class BaseEquipment:
    """
    This class represents an abstract piece of equipment to be processed by this library.
    This is primarily a set of abstract methods that define what must be overridden by derived equipment classes.
    """

    def this_type(self) -> EquipType:
        """
        Returns the EquipType enumeration for the derived equipment class.

        :return: Entry from the EquipType enumeration
        """
        return EquipType.InvalidType

    @abstractmethod
    def name(self) -> str:  # pragma: no cover
        """
        Must be overridden to return a meaningful descriptive name for this type of equipment

        :return: String long name for this equipment
        """
        pass

    @abstractmethod
    def short_name(self) -> str:  # pragma: no cover
        """
        Must be overridden to return a brief (max 32 characters) descriptive ID or short name for this type of equipment

        :return: String short name for this equipment
        """
        pass

    @abstractmethod
    def headers(self) -> ColumnHeaderArray:  # pragma: no cover
        """
        Must be overridden to return a set of ColumnHeader instances that define the catalog data for this type of
        equipment

        :return: List of ColumnHeader instances for this equipment
        """
        pass

    @abstractmethod
    def get_required_constant_parameters(self) -> List[BaseValueWithUnit]:  # pragma: no cover
        # TODO: I think this should just return unit types and names, right?
        """
        Must be overridden to return a set of constant/fixed/rated parameters for this type of equipment

        :return: List of BaseValueWithUnits (for now)
        """
        pass

    @abstractmethod
    def set_required_constant_parameter(self, parameter_name: str, new_value: float) -> None:  # pragma: no cover
        """
        Must be overridden to set a single parameter on this equipment instance, accessing it by string name.
        Basically, this function is a map from each of the constant parameter strings.

        :param parameter_name: Name of the parameter to set, as retrieved from `required_constant_parameters`
        :param new_value: The new floating point value to set as the fixed parameter value, should be in proper units
        :return: Nothing
        """
        pass

    @abstractmethod
    def to_eplus_idf_object(self) -> str:  # pragma: no cover
        """
        Must be overridden to return a fully filled out EnergyPlus IDF object for this type of equipment

        :return: String IDF representation
        """
        pass

    @abstractmethod
    def to_parameter_summary(self) -> str:  # pragma: no cover
        """
        Must be overridden to return a fully filled out free form parameter summary for this type of equipment

        :return: String parameter summary representation
        """
        pass

    @abstractmethod
    def to_eplus_epjson_object(self) -> str:  # pragma: no cover
        """
        Must be overridden to return a fully filled out EnergyPlus EpJSON object for this type of equipment

        :return: String EpJSON representation
        """
        pass

    @abstractmethod
    def get_number_of_progress_steps(self) -> int:  # pragma: no cover
        """
        Must be overridden to return the number of progress increment steps expected during the parameter gen process

        :return: Integer number of progress increment calls expected during processing
        """
        pass

    @abstractmethod
    def minimum_data_points_for_generation(self) -> int:  # pragma: no cover
        """
        Must be overridden to return the minimum number of data points required for generation.
        This is nominally the same as the number of coefficients to be found during curve fitting, but could be set
        higher if more would be necessary.

        :return: Integer number of required data points
        """
        pass

    @abstractmethod
    def generate_parameters(
            self, data_manager, cb_progress_increment: Callable, cb_progress_done: Callable
    ):  # pragma: no cover
        """
        Must be overridden to do the actual processing of parameters.  Most of these will follow a similar pattern of
        taking the generic catalog data manager's final data set, creating meaningful data arrays in this equipment
        instance, using SciPy to perform curve fitting, and finally calculating predicted model outputs from the
        generated coefficients.

        :param data_manager: A fully filled out catalog data manager instance
        :param cb_progress_increment: A callback function to alert the calling form/thread to increment progress.
                                      This callback should not take any extra arguments.
        :param cb_progress_done: A callback function to alert the calling form/thread that the process is complete.
                                 This callback should accept a boolean success flag and a string error message as args.
        :return: Nothing
        """
        pass

    @abstractmethod
    def get_absolute_plot_data(self) -> Tuple:  # pragma: no cover
        """
        Must be overridden to return a tuple of plot data for the raw catalog data comparison plot.  Typically, this
        will be pairs of plot data with catalog data as points and matching model output as lines of the same color.

        :return: A tuple of inner tuples that contain (string data name, string type either 'line' or 'point', a
                 matplotlib color string such as 'red' or 'blue', and a 1D iterable of data points to plot)
        """
        pass

    @abstractmethod
    def get_error_plot_data(self) -> Tuple:  # pragma: no cover
        """
        Must be overridden to return a tuple of plot data for the % error catalog data comparison plot.  Typically, this
        will be a percent error between catalog and model data for the same dependent variable.

        :return: A tuple of inner tuples that contain (string data name, string type typically 'line', a
                 matplotlib color string such as 'red' or 'blue', and a 1D iterable of data points to plot)
        """
        pass

    # noinspection PyMethodMayBeStatic
    def get_extra_regression_metrics(self) -> Tuple:
        """
        Returns a tuple of regression metrics for the parameter generation process.  By default, this returns an empty
        tuple, but can be overridden to return specifics for each type of equipment.

        :return: A tuple of inner tuples that contain (string metric name/description, floating point value)
        """
        return ()

    @staticmethod
    def fill_eplus_object_format(fields: List[str], form: str) -> str:
        """
        This function takes a list of parameters and field names and a preset EnergyPlus IDF object format and processes
        them into a nicely formed EnergyPlus IDF object.

        :param fields: A list of IDF object parameter values and field names
        :param form: A string format with the right number of {0}, {1], ..., placeholders
        :return: String IDF object
        """
        # TODO: Might want to pass in field values and field names separately
        preferred_spaces = 16
        hanging_indent_string = " "*4
        pads = []
        string_fields = [str(x) for x in fields]
        for f in string_fields:
            this_padding = preferred_spaces - len(f)
            this_padding = max(2, this_padding)
            pads.append(" "*this_padding)
        all_tokens = []
        for f, p in zip(string_fields, pads):
            all_tokens.append(hanging_indent_string + f)
            all_tokens.append(p)
        return form.format(*all_tokens)
