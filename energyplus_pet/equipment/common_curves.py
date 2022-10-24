class CommonCurves:
    """
    This class is just a collection of static curve evaluation functions.
    Several of the pieces of equipment being parameterized here use the same model
    formulation, and there is no need to redefine the evaluation function in each.
    """

    @staticmethod
    def heat_pump_5_coefficient_curve(x, a, b, c, d, e):
        """
        Evaluates:  Y / Y_rated = A + B*(TLI/TLI_R) + C*(TSI/TSI_R) + D*(VLI/VLI_R) + E*(VSI/VSI_R)
        Where Y would represent any of the desired dependent variables, such as Q or Power

        :param x: tuple of independent variables, (TLI/TLI_R, TSI/TSI_R, VLI/VLI_R, VSI/VSI_R)
        :param a: coefficient A in the above equation
        :param b: coefficient B in the above equation
        :param c: coefficient C in the above equation
        :param d: coefficient D in the above equation
        :param e: coefficient E in the above equation
        :return: Scaled dependent variable, such as Q/Q_rated
        """
        return a + b * x[0] + c * x[1] + d * x[2] + e * x[3]

    @staticmethod
    def heat_pump_5_coefficient_curve_raw_value(x, a, b, c, d, e, scale):
        return scale * CommonCurves.heat_pump_5_coefficient_curve(x, a, b, c, d, e)

    @staticmethod
    def heat_pump_6_coefficient_curve(x, a, b, c, d, e, f):
        """
        Evaluates:  Y / Y_rated = A + B*(Tdb/Tdb_R) + C*(Twb/Twb_R) + D*(TSI/TSI_R) + E*(VLI/VLI_R) + F*(VSI/VSI_R)
        Where Y would represent any of the desired dependent variables, such as Q or Power

        :param x: tuple of independent variables, (Tdb/Tdb_R, Twb/Twb_R, TSI/TSI_R, VLI/VLI_R, VSI/VSI_R)
        :param a: coefficient A in the above equation
        :param b: coefficient B in the above equation
        :param c: coefficient C in the above equation
        :param d: coefficient D in the above equation
        :param e: coefficient E in the above equation
        :param f: coefficient F in the above equation
        :return: Scaled dependent variable, such as Q/Q_rated
        """
        return a + b * x[0] + c * x[1] + d * x[2] + e * x[3] + f * x[4]

    @staticmethod
    def heat_pump_6_coefficient_curve_raw_value(x, a, b, c, d, e, f, scale):
        return scale * CommonCurves.heat_pump_6_coefficient_curve(x, a, b, c, d, e, f)
