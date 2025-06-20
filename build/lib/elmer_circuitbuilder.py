"""circuit_builder.py: builds circuit stiffness and damping matrices based on the Tableau Method.
# -----------------------------------------------------------------------------------------------
# Elmer Circuit Builder Library
# Description: This library enables the automatic build of circuits
#              matrices in ElmerFEM format and the .sif file
#              modifications needed to model different types of
#              coils: massive, stranded, and foil.
#
# Electrical Components Available: Voltage and Current Sources,
#                           Resistors, Inductors and Capacitors
# ------------------------------------------------------------------------------------------------
"""
import os
import sys
import numpy as np
from datetime import date
import cmath


class Component:
    """
    Component is a class to represent electrical components.

    Attributes
    ----------
    name : str
        the name of the component e.g. Resistor1.
    pin1 : int
        component positive network node
    pin2 : int
        component negative network node
    value : float
        electrical component value in SI units. e.g. A resistor of value=1 is 1 Ohm
    """

    def __init__(self, name, pin1, pin2, value=None):
        """
        Parameters
        ----------
        name : str
          The name of the electrical component
        pin1 : int
          positive terminal of the component
        pin2 : int
          negative terminal of the component
        value : float, optional
            value of electrical component in SI units. The value is optional.
            If the value is not defined in class, it will have to be defined
            manually in the .sif file. The default value is None.
            A resistor of value=1 is 1 Ohm, A voltage source of value=1 is 1 Volt,
            A current source of value=1 is 1 Ampere, An inductor of value=1 is 1 Henry,
            and A capacitor of value=1 is 1 Farad.

        """
        self.name = name
        self.pin1 = pin1
        self.pin2 = pin2
        self.value = value


class R(Component):
    """R is a derived class of the Component class to represent resistors in Ohms.

    This class is used to build Elmer's circuit stiffness matrix (B-matrix).

    Parameters
    ----------
    name : str
        the name of the component
    pin1 : int
        component positive network node
    pin2 : int
        component negative network node
    value: float
       Resistance value in Ohms
    """

    def __init__(self, name, pin1, pin2, value=None):
        Component.__init__(self, name, pin1, pin2, value)


class V(Component):
    """V is a derived class of the Component class to represent ideal voltage sources in Volt.

    The source value is assigned under Body Force 1 in the .sif file and appropriate contributions
    are assigned to build Elmer's circuit stiffness matrix (B-matrix)

    Parameters
    ----------
    name : str
        the name of the component
    pin1 : int
        component positive network node
    pin2 : int
        component negative network node
    value: float
       Voltage value in Volts
    """

    def __init__(self, name, pin1, pin2, value=None):
        Component.__init__(self, name, pin1, pin2, value)


class I(Component):
    """I is a derived class of the Component class to represent ideal current sources in Ampere.

    The source value is assigned under Body Force 1 in the .sif file and appropriate contributions
    are assigned to build Elmer's circuit stiffness matrix (B-matrix)

    Parameters
    ----------
    name : str
        the name of the component
    pin1 : int
        component positive network node
    pin2 : int
        component negative network node
    value: float
       Current value in Amps
    """

    def __init__(self, name, pin1, pin2, value=None):
        Component.__init__(self, name, pin1, pin2, value)


class L(Component):
    """L is a derived class of the Component class to represent inductors Henry.

    This class is used to build Elmer's circuit A-matrix (damping).

    Parameters
    ----------
    name : str
        the name of the component
    pin1 : int
        component positive network node
    pin2 : int
        component negative network node
    value: float
       Inductance value in Henry
    """

    def __init__(self, name, pin1, pin2, value=None):
        Component.__init__(self, name, pin1, pin2, value)


class C(Component):
    """C is a derived class of the Component class to represent capacitors in Farad.

    This class is used to build Elmer's circuit A-matrix (damping).

    Parameters
    ----------
    name : str
        the name of the component
    pin1 : int
        component positive network node
    pin2 : int
        component negative network node
    value: float
       Capacitance value in Farad
    """

    def __init__(self, name, pin1, pin2, value=None):
        Component.__init__(self, name, pin1, pin2, value)


class ElmerComponent(Component):
    """ElmerComponent is a derived class of the Component class to represent 2D and 3D Coils in Elmer.

    Parameters
    ----------
    name : str
        the name of the component e.g. Resistor1.
    pin1 : int
        component positive network node
    pin2 : int
        component negative network node
    component_number : int
        Elmer component index
    master_body_list : list of int
        List of bodies associated with component_number.
        The list members can be integers associated with Master Bodies
        or strings associated with Master Bodies Name.
    sector : int, optional
        Sector represents the integer associated with Symmetry Coefficient under Elmer's component.
        By default the value is 1, describing the full dimention of the circuit. Change the value
        accordingly depending on the symmetry of the problem at hand. For example if you're modeling
        half of your coil, then the value of sector is 0.5.

    Methods
    -------
    Massive()
        Sets coil_type to "Massive"

    Stranded(number_of_turns, resistance)
        Sets coil_type to "Stranded"

    Foil(umber_of_turns, coil_thickness)
        Sets coil_type to Foil

    is3D()
        Sets dimension to "3D"

    """

    def __init__(self, name, pin1, pin2, component_number=0, master_body_list=None, sector=1):
        Component.__init__(self, name, pin1, pin2)
        if master_body_list is None:
            master_body_list = []
        """
        Parameters
        ----------
        name : str
            the name of the component e.g. Resistor1.
        pin1 : int
            component positive network node
        pin2 : int
            component negative network node
        component_number : int
            Elmer component index
        master_body_list : list of int
            List of bodies associated with component_number.
            The list members can be integers associated with Master Bodies
            or strings associated with Master Bodies Name.
        sector : int, optional
            Sector represents the integer associated with Symmetry Coefficient under Elmer's component.
            By default the value is 1, describing the full dimention of the circuit. Change the value
            accordingly depending on the symmetry of the problem at hand. For example if you're modeling
            half of your coil, then the value of sector is 0.5.
        dimension : str
            Spatial dimension of the finite-element coil. By default it is set to "2D" and it can be
            set to "3D" by using the method is3D()
        coil_type : str
            The coil types are "Massive", "Stranded", "Foil". The default value is "Massive". Methods
            are available to set the coil types: Massive(), Stranded(), Foil()
        """
        self.component_number = component_number
        self.master_bodies = master_body_list
        self.sector = sector
        self.dimension = "2D"
        self.__coil_type = "Massive"
        self.__is_closed = None
        self.__number_turns = 1
        self.__resistance = 0
        self.__coil_thickness = 0
        self.__bnd1 = None
        self.__bnd2 = None

    def massive(self):
        """Sets coil_type as a Massive conductor by assigning appropriate keywords under Component in .sif """
        self.__coil_type = "Massive"

    def stranded(self, number_turns, resistance):
        """Sets coil_type as a "Stranded" conductor by assigning appropriate keywords under Component in .sif

        Parameters
        ----------
        number_turns : float
            Sets number of turns in "Stranded" conductor

        resistance : float
            Sets required resistance value of a single turn.
            For example, it is possible to use the DC Resistance R_dc = l/(sigma*A), where l is the length
            of the wire, sigma the electrical conductivity and A the cross section of the wire.

        """
        self.__coil_type = "Stranded"
        self.__number_turns = number_turns
        self.__resistance = resistance

    def foil(self, number_of_turns, coil_thickness):
        """Sets coil_type as a "Foil" conductor by assigning appropriate keywords under Component in .sif

        Parameters
        ----------
        number_of_turns : float
        Sets number of turns in "Stranded" conductor

        coil_thickness : float
        Sets required thickness value of a single turn.
        For example, it is possible to use the DC Resistance R_dc = l/(sigma*A), where l is the length
        of the wire, sigma the electrical conductivity and A the cross section of the wire.

        """
        self.__coil_type = "Foil winding"
        self.__number_turns = number_of_turns
        self.__coil_thickness = coil_thickness

    def is3D(self):
        """Sets dimension as a "3D" conductor by assigning appropriate keywords under Component in .sif.

        In 3D coils can be open or closed. The default value is closed.

        """
        self.dimension = "3D"

    def isClosed(self):
        """Sets coil type as closed. A closed coil has no terminal boundaries and cuts are needed.
        """
        self.__is_closed = True
        return self.__is_closed

    def isOpen(self, bnd1, bnd2):
        """Sets coil type as open. An open coil requires two terminal boundaries.
        """
        self.__bnd1 = bnd1
        self.__bnd2 = bnd2
        self.__is_closed = False
        return self.__is_closed

        # Getters

    def getCoilType(self):
        """Gets coil type: Massive, Stranded or Foil winding.
        """
        return self.__coil_type

    def getNumberOfTurns(self):
        """Gets number of turns for stranded and foil winding
        """
        return self.__number_turns

    def getResistance(self):
        """Gets resistance in stranded coil
        """
        return self.__resistance

    def getCoilThickness(self):
        """Gets thickness in Foil winding
        """
        return self.__coil_thickness

    def getOpenTerminals(self):
        """Access to boundary terminals defined by isOpen (for open coils)
        """
        return [self.__bnd1, self.__bnd2]

    def getTerminalType(self):
        return self.__is_closed


