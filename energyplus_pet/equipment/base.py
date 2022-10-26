from abc import abstractmethod
from typing import Callable, Dict, List, Tuple

from numpy import sqrt, diag, average
from scipy.optimize import curve_fit

from energyplus_pet.equipment.equip_types import EquipType
from energyplus_pet.equipment.column_header import ColumnHeaderArray
from energyplus_pet.units import UnitType


class BaseEquipment:
    """
    This class represents an abstract piece of equipment to be processed by this library.
    This is primarily a set of abstract methods that define what must be overridden by derived equipment classes.
    Data stored in the equipment class should assume that everything coming from the catalog/correction/rated forms
    are all coming in with the proper calculation units.  The forms won't allow continuing until everything is
    conformed properly.  So equipment specific parameters should be plain float arrays and scalars, not Unit instances.
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

    class RequiredConstantParameter:
        """A minimal class for capturing information to describe fixed/rated/constant parameters"""
        def __init__(self, p_id: str, title: str, description: str, unit_type: UnitType, default_value: float = 0.0):
            """
            Constructor for the instance

            :param p_id: A unique (for this equipment type) string ID for this parameter
            :param title: A brief (short sentence?) title for this variable
            :param description: A longer (long sentence?) description for this variable
            :param unit_type: A UnitType enum instance for this parameter
            :param default_value: An optional default value, should be already in the UnitType's calculation unit
            """
            self.id = p_id
            self.title = title
            self.description = description
            self.unit_type = unit_type
            self.default_value = default_value

    @abstractmethod
    def get_required_constant_parameters(self) -> List[RequiredConstantParameter]:  # pragma: no cover
        """
        Must be overridden to return a set of constant/fixed/rated parameters for this type of equipment

        :return: List of RequiredConstantParameter instances
        """
        pass

    @abstractmethod
    def set_required_constant_parameter(self, parameter_id: str, new_value: float) -> None:  # pragma: no cover
        """
        Must be overridden to set a single parameter on this equipment instance, accessing it by ID.

        :param parameter_id: ID of the parameter to set, as retrieved from `required_constant_parameters`
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
    def fill_eplus_object_format(object_name: str, fields: List[Tuple]) -> str:
        """
        This function takes a list of (field name, parameter) tuples and processes
        them into a nicely formed EnergyPlus IDF object.

        :param object_name: An IDF object name
        :param fields: A list of tuples of the form (field name, field value)
        :return: String IDF object
        """
        form = object_name + ',\n'
        field_names = [x[0] for x in fields]
        field_values = [x[1] for x in fields]
        for i, fn in enumerate(field_names):
            if i == len(field_names) - 1:
                form += "{};{}!-" + fn + '\n'
            else:
                form += "{},{}!-" + fn + '\n'
        preferred_spaces = 16
        hanging_indent_string = " "*4
        pads = []
        string_fields = [str(x) for x in field_values]
        for f in string_fields:
            this_padding = preferred_spaces - len(f)
            this_padding = max(2, this_padding)
            pads.append(" "*this_padding)
        all_tokens = []
        for f, p in zip(string_fields, pads):
            all_tokens.append(hanging_indent_string + f)
            all_tokens.append(p)
        return form.format(*all_tokens)

    @staticmethod
    def do_one_curve_fit(
            eval_function: Callable,
            independent_variable_arrays: Tuple[List[float], ...],
            dependent_variable_array: List[float]
    ) -> Tuple[List[float], float]:
        """
        Performs a curve fit operation given an evaluation function, a tuple of arrays of independent variable data,
        and an array of dependent variable values.

        The functional relationship to be solved is: Y = F(X, A), where:

        * Y is the known original dependent data array, such as an array of catalog heat transfer rates.
        * F is the evaluation function, which can take scalar coefficients & independent variables and calculate a new Y
        * X represents the independent variable data, which are passed into F as a tuple argument for each data point
        * A is a set of coefficients to be solved, which are passed to the function as scalar arguments

        :param eval_function: A function that takes a tuple of independent variable scalars and individual coefficient
                              values as trailing arguments. For example
                              ``def calc_one_output((one_flow_rate, one_inlet_temp), coeff_a, coeff_b) -> float``
                              The function should return the output of the curve evaluation.
        :param independent_variable_arrays: A tuple of arrays of independent variable data, for example
                                            ``(flow_rates_all_data_points, inlet_temp_all_data_points)``
        :param dependent_variable_array: A single array of dependent variable data, for example ``all_outputs: [float]``
        :return: Returns a tuple of two items: first is the actual list of solved parameters, and second is a one-sigma
                 average regression error which can be displayed to describe to the user just how good the curve fit is.
        """
        curve_fit_response = curve_fit(
            eval_function,
            independent_variable_arrays,
            dependent_variable_array
        )
        raw_parameters = curve_fit_response[0]
        calculated_parameters = list(raw_parameters)
        average_err_one_sigma = average(sqrt(diag(curve_fit_response[1])))
        return calculated_parameters, average_err_one_sigma

    @staticmethod
    def eval_curve_at_points(
            eval_function: Callable,
            independent_variable_arrays: Tuple[List[float], ...],
            generated_parameter_array: List[float],
            catalog_output_array: List[float],
    ) -> Tuple[List[float], List[float]]:
        """Evaluates a given curve function at all data points given"""
        num_points = len(catalog_output_array)
        predicated_values = []
        error_values = []
        for i in range(num_points):
            predicated_values.append(eval_function(
                [x[i] for x in independent_variable_arrays],
                *generated_parameter_array
            ))
            error_values.append(
                100.0 * (predicated_values[i] - catalog_output_array[i]) /
                catalog_output_array[i]
            )
        return predicated_values, error_values

    @staticmethod
    def current_eplus_version_object_idf() -> str:
        """Returns a version IDF object string to include in IDF outputs"""
        return BaseEquipment.fill_eplus_object_format('Version', [('Version Identifier', 22.2)])

    @staticmethod
    def current_eplus_version_object_epjson() -> Dict:
        """Returns a version EpJSON object to include in EpJSON outputs"""
        return {'Version': {'Version 1': {'version_identifier': 22.2}}}
