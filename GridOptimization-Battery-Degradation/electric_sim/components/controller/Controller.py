import numpy as np


class PIDController:
    """
    PID Controller in velocity form, used to control the temperature in the house.
    """

    def __init__(self, p, i, d, dt, min_u=0, max_u=0):
        """
        Initializes the PID Controller with given parameters.

        Parameters:
        p: Proportional gain
        i: Integral gain
        d: Derivative gain
        dt: Time step size
        min_u: Minimum value for the output 'u'
        max_u: Maximum value for the output 'u'
        """
        self.dt = np.asarray(dt)
        self.p = np.asarray(p)
        self.i = np.asarray(i)
        self.d = np.asarray(d)
        self.min_u = min_u
        self.max_u = max_u
        self.error = np.zeros((3, 1))  # Initialize error as a zero vector

    def reset_i(self):
        """Resets the integral gain to zero."""
        self.i = 0

    def update(self, err, u):
        """
        Calculates new control moves 'u' from current tracking error 'err'.

        Parameters:
        err: Current tracking error
        u: Control input

        Returns:
        u: Updated control input
        """
        # Update error values
        self.error = np.concatenate(([[err]], self.error[:2]), axis=0)

        # Calculate change in control input
        du = np.dot(self.p * [1 + self.i * self.dt + self.d / self.dt, -1 - (2 * self.d / self.dt), self.d / self.dt],
                    self.error)

        # Update control input
        u = u + du[0]

        # Clip the output 'u' to be within the range [min_u, max_u]
        #u = np.clip(u, self.min_u, self.max_u)

        return u



class BangBangController:
    """
    The BangBang controller class. This is a simple type of controller that switches between two states
    based on the value of the input. It's often used in systems where a simple on/off control is sufficient.
    """

    def __init__(self, initial_state, Y_min, Y_max, U_min, U_max):
        """
        Initialize the BangBang controller.

        Args:
            initial_state: The initial state of the controller.
            Y_min: The lower threshold for the input value.
            Y_max: The upper threshold for the input value.
            U_min: The lower limit for the output value.
            U_max: The upper limit for the output value.
        """
        self.y_min = Y_min
        self.y_max = Y_max
        self.state = initial_state
        self.u_min = U_min
        self.u_max = U_max
        self.u = 0.

    def propagate(self, Y=None):
        """
        Propagate the controller state based on the current input value.

        Args:
            Y: The current input value.

        Returns:
            None
        """
        # If the input is below the lower threshold and the current state is 0, switch the state to 1.
        if (Y < self.y_min) & (self.state == 0):
            self.state = 1
        # If the input is above the upper threshold and the current state is 1, switch the state to 0.
        elif (Y > self.y_max) & (self.state == 1):
            self.state = 0
        # The output is the current state multiplied by the maximum output value.
        self.u = self.state * self.u_max

class BangBangTankElectric:
    """
    BangBang controller for heatpump electric power depending on Tank SOC
    """

    def __init__(self, initial_state, P_el_max, SOC_min=0.2, SOC_max=0.95):
        self.SOC_min = SOC_min
        self.SOC_max = SOC_max
        self.state = initial_state
        self.P_el = 0
        self.P_el_max = P_el_max

    def propagate(self, SOC=None):
        """
        :param SOC: state of charge of the warm water tank
        :return:
        """
        if (SOC < self.SOC_min) & (self.state == 0):
            self.state = 1
        elif (SOC > self.SOC_max) & (self.state == 1):
            self.state = 0

        self.P_el = self.state * self.P_el_max


