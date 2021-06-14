from time import time
import random
import array
import numpy as np
from deap import creator, base, tools, algorithms
from dataclasses import dataclass

class GAOptimizer(object):
    """A genetic algorithm optimizer using the DEAP library: https://github.com/deap/deap
    """

    @dataclass
    class AlgorithmParameters:
        cost_function: any
        lower_bounds: list
        upper_bounds: list
        generations: int = 100
        num_individuals: int = 100
        crossover_prob: float = 0.9
        mutation_prob: float = 0.05

    def __init__(self, params: AlgorithmParameters):
        """Initialize the genetic algorithm that will solve the control synthesis problem.
        The params dictionary has the following items
        num_control_params      The number of control parameters used in a solution.
        generations             The number of iterations of the genetic algorithm to run.

        """
        assert len(params.lower_bounds) == len(params.upper_bounds)
    
        self.ind_size = len(params.lower_bounds)
        ngen = params.generations
        nind = params.num_individuals
        cxpb, mutpb, mu, lam = params.crossover_prob, params.mutation_prob, nind, nind

        # Here we are creating two new types. The FitnessMin type and the Individual type.
        # FitnessMin inherits from deap.base.Fitness and has a new weights attribute that is
        # a tuple. For single objective optimization, the weights attribute has one element
        # for multi-objective optimization it will have multiple elements. A negative weight
        # indicates this is a minimization problem.
        if hasattr(creator, 'FitnessMin') is False:
            creator.create('FitnessMin', base.Fitness, weights=(-1.0,))

        # The individual type inherits from array.array (could use list) and it needs a 
        # fitness attribute to know how to calculate the fitness of the individual.
        # Arrays store only one type of data. This is set by the tyepcode paramter. 'd' is for double.
        if hasattr(creator, 'Individual') is False:
            kw0 = {'typecode': 'd', 'fitness': creator.FitnessMin}
            creator.create('Individual', array.array, **kw0)

        # Creates the initial lists of individuals.
        atr = lambda: [random.uniform(lb, ub) for lb, ub in zip(params.lower_bounds, params.upper_bounds)]
        ind = lambda: creator.Individual(atr())
        population = [ind() for _ in range(nind)]

        # The toolbox is a container to store partial functions. In particular we want the evaluate, mate, mutate, 
        # and select genetic algorithm functions defined here.
        toolbox = base.Toolbox()

        kw1 = {'low': params.lower_bounds, 'up': params.upper_bounds, 'eta': 20.0, 'indpb': 1.0 / self.ind_size}
        mut = lambda xs: tools.mutPolynomialBounded(xs, **kw1)
        kw2 = {'low': params.lower_bounds, 'up': params.upper_bounds, 'eta': 20.0}
        crs = lambda i1, i2: tools.cxSimulatedBinaryBounded(i1, i2, **kw2)
        sel = lambda p, n: tools.selTournament(p, n, tournsize=3)

        toolbox.register('evaluate', params.cost_function)
        toolbox.register('mate', crs)
        toolbox.register('mutate', mut)
        toolbox.register('select', sel)

        # DEAP provides objects taht will record algorithm statisitics and keep trak of the best solutions.
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register('min', np.min)
        self.hof = tools.HallOfFame(5)

        # Setting up the DEAP library for the genetic algorithm comes down to creating and
        # executing an algorithm function. There are a number of pre-build algorithms that
        # can be used rather than coding your own. The eaMuPlusLambda algorithm requires
        # the parameters that have been generated above.
        args = (population, toolbox, mu, lam, cxpb, mutpb, ngen)
        kw3 = {'stats': stats, 'halloffame': self.hof, 'verbose': True}
        self.algorithm = lambda: algorithms.eaMuPlusLambda(*args, **kw3)

    def execute(self):
        self.to_console_init()
        tic = time()
        self.pop, self.log = self.algorithm()
        toc = time()
        self.exe_time = toc - tic
        self.to_console_final(self.hof[0])

    def to_console_init(self):
        print()
        print(f'Number of Parameters: {self.ind_size}')

    def to_console_final(self, xopt):
        print()
        print('--- Solution Characteristics ---')
        if self.exe_time != 0:
            print('Time (s): %g' % (self.exe_time))
        print(f'The optimal solution is: {xopt}')