class Circuit:
    """Circuit class is associated to a circuit index,
    holds the components within circuit and requires a reference node (default=1)"""

    def __init__(self, index, components, ref_node=1):
        """
        Parameters
        ----------
        index : int
            Circuit number. In Elmer you may setup n circuits. The index is associated with the
            current circuit at hand.

        components : Component list
           This parameter holds the components that constitute the electrical network of the circuit at hand.

        ref_node : int, optional
           The reference node is generally addressed as the ground node. If user does not define
           a reference node, it will use the default node number 1.

        """
        self.index = index
        self.components = components
        self.ref_node = ref_node  # default value


def number_of_circuits(ncircuits):
    """Instantiate Circuit objects for every circuit required

    Parameters
    ----------

    ncircuits : int
        Set the total number of circuits

    Returns
    ----------

    c : dict
      Returns a dictionary of Circuit instances

    """
    c = {}
    for i in range(1, ncircuits + 1):
        c[i] = Circuit(i, [])

    return c


def get_component_information(components):
    """ Parses circuit's component information by pins, type and value

    Parameters
    ----------
    components : list of class
        Set the total number of circuits

    Returns
    ----------
    cnode, cmptype, cval : tuple[list of int, list of Component, list of float]
       Returns list of component positive and negative terminal, list of component types and list of component value

    """
    cnode = []  # [n1,n2] # component node
    cmptype = []  # component type
    cval = []  # component value

    for cmp in components:
        cnode.append([cmp.pin1, cmp.pin2])
        cmptype.append(cmp)
        cval.append([cmp.value])

    return cnode, cmptype, cval


def get_num_nodes(components):
    """ Sets the number of terminals in circuit network by collecting the unique node names from components

    Parameters
    ----------
    components : list of Component
        List of component classes in circuit network

    Returns
    ----------
    int
        Returns the number of unique nodes in graph
    """
    # check for unique nodes
    unique_nodes = []

    for component in components:
        if component.pin1 not in unique_nodes:
            unique_nodes.append(component.pin1)
        if component.pin2 not in unique_nodes:
            unique_nodes.append(component.pin2)

    return len(unique_nodes)


def get_num_edges(components):
    """ Sets the number of edges used in the incidence matrix based on the number of components

    Parameters
    ----------
    components : list of class
        List of component classes in circuit network

    Returns
    ----------
    len(components) : int
        The number of components represents the number of edges on matrix
    """
    return len(components)


def get_incidence_matrix(components, num_nodes, num_edges, n_ref):
    """ Populates the incidence matrix A as a directed graph

    The matrix is constructed using nodes to represent rows, and edges columns.
    See: https://en.wikipedia.org/wiki/Incidence_matrix
    The directed graph implies that the direction of each edge is given by the
    nodes, for which you have a positive and a negative terminal for each component.

    Parameters
    ----------
    components : list of Component
        List of component classes in circuit network

    num_nodes : int
        Number of nodes in circuit network graph

    num_edges : int
        Number of edges/components in circuit network graph

    n_ref : int
        Reference ground node in circuit network

    Returns
    ----------
    numpy.ndarray
        Returns numerical incidence matrix

    """
    # use netlist node numbering as indices (n -1 so we can start indexing from 0)
    n1_index = [components[i].pin1 - 1 for i in range(0, num_edges)]
    n2_index = [components[i].pin2 - 1 for i in range(0, num_edges)]

    # dummy vector for indexing in A matrix
    plus_terminal = [i for i in range(0, num_edges)]
    minus_terminal = [i for i in range(0, num_edges)]

    # initialize A matrix
    Amat_plus = np.zeros(shape=(num_nodes, num_edges))
    Amat_minus = np.zeros(shape=(num_nodes, num_edges))

    for i, j in zip(n1_index, plus_terminal):
        Amat_plus[i][j] = 1

    for i, j in zip(n2_index, minus_terminal):
        Amat_minus[i][j] = -1

    # Incident matrix by adding the negative and positive nodes
    Amat_comp = Amat_plus + Amat_minus

    # Remove row of Amat_comp (Linear Independent Matrix)
    Amat = np.delete(Amat_comp, n_ref - 1, 0)  # remove GND/Ref node row
    return Amat


def get_incidence_matrix_str(components, numnodes, numedges, n_ref):
    """ Populates the string incidence matrix A as a directed graph

    The matrix is constructed using nodes to represent rows, and edges columns.
    See: https://en.wikipedia.org/wiki/Incidence_matrix
    The directed graph implies that the direction of each edge is given by the
    nodes, for which you have a positive and a negative terminal for each component.

    The string/char output enables easy parsing to output elmer's parametrized output file

    Parameters
    ----------
    components : list of Component
        List of component classes in circuit network

    numnodes : int
        Number of nodes in circuit network graph

    numedges : int
        Number of edges/components in circuit network graph

    n_ref : int
        Reference ground node in circuit network

    Returns
    ----------
    Amat_str : numpy.ndarray of `bytes` strings
        Returns string incidence matrix
    """

    # use netlist node numbering as indices (n -1 so we can start indexing from 0)
    n1_index = [components[i].pin1 - 1 for i in range(0, numedges)]
    n2_index = [components[i].pin2 - 1 for i in range(0, numedges)]

    # dummy vector for indexing in A matrix
    plus_terminal = [i for i in range(0, numedges)]
    minus_terminal = [i for i in range(0, numedges)]

    # initialize string matrices
    Amat_plus_str = np.empty((numnodes, numedges), dtype='|S500')
    Amat_minus_str = np.empty((numnodes, numedges), dtype='|S500')

    # initialize zero char in all matrices
    for i in range(0, numnodes):
        for j in range(0, numedges):
            Amat_plus_str[i][j] = ''
            Amat_minus_str[i][j] = ''

    for i, j in zip(n1_index, plus_terminal):
        Amat_plus_str[i][j] = str(1)

    for i, j in zip(n2_index, minus_terminal):
        Amat_minus_str[i][j] = str(-1)

    # Incident matrix by adding the negative and positive nodes
    Amat_comp_str = Amat_plus_str + Amat_minus_str

    Amat_str = np.delete(Amat_comp_str, n_ref - 1, 0)  # remove GND/Ref node row

    return Amat_str


def get_resistance_matrix(components, nedges, indr, indi, indcap):
    """ Populates the resistance matrix R

     R = R_r + R_i + R_cap where the subscripts r, i, and cap refer to the
     resistance contributions from resistor, current generators, and capacitors respectively.

    Parameters
    ----------
    components : list of class
        List of component classes in circuit network

    nedges : int
        Number of edges/components in circuit network graph

    indr : int
        Resistor index

    indi : int
        Ideal current generator index

    indcap : int
        Capacitor index

    Returns
    ----------
    Rmat : numpy.ndarray
        Returns numerical resistance matrix

    """

    Rmat_r = np.zeros(shape=(nedges, nedges))
    Rmat_i = np.zeros(shape=(nedges, nedges))
    Rmat_cap = np.zeros(shape=(nedges, nedges))

    for i in indr:
        Rmat_r[i][i] = components[i].value

    for i in indi:
        Rmat_i[i][i] = 1

    for i in indcap:
        Rmat_cap[i][i] = 1

    # Add all R contributions
    Rmat = Rmat_r + Rmat_i + Rmat_cap

    return Rmat


def get_resistance_matrix_str(components, nedges, indr, indi, indcap):
    """ Populates the resistance matrix R as a characters/string array.

    R = R_r + R_i + R_cap where the subscripts r, i, and cap refer to the
    resistance contributions from resistor, current generators, and capacitors respectively.

    The string/char output enables easy parsing to output elmer's parametrized output file

    Parameters
    ----------
    components : list of Component
        List of component classes in circuit network

    nedges : int
        Number of edges/components in circuit network graph

    indr : int
        Resistor index

    indi : int
        Ideal current generator index

    indcap : int
        Capacitor index

    Returns
    ----------
    Rmat_str : numpy.ndarray of `bytes` strings
        Returns string/char resistance matrix

    """
    # initialize R matrix. R = R_r + R_i + R_cap
    Rmat_r_str = np.empty((nedges, nedges), dtype='|S500')
    Rmat_i_str = np.empty((nedges, nedges), dtype='|S500')
    Rmat_cap_str = np.empty((nedges, nedges), dtype='|S500')

    # initialize zero char in all matrices

    for i in range(0, nedges):
        for j in range(0, nedges):
            Rmat_r_str[i][j] = ''
            Rmat_i_str[i][j] = ''
            Rmat_cap_str[i][j] = ''

    for i in indr:
        Rmat_r_str[i][i] = components[i].name

    for i in indi:
        Rmat_i_str[i][i] = str(1)

    for i in indcap:
        Rmat_cap_str[i][i] = str(1)

    # Add all R contributions
    Rmat_str = Rmat_r_str + Rmat_i_str + Rmat_cap_str

    return Rmat_str


