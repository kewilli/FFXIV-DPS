import gym
import numpy as np
from gym import spaces

class BlmDamage(gym.Env):
	"""This class creates a pseudo environment for expressing BLM damage in FFXIV."""
	
	class Ability:
		def __init__(self, name, damage, stateChanger):
			self.damage = damage
			self.stateChanger = stateChanger

		def apply(self, state):
			return self.damage, self.stateChanger(state)

	class Buff:
		def __init__(self, effect):
			self.effect = effect

		def apply(self, state):
			self.effect(state)

	def __init__(self, maxUmbralAstral):
		self.ABILITIES = [
            self.Ability("Blizzard", 2, self.UmbralIceIncrease),
            self.Ability("Fire", 100, self.AstralFireIncrease)]
		self.BUFFS = []
		self.MAXTIME = 10
		self.initialState = np.array([0] * (len(self.ABILITIES) + len(self.BUFFS)) + [0])
		self.iteration = 0
		self.maxUmbralAstral = maxUmbralAstral

		# What the learner can pick between
		self.action_space = spaces.Discrete(len(self.ABILITIES))

		# What the learner can see to make a choice (cooldowns and buffs)
		self.observation_space = spaces.MultiDiscrete([[0,1]] * (len(self.ABILITIES) + len(self.BUFFS)) + [[-3,3]])

	def _reset(self):
		self.state = self.initialState
		self.iteration = 0
		return self.state

	def _step(self, action):
		assert self.action_space.contains(action), "Invalid action!"

		# Apply ability and get reward
		damage, state = self.ABILITIES[action].apply(self.state)

		# Update observation (CDs and buffs)
		state = self.state

		return state, damage, self._isDone(), {}

	def _isDone(self):
		self.iteration += 1
		return self.iteration >= self.MAXTIME

	def AstralFireIncrease(self, state):
		return state

	def UmbralIceIncrease(self, state):
		return state