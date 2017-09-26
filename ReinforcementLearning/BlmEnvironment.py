from tensorforce.environments import Environment

class BlmEnvironment(Environment):

    def __init__(self):
        # Constants
        self.__Umbral3 = 3
        self.__Umbral2 = 2
        self.__Umbral1 = 1
        self.__None = 0
        self.__Astral3 = 6
        self.__Astral2 = 5
        self.__Astral1 = 4

        # Abilities
        self.abilities = [50, 100]

        # Stateful
        self.damageDone = 0

    def __str__(self):
        return "This is __str__ for BlmEnvironment"

    def close(self):
        return

    def reset(self):
        self.damageDone = 0

    def execute(self, action):
        reward = self.abilities[action]
        return tuple(tuple(1.0, self.__None), reward, False)

    @property
    def states(self):
        # tuple(box(1), discrete(7), discrete(2) * #ofSpells, discrete(2) * #ofBuffs
        # mp, astral+umbral, CDs, status
        stateDict = dict()

        # mp = box(1)
        stateDict['state{}'.format(0)] = dict(shape=(1), type='float')

        # astral+umbral = discrete(7)
        stateDict['state{}'.format(1)] = dict(shape=(), type='int')

        return stateDict

    @property
    def actions(self):
		# discrete(len(self.abilities)
        return dict(continuous=False, num_actions=len(self.abilities))