def get_conductance_matrix(nedges, indr, indv, indInd):
    """ Populates the conductance matrix G

     G = G_r + G_v + G_Ind where the subscripts r, v, and Ind refer to the
     resistance contributions from resistor, voltage generators, and inductors respectively.

    Parameters
    ----------
    nedges : int
        Number of edges/components in circuit network graph

    indr : int
        Resistor index

    indv : int
        Ideal voltage generator index

    indInd : int
        Inductor index

    Returns
    ----------
    Gmat : numpy.ndarray
        Returns numerical conductance matrix

    """
    # initialize G matrix. G = G_r + G_v + G_ind
    # (resistor, voltage generators, inductors)
    Gmat_r = np.zeros(shape=(nedges, nedges))
    Gmat_v = np.zeros(shape=(nedges, nedges))
    Gmat_ind = np.zeros(shape=(nedges, nedges))
    Gmat_v_re = np.zeros(shape=(nedges, nedges))
    Gmat_v_im = np.zeros(shape=(nedges, nedges))

    for i in indr:
        Gmat_r[i][i] = -1

    for i in indv:
        Gmat_v[i][i] = 1

    for i in indInd:
        Gmat_ind[i][i] = 1

    # Add all G contributions
    Gmat = Gmat_r + Gmat_v + Gmat_ind

    return Gmat


def get_conductance_matrix_str(nedges, indr, indv, indInd):
    """ Populates the conductance matrix G as a characters/string array.

    G = G_r + G_v + G_Ind where the subscripts r, V, and Ind refer to the
    resistance contributions from resistor, voltage generators, and inductors respectively.

    The string/char output enables easy parsing to output elmer's parametrized output file

    Parameters
    ----------
    nedges : int
        Number of edges/components in circuit network graph

    indr : int
        Resistor index

    indv : int
        Ideal voltage generator index

    indInd : int
        Inductor index

    Returns
    ----------
    Gmat_str : numpy.ndarray of `bytes` strings
        Returns string/char conductance matrix

    """
    # initialize G matrix. G = G_r + G_v + G_ind
    # (resistor, voltage generators, inductors)
    Gmat_r_str = np.empty((nedges, nedges), dtype='|S500')
    Gmat_v_str = np.empty((nedges, nedges), dtype='|S500')
    Gmat_ind_str = np.empty((nedges, nedges), dtype='|S500')

    # initialize zero char in all matrices
    for i in range(0, nedges):
        for j in range(0, nedges):
            Gmat_r_str[i][j] = ''
            Gmat_v_str[i][j] = ''
            Gmat_ind_str[i][j] = ''

    for i in indr:
        Gmat_r_str[i][i] = str(-1)

    for i in indv:
        Gmat_v_str[i][i] = str(1)

    for i in indInd:
        Gmat_ind_str[i][i] = str(1)

    # Add all R contributions
    Gmat_str = Gmat_r_str + Gmat_v_str + Gmat_ind_str

    return Gmat_str


def get_inductance_matrix(components, nedges, indInd):
    """ Populates the inductance matrix L

    Parameters
    ----------
    components : list of Component
        List of component classes in circuit network

    nedges : int
        Number of edges/components in circuit network graph

    indInd : int
        Inductor index

    Returns
    ----------
    Lmat : numpy.ndarray
        Returns numerical inductance matrix

    """
    # initialize L matrix.
    Lmat = np.zeros(shape=(nedges, nedges))

    for i in indInd:
        Lmat[i][i] = -components[i].value

    return Lmat


def get_inductance_matrix_str(components, nedges, indInd):
    """ Populates the inductance matrix L as a characters/string array.

    The string/char output enables easy parsing to output elmer's parametrized output file

    Parameters
    ----------
    components : list of Component
        List of component classes in circuit network

    nedges : int
        Number of edges/components in circuit network graph

    indInd : int
        Inductor index

    Returns
    ----------
    Lmat_str : numpy.ndarray of `bytes` strings
        Returns string/char inductance matrix
    """
    # initialize L matrix.
    Lmat_str = np.empty((nedges, nedges), dtype='|S500')

    # initialize zero char in all matrices
    for i in range(0, nedges):
        for j in range(0, nedges):
            Lmat_str[i][j] = ''

    for i in indInd:
        Lmat_str[i][i] = "-" + components[i].name

    return Lmat_str


def get_capacitance_matrix(components, nedges, indcap):
    """ Populates the capacitance matrix C

    Parameters
    ----------
    components : list of Component
        List of component classes in circuit network

    nedges : int
        Number of edges/components in circuit network graph

    indcap : int
        Capacitor index

    Returns
    ----------
    Cmat : numpy.ndarray
        Returns numerical capacitance matrix
    """
    # initialize C matrix.
    Cmat = np.zeros(shape=(nedges, nedges))

    for i in indcap:
        Cmat[i][i] = -components[i].value

    return Cmat


def get_capacitance_matrix_str(components, nedges, indcap):
    """ Populates the capacitance matrix C as a characters/string array.

    The string/char output enables easy parsing to output elmer's parametrized output file

    Parameters
    ----------
    components : list of Component
        List of component classes in circuit network

    nedges : int
        Number of edges/components in circuit network graph

    indcap : int
        Capacitor index

    Returns
    ----------
    Cmat_str : numpy.ndarray of `bytes` strings
        Returns string/char capacitance matrix
    """
    # initialize L matrix.
    Cmat_str = np.empty((nedges, nedges), dtype='|S500')

    # initialize zero char in all matrices
    for i in range(0, nedges):
        for j in range(0, nedges):
            Cmat_str[i][j] = ''

    for i in indcap:
        Cmat_str[i][i] = "-" + components[i].name

    return Cmat_str


def get_rhs(components, nedges, indi, indv):
    """ Populates Source Vector/ Right Hand Side (RHS) according to ideal sources in components list

    rhs = rhs_i + rhs_v, where subscripts i and v represent the current and voltage sources in electrical network
    Note that source vector can account for complex (rhs = complex(rhs_i) + complex(rhs_v)) sources

    Parameters
    ----------
    components : list of Component
        List of component classes in circuit network

    nedges : int
        Number of edges/components in circuit network graph

    indi : int
        Ideal current source index

    indv : int
        Ideal voltage source index

    Returns
    ----------
    rhs : numpy.ndarray
        Returns numerical source vector
    """
    # initialize RHS vector. RHS = RHS_i + RHS_v
    # (current source, voltage source)
    rhs_v = np.zeros(shape=(nedges, 1))
    rhs_i = np.zeros(shape=(nedges, 1))

    complex_switch = True  # used to create separate real and imag rhs

    for i in indi:
        if isinstance(components[i].value, complex):

            if complex_switch:
                rhs_i_re = np.zeros(shape=(nedges, 1))
                rhs_i_im = np.zeros(shape=(nedges, 1))
                complex_switch = False

            rhs_i_re[i] = np.real(components[i].value)
            rhs_i_im[i] = np.imag(components[i].value)

            rhs_i = rhs_i_re + 1j * rhs_i_im

        else:
            rhs_i[i] = components[i].value

    complex_switch = True  # used to create separate real and imag rhs
    for i in indv:
        if isinstance(components[i].value, complex):
            if complex_switch:
                rhs_v_re = np.zeros(shape=(nedges, 1))
                rhs_v_im = np.zeros(shape=(nedges, 1))
                complex_switch = False

            rhs_v_re[i] = -np.real(components[i].value)
            rhs_v_im[i] = -np.imag(components[i].value)

            rhs_v = rhs_v_re + 1j * rhs_v_im
        else:
            rhs_v[i] = -components[i].value

    rhs = rhs_v + rhs_i

    return rhs


def get_rhs_str(components: list, nedges: int, indi: list, indv: list):
    """ Populates Source Vector/ Right Hand Side (RHS) according to ideal sources in components list as a str/char

    rhs = rhs_i + rhs_v, where subscripts i and v represent the current and voltage sources in electrical network
    Note that source vector can account for complex (rhs = str(complex(rhs_i) + complex(rhs_v))) sources

    Parameters
    ----------
    components : list of Component
        List of component classes in circuit network

    nedges : int
        Number of edges/components in circuit network graph

    indi : list
        Ideal current source index

    indv : list
        Ideal voltage source index

    Returns
    ----------
    rhs : numpy.ndarray of `bytes` strings
        Returns string/char source vector
    """

    # initialize RHS vector. RHS = RHS_i + RHS_v
    # (current source, voltage source)
    rhs_v_str = np.empty((nedges, 1), dtype='|S500')

    rhs_i_str = np.empty((nedges, 1), dtype='|S500')

    # initialize zero char in all matrices
    for i in range(0, nedges):
        rhs_v_str[i] = ''
        rhs_i_str[i] = ''

    # complex_switch = True  # used to create separate real and imag rhs

    for i in indi:
        rhs_i_str[i] = components[i].name

    for i in indv:
        rhs_v_str[i] = '-' + components[i].name  # -value

    rhs_str = rhs_v_str + rhs_i_str

    return rhs_str


def get_indices(components):
    """ Creates indices for each component to assist in matrix population (incidence and component)

    Parameters
    ----------
    components : list of Component
        List of component classes in circuit network

    Returns
    ----------
    indr, indv, indi, indInd, indcap, indcelm : tuple[int, int, int, int, int, int]
        Returns indices for each electrical component: resistor, ideal voltage, ideal current,
        ideal inductor, capacitors and elmer components.
    """
    # create indices per component
    indr = []
    indv = []
    indi = []
    indInd = []
    indcap = []
    indcelm = []

    for i, comp in enumerate(components):
        if isinstance(comp, R):
            indr.append(i)
        if isinstance(comp, V):
            indv.append(i)
        if isinstance(comp, I):
            indi.append(i)
        if isinstance(comp, L):
            indInd.append(i)
        if isinstance(comp, C):
            indcap.append(i)
        if isinstance(comp, ElmerComponent):
            indcelm.append(i)

    return indr, indv, indi, indInd, indcap, indcelm


def get_tableau_matrix(Amat, Rmat, Gmat, Lmat, Cmat, fvec, num_nodes, num_edges):
    """ Populates circuit network matrices according to the Sparse Tableau Method

    Parameters
    ----------
    Amat : numpy.ndarray
        Incidence matrix

    Rmat : numpy.ndarray
        Resistance matrix

    Gmat : numpy.ndarray
        Conductance matrix

    Lmat : numpy.ndarray
        Inductance matrix

    Cmat : numpy.ndarray
        Conductance matrix

    fvec : numpy.ndarray
        Numerical incidence matrix

    num_nodes : int
        Number of nodes in circuit network graph

    num_edges : int
        Number of edges/components in circuit network graph

    Returns
    ----------
    Mmat1, Mmat2, bvec : tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]
        Returns stiffness matrix (Mmat1), damping matrix (Mmat2) and source vector (bvec).
        In Elmer A = Mmat1, B = Mmat2 and source = bvec
    """

    M_kcl = np.block([Amat, np.zeros(shape=(num_nodes - 1, num_edges)), np.zeros(shape=(num_nodes - 1, num_nodes - 1))])
    M_kvl = np.block([np.zeros(shape=(num_edges, num_edges)), -np.eye(num_edges, num_edges), np.transpose(Amat)])
    M_comp = np.block([Rmat, Gmat, np.zeros(shape=(num_edges, num_nodes - 1))])

    # B matrix in Elmer
    Mmat1 = np.block([[M_kcl], [M_kvl], [M_comp]])

    # Source term
    bvec = np.block([[np.zeros(shape=(num_nodes - 1, 1))], [np.zeros(shape=(num_edges, 1))], [fvec]])

    # A matrix in Elmer
    Mmat2 = np.block([[np.zeros(shape=(num_edges + (num_nodes - 1), 2 * num_edges + (num_nodes - 1)))],
                      [Lmat, Cmat, np.zeros(shape=(num_edges, num_nodes - 1))]])

    return Mmat1, Mmat2, bvec


def get_tableau_matrix_str(Amat_str, Rmat_str, Gmat_str, Lmat_str, Cmat_str, fvec_str, numnodes, numedges):
    """ Populates circuit network matrices according to the Sparse Tableau Method as str/char array

    Parameters
    ----------
    Amat_str : numpy.ndarray of `bytes` strings
        Incidence matrix

    Rmat_str : numpy.ndarray of `bytes` strings
        Resistance matrix

    Gmat_str : numpy.ndarray of `bytes` strings
        Conductance matrix

    Lmat_str : numpy.ndarray of `bytes` strings
        Inductance matrix

    Cmat_str : numpy.ndarray of `bytes` strings
        Conductance matrix

    fvec_str : numpy.ndarray of `bytes` strings
        Numerical incidence matrix

    numnodes : int
        Number of nodes in circuit network graph

    numedges : int
        Number of edges/components in circuit network graph

    Returns
    ----------
    Mmat1, Mmat2, bvec : tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]
        Returns stiffness matrix (Mmat1), damping matrix (Mmat2) and source vector (bvec).
        In Elmer A = Mmat1, B = Mmat2 and source = bvec
    """

    # Set up matrices based on Kirchoff's Laws and Component Equations
    M_kcl_str = np.block([Amat_str, np.zeros(shape=(numnodes - 1, numedges)),
                          np.zeros(shape=(numnodes - 1, numnodes - 1))])
    M_kvl_str = np.block([np.zeros(shape=(numedges, numedges)), -np.eye(numedges, numedges),
                          np.transpose(Amat_str.copy())])
    M_comp_str = np.block([Rmat_str, Gmat_str, np.zeros(shape=(numedges, numnodes - 1))])

    # B matrix in Elmer
    Mmat1_str = np.block([[M_kcl_str], [M_kvl_str], [M_comp_str]])

    # Source term
    for i in range(len(fvec_str)):
        if fvec_str[i].item().decode() == '' or fvec_str[i].item().decode() == '0.0' or fvec_str[
            i].item().decode() == '-0.0':
            fvec_str[i] = str(0)
    bvec_str = np.block([[np.zeros(shape=(numnodes - 1, 1))], [np.zeros(shape=(numedges, 1))], [fvec_str]])

    # redundant cleanup for int format looks
    for i in range(len(bvec_str)):
        if bvec_str[i][0].item().decode() == '' or bvec_str[i][0].item().decode() == '0.0' or bvec_str[i][
            0].item().decode() == '-0.0':
            bvec_str[i][0] = str(0)

    # A matrix in Elmer
    Mmat2_str = np.block([[np.zeros(shape=(numedges + (numnodes - 1), 2 * numedges + (numnodes - 1)))],
                          [Lmat_str, Cmat_str, np.zeros(shape=(numedges, numnodes - 1))]])

    rows, cols = Mmat1_str.shape
    for i in range(0, rows):
        for j in range(0, cols):
            if Mmat1_str[i][j].item().decode() == '' or Mmat1_str[i][j].item().decode() == '-0.0' \
                    or Mmat1_str[i][j].item().decode() == '0.0':
                Mmat1_str[i][j] = str(0)
            if Mmat1_str[i][j].item().decode() == '-1.0':
                Mmat1_str[i][j] = str(-1)
            if Mmat1_str[i][j].item().decode() == '1.0':
                Mmat1_str[i][j] = str(1)

    rows, cols = Mmat2_str.shape
    for i in range(0, rows):
        for j in range(0, cols):
            if Mmat2_str[i][j].item().decode() == '' or Mmat2_str[i][j].item().decode() == '-0.0' \
                    or Mmat2_str[i][j].item().decode() == '0.0':
                Mmat2_str[i][j] = str(0)
            if Mmat2_str[i][j].item().decode() == '-1.0':
                Mmat2_str[i][j] = str(-1)
            if Mmat2_str[i][j].item().decode() == '1.0':
                Mmat2_str[i][j] = str(1)

    return Mmat1_str, Mmat2_str, bvec_str


def solve_system(M1, M2, b, freq=50):
    """ Solve a linear matrix equation using numpy.linalg.solve¶

    Parameters
    ----------
    M1 : numpy.ndarray
        stiffness matrix equations (resistance, incidence, generators)

    M2 : numpy.ndarray
        damping matrix equations (inductors, capacitors)

    b : numpy.ndarray
        source vector

    freq : float, optional
        excitation frequency

    Returns
    ----------
    numpy.ndarray
        Returns the solution vector

    """

    iw = 1j * 2 * np.pi * freq

    if np.all((M2 == 0)):
        lhs = M1
    else:
        lhs = M1 + iw * M2

    rhs = b

    return np.linalg.solve(lhs, rhs)


def elmer_format_matrix(M1_str, M2_str, b_str, vcomp_rows, zero_rows):
    """
    Takes the string/char sparse tableau matrices and source vector and parses it into Elmer's format

    In order to couple lumped circuit networks to Elmer, the voltage rows for Elmer Components
    need to be empty. This way the matrix is completed by using the Component keyword in the .sif file.
    This function ensures that the vcomp_rows are also zero_rows by moving rows systematically.

    Parameters
    ----------
    M1_str : numpy.ndarray of `bytes` strings
        stiffness matrix equations (resistance, incidence, generators)

    M2_str : numpy.ndarray of `bytes` strings
        damping matrix equations (inductors, capacitors)

    b_str : numpy.ndarray of `bytes` strings
        source vector

    vcomp_rows : float, optional
        Voltage component rows

    zero_rows : float, optional
        Rows that are zero when the system of equation is built prior to parsing into Elmer's format

    Returns
    ----------
    elmer_Amat, elmer_Bmat, elmer_source : tuple(numpy.ndarray, numpy.ndarray, numpy.ndarray)
        Elmer's stiffness (B) matrix, damping (A) matrix and source vector
    """

    # elmer matrices don't allow entries in v_component(n) rows

    # ----------------------------------------------------------------------------
    #   Swap rows in M matrix to comply with vcomp_rows = 0 in B matrix in Elmer
    # ----------------------------------------------------------------------------

    elmer_Bmat = np.copy(M1_str)
    elmer_source = np.copy(b_str)
    elmer_Amat = np.copy(M2_str)

    # swap zero rows to Vcomp rows
    for zrow, vcomprow in zip(zero_rows, vcomp_rows):
        elmer_Bmat[[zrow, vcomprow]] = elmer_Bmat[[vcomprow, zrow]]
        elmer_Amat[[zrow, vcomprow]] = elmer_Amat[[vcomprow, zrow]]
        elmer_source[[zrow, vcomprow]] = elmer_source[[vcomprow, zrow]]

    return elmer_Amat, elmer_Bmat, elmer_source


def create_unknown_name(components, ref_node, circuit_number):
    """
    Takes the string/char sparse tableau matrices and source vector and parses it into Elmer's format

    In order to couple lumped circuit networks to Elmer, the voltage rows for Elmer Components
    need to be empty. This way the matrix is completed by using the Component keyword in the .sif file.
    This function ensures that the vcomp_rows are also zero_rows by moving rows systematically.

    Parameters
    ----------
    components : list of Component
        List of component classes in circuit network

    ref_node : int
        The reference node is addressed as the ground node.

    circuit_number : int
        Circuit index tag

    Returns
    ----------
    unknown_names, v_comp_rows : tuple[list of str, list of int]
        returns list of strings containing the names of the unknowns (DoF) and a list with the component voltage
        row indices
    """
    v_comp_rows = []
    unknown_names = []
    unknown_nodes = []

    # only include pins that are unknown (remove reference)
    for component in components:
        if (component.pin1 not in unknown_nodes) and (component.pin1 != ref_node):
            unknown_nodes.append(component.pin1)
        if (component.pin2 not in unknown_nodes) and (component.pin2 != ref_node):
            unknown_nodes.append(component.pin2)

    # create current I entries
    for i, component in enumerate(components):
        if isinstance(component, ElmerComponent):
            current_string = "\"i_component(" + str(component.component_number) + ")\""
        else:
            current_string = "\"i_" + component.name + "\""
        unknown_names.append(current_string)

    # create current V entries
    for i, component in enumerate(components):
        if isinstance(component, ElmerComponent):
            voltage_string = "\"v_component(" + str(component.component_number) + ")\""
        else:
            voltage_string = "\"v_" + component.name + "\""
        unknown_names.append(voltage_string)

    # create current potential entries
    for i, node_name in enumerate(unknown_nodes):
        node_string = "\"u_" + str(node_name) + "_circuit_" + str(circuit_number) + "\""
        unknown_names.append(node_string)

    # v_comp rows
    for i, name in enumerate(unknown_names):
        if "v_component(" in name:
            v_comp_rows.append(i)

    return unknown_names, v_comp_rows


def get_zero_rows(M1, M2, b):
    """
    Takes the sparse tableau matrices and source vector and outputs the row indices for rows populated with zeros

    Parameters
    ----------
    M1 : numpy.ndarray
        Stiffness matrix

    M2 : numpy.ndarray
        Damping matrix

    b : numpy.ndarray
        Source vector

    Returns
    ----------
    zero_row_index : list of int
        Returns a index list of zero populated rows
    """

    zero_rows_matrix = np.copy(M1) + np.copy(M2) + np.copy(b)

    check_zeros = np.where(~zero_rows_matrix.any(axis=1))[0]

    # changing format to list for uniformity
    zero_row_index = [zr for zr in check_zeros]

    return zero_row_index


def get_zero_rows_str(M1_str, M2_str, b_str):
    """
    Takes the string sparse tableau matrices and source vector and outputs the row indices for rows populated with zeros

    Parameters
    ----------
    M1_str : numpy.ndarray of `bytes` strings
        String stiffness matrix

    M2_str : numpy.ndarray of `bytes` strings
        String damping matrix

    b_str : numpy.ndarray of `bytes` strings
        String source vector

    Returns
    ----------
    zero_row_index : list of int
        Returns a index list of zero populated rows
    """

    rows, cols = M1_str.shape
    zero_row_index = []
    zero_counter = 0
    for i in range(rows):
        for j in range(cols):
            m1_ = M1_str[i][j].item().decode().strip("-")
            m2_ = M2_str[i][j].item().decode().strip("-")

            zero_condition1 = (m1_ == str(0.0) or m1_ == str(0)) and (m2_ == str(0.0) or m2_ == str(0))

            if zero_condition1:
                zero_counter += 1

        b_ = b_str[i][0].item().decode().strip("-")

        zero_condition2 = (b_ == str(0.0) or b_ == str(0))

        if (zero_counter == cols) and zero_condition2:
            zero_row_index.append(i)

        zero_counter = 0

    return zero_row_index


def get_file_header(circuit, generate_timestep=True) -> str:
    """
    Creates circuit file and writes the number of circuits and date of generation

    Parameters
    ----------
    circuit : dict
       A dictionary of Circuit instances

    ofile : str
        output file name

    Returns
    ----------
    None
    """

    header = ""

    for i in range(1, len(circuit) + 1):

        # loop over all circuits
        c = circuit[i]
        components = c.components[0]

        # only run script if there are no elmer components
        check_elmer_instance = [isinstance(components[i], ElmerComponent) for i in range(len(components))]
        check_component_values = [(component.value is None) for component in components]

        # condition that no elmer components in circuit
        isElmerComponent = True in check_elmer_instance
        # isValueNone = True in check_component_values

        # if there are elmer components or there's no value component break the loop
        if not isElmerComponent:
            return 0
    if generate_timestep:
        header += "! -----------------------------------------------------------------------------\n"
        header += "! ElmerFEM Circuit Generated: " + str(date.today().strftime("%B %d, %Y")) + "\n"
        header += "! -----------------------------------------------------------------------------\n"
        header += "\n"
    header += "! -----------------------------------------------------------------------------\n"
    header += "! Number of Circuits in Model\n"
    header += "! -----------------------------------------------------------------------------\n"
    header += "$ Circuits = " + str(len(circuit)) + "\n"
    header += ""

    return header


def get_matrix_initialization(c, num_variables) -> str:
    """
    Writes zero entries on matrix definitions in circuit file

    Parameters
    ----------
    c : dict
        A dictionary of Circuit instances

    num_variables : int
        number of degrees of freedom / unknowns to define nxn matrix
    ofile : str
        output file name

    Returns
    ----------
    None
    """
    matrix_block = ""

    # Write matrices in Elmer Format
    matrix_block += "! -----------------------------------------------------------------------------\n"
    matrix_block += "! Matrix Size Declaration and Matrix Initialization\n"
    matrix_block += "! -----------------------------------------------------------------------------\n"
    matrix_block += "$ C." + str(c.index) + ".variables = " + str(num_variables) + "\n"
    matrix_block += "$ C." + str(c.index) + ".perm = zeros(" + "C." + str(c.index) + ".variables" + ")\n"
    matrix_block += "$ C." + str(c.index) + ".A = zeros(" + "C." + str(c.index) + ".variables," + "C." + str(
        c.index) + ".variables" + ")\n"
    matrix_block += "$ C." + str(c.index) + ".B = zeros(" + "C." + str(c.index) + ".variables," + "C." + str(
        c.index) + ".variables" + ")\n"
    matrix_block += "\n"

    return matrix_block


def get_unknown_vector(c, unknown_names) -> str:
    """
    Writes the unknown vector in circuit file

    Parameters
    ----------
    c : dict
        A dictionary of Circuit instances

    unknown_names : list of str
        Name of degrees of freedom / Unknowns in n entry vector

    ofile : str
        output file name

    Returns
    ----------
    None
    """
    definitions = ""

    # Write matrices in Elmer Format
    definitions += "! -----------------------------------------------------------------------------\n"
    definitions += "! Dof/Unknown Vector Definition\n"
    definitions += "! -----------------------------------------------------------------------------\n"

    for i, name in enumerate(unknown_names):
        definitions += "$ C." + str(c.index) + ".name." + str(i + 1) + " = " + name + "\n"

    definitions += "\n"

    return definitions


def get_source_vector(c, source_vector, postfix="_Source") -> str:
    """
    Writes source vector in circuit file

    Parameters
    ----------
    postfix
    c : dict
        A dictionary of Circuit instances

    source_vector : list of str
        Name of source terms in n entry vector

    Returns
    ----------
    None
    """
    definitions = ""

    definitions += "! -----------------------------------------------------------------------------\n"
    definitions += "! Source Vector Definition\n"
    definitions += "! -----------------------------------------------------------------------------\n"
    for i, source_name in enumerate(source_vector):
        if (source_name[0].item().decode() != str(0.0)) and (source_name[0].item().decode() != str(0)):
            definitions += "$ C." + str(c.index) + ".source." + str(i + 1) + " = \"" + source_name[
                0].item().decode().strip(
                "-") + postfix + "\"\n"
    definitions += "\n"

    return definitions


def get_kcl_equations(c, num_nodes, num_variables, elmer_Amat, elmer_Bmat) -> str:
    """
    Writes Kirchhoff Current Law (KCL) in circuit file

    Parameters
    ----------
    c : dict
        A dictionary of Circuit instances

    num_nodes : int
        number of unique nodes in circuit network

    num_variables : int
        number of variables/uknowns in circuit definition

    elmer_Amat : numpy.ndarray of `bytes` strings
        Elmer format damping matrix

    elmer_Bmat : numpy.ndarray of `bytes` strings
        Elmer format stiffness matrix

    Returns
    ----------
    None
    """

    equations = ""

    equations += "! -----------------------------------------------------------------------------\n"
    equations += "! KCL Equations\n"
    equations += "! -----------------------------------------------------------------------------\n"

    print(elmer_Bmat)

    for i in range(num_nodes - 1):
        for j in range(num_variables):
            if (elmer_Bmat[i][j].item().decode() != str(0)) and (elmer_Bmat[i][j].item().decode() != str(0.0)):
                equations += "$ C." + str(c.index) + ".B(" + str(i) + "," + str(j) + ")" + " = " + str(
                    elmer_Bmat[i][j].item().decode()) + "\n"

    for i in range(num_nodes - 1):
        for j in range(num_variables):
            if (elmer_Amat[i][j].item().decode() != str(0)) and (elmer_Amat[i][j].item().decode() != str(0.0)):
                equations += "$ C." + str(c.index) + ".A(" + str(i) + "," + str(j) + ")" + " = " + str(
                    elmer_Amat[i][j].item().decode()) + "\n"

    equations += "\n"
    return equations


def get_kvl_equations(c, num_nodes, num_edges, num_variables, elmer_Amat, elmer_Bmat, unknown_names):
    """
    Writes Kirchhoff Voltage Law (KVL) in circuit file

    Parameters
    ----------
    c : dict
        A dictionary of Circuit instances

    num_nodes : int
        number of unique nodes in circuit network

    num_edges : int
        number of edges/components in circuit network

    num_variables : int
        number of variables/uknowns in circuit definition

    elmer_Amat : numpy.ndarray of `bytes` strings
        Elmer format damping matrix

    elmer_Bmat : numpy.ndarray of `bytes` strings
        Elmer format stiffness matrix

    unknown_names : list of str
        Name of degrees of freedom / Unknowns in n entry vector

    ofile : str
        output file name

 Returns
 ----------
 None
 """

    equations = ""

    range_init = num_nodes - 1

    # this trick switches all source voltage signs
    # to comply with Elmer's convention
    source_names = []
    components = c.components[0]
    for component in components:
        if type(component) == I:
            source_names.append(component.name)

    source_sign_index = []
    for i, name in enumerate(unknown_names):
        if name.strip('"').strip("i_") in source_names:
            source_sign_index.append(i)
        else:
            source_sign_index.append(None)

    equations += "! -----------------------------------------------------------------------------\n"
    equations += "! KVL Equations\n"
    equations += "! -----------------------------------------------------------------------------\n"

    for i in range(range_init, num_edges + range_init):
        for j in range(num_variables):
            if (elmer_Bmat[i][j].item().decode().strip("-") != str(0)) and (
                    elmer_Bmat[i][j].item().decode().strip("-") != str(0.0)):
                kvl_without_decimal = elmer_Bmat[i][j].item().decode().split(".")[0]
                if j == source_sign_index[j]:
                    if "-" in kvl_without_decimal:
                        equations += "$ C." + str(c.index) + ".B(" + str(i) + "," + str(j) + ")" + " = " + str(
                            kvl_without_decimal.strip("-")) + "\n"
                    else:
                        equations += "$ C." + str(c.index) + ".B(" + str(i) + "," + str(j) + ")" + " = -" + str(
                            kvl_without_decimal.strip("-")) + "\n"
                else:
                    equations += "$ C." + str(c.index) + ".B(" + str(i) + "," + str(j) + ")" + " = " + str(
                        kvl_without_decimal) + "\n"

    for i in range(range_init, num_edges + range_init):
        for j in range(num_variables):
            if (elmer_Amat[i][j].item().decode().strip("-") != str(0)) and (
                    elmer_Amat[i][j].item().decode().strip("-") != str(0.0)):
                equations += "$ C." + str(c.index) + ".A(" + str(i) + "," + str(j) + ")" + " = " + str(
                    elmer_Amat[i][j].item().decode()) + "\n"

    return equations


def get_component_equations(c, num_nodes, num_edges, num_variables, elmer_Amat, elmer_Bmat) -> str:
    """
    Writes Component Equations in circuit file.

    Parameters
    ----------
    c : dict
        A dictionary of Circuit instances

    num_nodes : int
        number of unique nodes in circuit network

    num_edges : int
        number of edges/components in circuit network

    num_variables : int
        number of variables/uknowns in circuit definition

    elmer_Amat : numpy.ndarray of `bytes` strings
        Elmer format damping matrix

    elmer_Bmat : numpy.ndarray of `bytes` strings
        Elmer format stiffness matrix

    ofile : str
        output file name

 Returns
 ----------
 None
 """

    equations = ""

    range_init = num_nodes - 1 + num_edges

    equations += "! -----------------------------------------------------------------------------\n"
    equations += "! Component Equations\n"
    equations += "! -----------------------------------------------------------------------------\n"

    for i in range(range_init, num_edges + range_init):
        for j in range(num_variables):
            if (elmer_Bmat[i][j].item().decode().strip("-") != str(0)) and (
                    elmer_Bmat[i][j].item().decode().strip("-") != str(0.0)):
                equations += "$ C." + str(c.index) + ".B(" + str(i) + "," + str(j) + ")" + " = " + str(
                    elmer_Bmat[i][j].item().decode()) + "\n"

    equations += "\n"

    for i in range(range_init, num_edges + range_init):
        for j in range(num_variables):
            if (elmer_Amat[i][j].item().decode().strip("-") != str(0)) and (
                    elmer_Amat[i][j].item().decode().strip("-") != str(0.0)):
                equations += "$ C." + str(c.index) + ".A(" + str(i) + "," + str(j) + ")" + " = " + str(
                    elmer_Amat[i][j].item().decode()) + "\n"

    equations += "\n"

    return equations


def get_sif_additions(c, source_vector) -> tuple:
    """
    Writes Components as defined in .sif file and collects all circuits sources on a list

    Components are indexed blocks in Elmer's .sif file requiring
    keywords to define the coil modeling type in the finite element model.

    Parameters
    ----------
    c : dict
        A dictionary of Circuit instances

    source_vector : list of string
        name of sources in circuit

    ofile : str
        output file name

    Returns
    ----------
    body_force_list : list of str
        Returns an n-entry vector with the names of the sources of every circuit
    """
    additions = ""

    components = c.components[0]

    # split and store components and sources
    source_components = []
    elmer_components = []
    for i, component in enumerate(components):
        if (isinstance(component, I) or isinstance(component, V)) and \
                component not in source_components:
            source_components.append(component)
        if (isinstance(component, ElmerComponent)) and \
                component not in elmer_components:
            elmer_components.append(component)

    # store source parameter value
    source_str_values = []
    for source_val in source_vector:
        if source_val[0].item().decode() != str(0.0) and source_val[0].item().decode() != str(0) \
                and source_val[0].item().decode() not in source_str_values:
            source_str_values.append(source_val[0].item().decode())

    additions += "! -----------------------------------------------------------------------------\n"
    additions += "! Additions in SIF file\n"
    additions += "! -----------------------------------------------------------------------------\n"
    if len(elmer_components) > 0:
        for ecomp in elmer_components:
            additions += "Component " + str(ecomp.component_number) + "\n"
            additions += "  Name = \"" + str(ecomp.name) + "\"\n"

            # split integer and string list members: master bodies, and master bodies name
            str_mbody = []
            str_mb_count = 0
            int_mbody = []
            int_mb_count = 0
            for mbody in ecomp.master_bodies:
                if type(mbody) == str:
                    str_mbody.append(mbody)
                    str_mb_count += 1
                if (type(mbody) == int):
                    int_mbody.append(str(mbody))
                    int_mb_count += 1

            if (str_mbody):
                joined_str_master_names = ", ".join(str_mbody)
                additions += "  Master Bodies Name = " + str(joined_str_master_names) + "\n"
            if (int_mbody):
                joined_str_master_bodies = ", ".join(int_mbody)
                additions += "  Master Bodies(" + str(int_mb_count) + ") = " + str(joined_str_master_bodies) + "\n"
            # ------------------------------------------------------------------------------
            additions += "  Coil Type = \"" + str(ecomp.getCoilType()) + "\"\n"
            if ecomp.getCoilType() == "Stranded":
                additions += "  Number of Turns = Real $ N_" + str(ecomp.name) + "\n"
                additions += "  Resistance = Real $ R_" + str(ecomp.name) + "\n"

            if ecomp.getCoilType() == "Foil winding":
                additions += "  Number of Turns = Real $ N_" + str(ecomp.name) + "\n"
                additions += "  Coil Thickness = Real $ L_" + str(ecomp.name) + "\n"

            if ecomp.dimension == "3D":
                additions += "\n"
                additions += "  ! Additions for 3D Coil\n"

                # massive coils
                if ecomp.getCoilType() == "Massive":
                    if ecomp.isClosed():
                        additions += "  Coil Use W Vector = Logical True\n"
                        additions += "  W Vector Variable Name = String "'CoilCurrent e'"\n"
                        additions += "  Electrode Area = Real $ Ae_" + str(ecomp.name) + "\n"
                    else:
                        additions += "  Coil Use W Vector = Logical True\n"
                        additions += "  W Vector Variable Name = String "'CoilCurrent e'"\n"
                        additions += "  Electrode Area = Real $ Ae_" + str(ecomp.name) + "\n"

                # stranded coils
                if ecomp.getCoilType() == "Stranded":
                    if ecomp.getTerminalType():  # if true = closed
                        additions += "  Coil Use W Vector = Logical True\n"
                        additions += "  W Vector Variable Name = String "'CoilCurrent e'"\n"
                        additions += "  Electrode Area = Real $ Ae_" + str(ecomp.name) + "\n"
                    else:  # else open
                        bnds = ecomp.getOpenTerminals()
                        additions += "  Electrode Boundaries(2) = Integer " + str(bnds[0]) + " " + str(bnds[1]) + "\n"
                        additions += "  Circuit Equation Voltage Factor = Real 0.5 !(use for symmetry, e.g. half of the coil)" + "\n"

                # foil winding
                if ecomp.getCoilType() == "Foil winding":
                    if ecomp.getTerminalType():
                        pass
                    else:
                        bnds = ecomp.getOpenTerminals()
                        additions += "  Electrode Boundaries(2) = Integer " + str(bnds[0]) + " " + str(bnds[1]) + "\n"
                        additions += "  Circuit Equation Voltage Factor = Real 0.5 !(use for symmetry, e.g. half of the coil)\n"

            if ecomp.dimension == "2D":
                additions += "  Symmetry Coefficient = Real $ 1/(Ns_" + str(ecomp.name) + ")\n"
            additions += "End \n"

    # store body forces per circuit to print later
    body_force_list = []
    for component, str_val in zip(source_components, source_str_values):
        name = component.name
        value = component.value

        val_sign = ""
        if "-" in str_val:
            val_sign = "-"

        if isinstance(value, complex):
            body_force_list.append("  " + name + "_Source re = Real $ " + val_sign + "re_" + str_val.strip("-")
                                   + "*cos(phase_" + name + ")")
            body_force_list.append("  " + name + "_Source im = Real $ " + val_sign + "im_" + str_val.strip("-")
                                   + "*sin(phase_" + name + ")")
        else:
            body_force_list.append("  " + name + "_Source = Variable \"time\" \n  \t Real MATC \""
                                   + str_val.strip("-") + "\"")

    return additions, body_force_list


def write_to_file(data: str, output_file, append=True):
    if append:
        file_mode = "a"
    else:
        file_mode = "w"
    with open(output_file, file_mode) as file:
        file.write(data)


def get_parameters(c) -> str:
    parameters_block = ""
    components = c.components[0]
    parameters_block += "! -----------------------------------------------------------------------------\n"
    parameters_block += "! Parameters\n"
    parameters_block += "! -----------------------------------------------------------------------------\n"
    parameters_block += "\n"

    parameters_block += "! General Parameters \n"
    for component in components:
        if not isinstance(component, ElmerComponent):
            if isinstance(component.value, complex):
                parameters_block += f"! {component.name} = re_{component.name}+ j im_{component.name}, phase_{component.name} = {np.degrees(cmath.phase(component.value))}(Deg)\n"
                parameters_block += f"$ re_{component.name} = {abs(np.real(component.value))}\n"  # noqa
                parameters_block += f"$ im_{component.name} = {abs(np.imag(component.value))}\n"  # noqa
                parameters_block += f"$ phase_{component.name} = {cmath.phase(component.value)}\n"
            else:
                parameters_block += f"$ {component.name} = {component.value}\n"
    parameters_block += "\n"

    for component in components:
        if isinstance(component, ElmerComponent):
            parameters_block += f"! Parameters in Component {component.component_number}: {component.name}\n"
            if component.getCoilType() == "Stranded":
                parameters_block += f"$ N_{component.name} = {component.getNumberOfTurns()}\t ! Number of Turns\n"
                parameters_block += f"$ R_{component.name} = {component.getResistance()}\t ! Coil Resistance\n"

            if component.getCoilType() == "Foil winding":
                parameters_block += f"$ N_{component.name} = {component.getNumberOfTurns()}\t ! Number of Turns\n"
                parameters_block += f"$ L_{component.name} = {component.getCoilThickness()}\t ! Coil Thickness\n"

            parameters_block += f"$ Ns_{component.name} = {component.sector}\t ! Sector/Symmetry Coefficient (e.g. 4 is 1/4 of the domain)\n"

            if component.dimension == "3D":
                parameters_block += f"$ Ae_{component.name} = 0.0025\t ! Electrode Area (dummy for now change as required)\n"
    return parameters_block


# def generate_elmer_circuit_file(c, elmerA, elmerB, elmersource, unknown_names, num_nodes, num_edges, ofile)

def check_elmer_instance(components):
    # only run script if there are no elmer components
    is_elmer_instances = [isinstance(components[i], ElmerComponent) for i in range(len(components))]
    # check_component_values = [(component.value is None) for component in components]

    # condition that no elmer components in circuit
    if not any(is_elmer_instances):
        raise ElmerComponentsNotFound("No Elmer Components found in Circuit instances")


def generate_circuit(c, elmerA, elmerB, elmersource, unknown_names, num_nodes, num_edges) -> dict:
    """
    Main writing function. It lays out step by step the Elmer circuit writing process:

    - parameters
    - Kischoff's laws
    - sif additions : Components

    and returns all body forces in circuit definition

    Parameters
    ----------
    c : dict
        A dictionary of Circuit instances

    elmerA : numpy.ndarray of `bytes` strings
        Elmer format damping matrix

    elmerB : numpy.ndarray of `bytes` strings
        Elmer format stiffness matrix

    elmersource : numpy.ndarray of `bytes` strings
        Elmer format source vector

    unknown_names : list of str
        Name of degrees of freedom / Unknowns in n entry vector

    num_nodes : int
        number of unique nodes in circuit network

    num_edges : int
        number of edges/components in circuit network

    Returns
    ----------
    body_forces : dict
        return dictionary of circuit components
    """

    components = c.components[0]
    check_elmer_instance(components)
    sif_matrix = ""

    # if there are elmer components or there's no value component break the loop
    num_variables = len(unknown_names)
    formatted_parameters = get_parameters(c)
    sif_matrix += get_matrix_initialization(c, num_variables)
    sif_matrix += get_unknown_vector(c, unknown_names)
    sif_matrix += get_source_vector(c, elmersource, postfix="")
    sif_matrix += get_kcl_equations(c, num_nodes, num_variables, elmerA, elmerB)
    sif_matrix += get_kvl_equations(c, num_nodes, num_edges, num_variables, elmerA, elmerB, unknown_names)
    sif_matrix += get_component_equations(c, num_nodes, num_edges, num_variables, elmerA, elmerB)
    additions, body_forces = get_sif_additions(c, elmersource)
    # write_to_file(data_to_write, ofile)
    # print("Circuit model will be written in:", ofile)

    return {
        "Parameters": formatted_parameters,
        "Matrix": sif_matrix,
        "Additions": additions,
        "Body Forces": body_forces,
    }


def get_body_forces(body_force_def: list) -> str:
    """
    Writes all sources under Body Force 1 in .sif file.

    Parameters
    ----------
    body_force_def : list of str
        n-entry vector with the names of the sources of all circuits

    ofile : str
        output file name

    Returns
    ----------
    body_forces_block : str

    """

    body_forces = ""

    body_forces += "! -----------------------------------------------------------------------------\n"
    body_forces += "! Sources in SIF \n"
    body_forces += "! -----------------------------------------------------------------------------\n"
    body_forces += "\n"

    body_forces += "Body Force 1\n"

    for ckt_body_force in body_force_def:
        if ckt_body_force is not None:
            for body_force in ckt_body_force:
                body_forces += body_force

    body_forces += "End\n"

    body_forces += "\n"

    body_forces += "! -----------------------------------------------------------------------------\n"
    body_forces += "! End of Circuit\n"
    body_forces += "! -----------------------------------------------------------------------------\n"

    return body_forces


def solve_circuit(circuit):
    """
    Solves the circuit equations using numpy.linalg.solve for a single circuit defined without Elmer Components

    solve_circuit(circuit) is an auxiliary function to ensure and validate stiffness, damping matrices by comparing
    the solution to a circuit simulator's solution (e.g. Qucs)

    It builds the sparse tableau matrices.

    Parameters
    ----------
    circuit : dict
        n-entry vector with the names of the sources of all circuits

    Returns
    ----------
    None
    """

    # loop over all circuits
    # source_components = []  # store sources separately for Body Force 1
    for i in range(1, len(circuit) + 1):

        # loop over all circuits
        c = circuit[i]
        components = c.components[0]
        ref_node = c.ref_node

        # only run script if there are no elmer components
        check_elmer_instance = [isinstance(components[i], ElmerComponent) for i in range(len(components))]
        check_component_values = [(component.value is None) for component in components]

        # condition that no elmer components in circuit
        isElmerComponent = True in check_elmer_instance
        isValueNone = True in check_component_values

        # if there are elmer components or there's no value component break the loop
        if isElmerComponent or isValueNone:
            # print("This model will not be solved externally due to:")
            print("Elmer Circuit Model:", isElmerComponent)
            # print("Component Values not Defined:", isValueNone)

            if isElmerComponent:
                print("Include circuit file in .sif file to be run with ElmerSolver")
            break

        # number of nodes and edges in our network
        num_nodes = get_num_nodes(components)
        num_edges = get_num_edges(components)

        # indices numbered based on component type
        # ind resistor, voltage, current, inductor, capacitor, elmer comp
        indr, indv, indi, indInd, indcap, indcelm = get_indices(components)

        # incidence/connectivity matrix for KCL and KVL
        A = get_incidence_matrix(components, num_nodes, num_edges, ref_node)

        # R matrix including current generators
        R = get_resistance_matrix(components, num_edges, indr, indi, indcap)

        # G matrix including voltage generators
        G = get_conductance_matrix(num_edges, indr, indv, indInd)

        # The following matrices are only needed in time/harmonic cases

        # L matrix including
        L = get_inductance_matrix(components, num_edges, indInd)

        # C matrix including
        C = get_capacitance_matrix(components, num_edges, indcap)

        # RHS = source vector f
        f = get_rhs(components, num_edges, indi, indv)

        # M Matrix and b full source vector RHS (M1x + M2x' = b)
        M1, M2, b = get_tableau_matrix(A, R, G, L, C, f, num_nodes, num_edges)

        # get/create unknown vector name and the v_comp index and source names/index
        unknown_names, vcomp_rows = create_unknown_name(components, ref_node, i)

        # Solve Mx = b if no elmer components
        print("This is NOT an Elmer Circuit model")
        print("Solution: ")
        x = solve_system(M1, M2, b)
        for var, val in zip(unknown_names, x):
            print(var, val)


def generate_elmer_circuits(circuit) -> tuple:
    """
    Creates circuit matrices in Elmer format (main circuitbuilder function).

    This function first creates the stiffness and damping matrices
    based on electrical circuit component definitions.

    Writes the file header, parameters, matrices, .sif components and body force


    Parameters
    ----------
    circuit : dict
        dictionary with circuit definitions

    ofile : str
        output file name

    Returns
    ----------
    header, circuits, body_forces : tuple[str, list[dict], list]
       Returns elmer circuits
    """

    # create list to store all body forces from each circuit def
    all_body_forces = []
    circuits = []

    # write elmer file header
    header = get_file_header(circuit, generate_timestep=True)

    # loop over all circuits
    source_components = []  # store sources separately for Body Force 1
    for i in range(1, len(circuit) + 1):
        # loop over all circuits
        c = circuit[i]
        components = c.components[0]
        ref_node = c.ref_node

        # number of nodes and edges in our network
        num_nodes = get_num_nodes(components)
        num_edges = get_num_edges(components)

        # indices numbered based on component type
        # ind resistor, voltage, current, inductor, capacitor, elmer comp
        indr, indv, indi, indInd, indcap, indcelm = get_indices(components)

        # incidence/connectivity matrix for KCL and KVL
        A_str = get_incidence_matrix_str(components, num_nodes, num_edges, ref_node)

        # R matrix including current generators
        R_str = get_resistance_matrix_str(components, num_edges, indr, indi, indcap)

        # G matrix including voltage generators
        G_str = get_conductance_matrix_str(num_edges, indr, indv, indInd)

        # The following matrices are only needed in time/harmonic cases

        # L matrix including
        L_str = get_inductance_matrix_str(components, num_edges, indInd)

        # C matrix including
        C_str = get_capacitance_matrix_str(components, num_edges, indcap)

        # RHS = source vector f
        f_str = get_rhs_str(components, num_edges, indi, indv)

        # M Matrix and b full source vector RHS (M1x + M2x' = b)
        M1_str, M2_str, b_str = get_tableau_matrix_str(A_str, R_str, G_str, L_str, C_str, f_str, num_nodes, num_edges)

        # get/create unknown vector name and the v_comp index and source names/index
        unknown_names, vcomp_rows = create_unknown_name(components, ref_node, i)

        # get rows filled with zeros
        zero_rows_str = get_zero_rows_str(M1_str, M2_str, b_str)

        # create elmer matrices
        elmerA, elmerB, elmersource = elmer_format_matrix(M1_str, M2_str, b_str, vcomp_rows, zero_rows_str)

        # create elmer circuits file
        formatted_circuit = generate_circuit(c, elmerA, elmerB, elmersource, unknown_names,
                                             num_nodes, num_edges)
        body_forces = formatted_circuit.pop("Body Forces")
        all_body_forces.append(body_forces)
        circuits.append(formatted_circuit)

        # just for debugging. valued matrices and solution solve if no elmer components
        solve_circuit(circuit)

    return header, circuits, all_body_forces


def write_elmer_circuits(circuit, output_file):
    import pprint
    print("Circuit model will be written in:", output_file)
    if os.path.isfile(output_file):
        os.remove(output_file)
    header, circuits, body_forces = generate_elmer_circuits(circuit)
    body_forces_block = get_body_forces(body_forces)
    with open(output_file, "w") as file:
        file.write(header)
        for circuit in circuits:
            pprint.pprint(circuit)
            circuit_block = ""
            for data_block in circuit.values():
                circuit_block += data_block
            file.write(circuit_block)
        file.write(body_forces_block)


def generate_sif_matrices(circuit):
    # create list to store all body forces from each circuit def
    all_body_forces = []
    # loop over all circuits
    source_components = []  # store sources separately for Body Force 1
    for i in range(1, len(circuit) + 1):
        # loop over all circuits
        c = circuit[i]
        components = c.components[0]
        ref_node = c.ref_node

        # number of nodes and edges in our network
        num_nodes = get_num_nodes(components)
        num_edges = get_num_edges(components)

        # indices numbered based on component type
        # ind resistor, voltage, current, inductor, capacitor, elmer comp
        indr, indv, indi, indInd, indcap, indcelm = get_indices(components)

        # incidence/connectivity matrix for KCL and KVL
        A_str = get_incidence_matrix_str(components, num_nodes, num_edges, ref_node)

        # R matrix including current generators
        R_str = get_resistance_matrix_str(components, num_edges, indr, indi, indcap)

        # G matrix including voltage generators
        G_str = get_conductance_matrix_str(num_edges, indr, indv, indInd)

        # The following matrices are only needed in time/harmonic cases

        # L matrix including
        L_str = get_inductance_matrix_str(components, num_edges, indInd)

        # C matrix including
        C_str = get_capacitance_matrix_str(components, num_edges, indcap)

        # RHS = source vector f
        f_str = get_rhs_str(components, num_edges, indi, indv)

        # M Matrix and b full source vector RHS (M1x + M2x' = b)
        M1_str, M2_str, b_str = get_tableau_matrix_str(A_str, R_str, G_str, L_str, C_str, f_str, num_nodes, num_edges)

        # get/create unknown vector name and the v_comp index and source names/index
        unknown_names, vcomp_rows = create_unknown_name(components, ref_node, i)

        # get rows filled with zeros
        zero_rows_str = get_zero_rows_str(M1_str, M2_str, b_str)

        # create elmer matrices
        elmerA, elmerB, elmersource = elmer_format_matrix(M1_str, M2_str, b_str, vcomp_rows, zero_rows_str)  # noqa

        # create elmer circuits file
        body_forces = generate_circuit(c, elmerA, elmerB, elmersource, unknown_names, num_nodes, num_edges)
        all_body_forces.append(body_forces)

        # just for debugging. valued matrices and solution solve if no elmer components
        solve_circuit(circuit)

    return all_body_forces


class CircuitBuilderExceptions(Exception):
    pass


class ElmerComponentsNotFound(CircuitBuilderExceptions):
    pass


# for installation testing (temporary)
def say_hello(name=None):
    if name is None:
        return "Hello, World!"
    else:
        return f"Hello, {name}!"
