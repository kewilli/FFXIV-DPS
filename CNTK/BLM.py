from enum import Enum
import gym
import numpy as np
from gym import spaces

class BLM(gym.Env):
	"""This class creates a pseudo environment for expressing BLM potency in FFXIV."""

	MAXMANA = 15480
	MAXUMBRALASTRAL = 0
	
	class DamageType(Enum):
		Neither = 0
		Ice = 1
		Fire = 2

	class Ability:
		def __init__(self, name, potency, mana, stateChanger, elementEnum):
			self.name = name
			self.potency = potency
			self.mana = mana
			self.stateChanger = stateChanger
			self.elementEnum = elementEnum

		def apply(self, state):
			scaledPotency = self.potency
			if (self.elementEnum == BLM.DamageType.Fire):
				scaledPotency = self.firePotency(state)
				state = BLM.Helper.UpdateMana(state, self.fireMana(state))
			elif (self.elementEnum == BLM.DamageType.Ice):
				scaledPotency = self.icePotency(state)
				state = BLM.Helper.UpdateMana(state, self.iceMana(state))
			else:
				state = BLM.Helper.UpdateMana(state, -self.mana)

			return scaledPotency, self.stateChanger(state)

		def firePotency(self, state):
			astralUmbral = BLM.Helper.GetAstralUmbral(state)
			if (astralUmbral == 0):
				return self.potency
			elif (astralUmbral == 1):
				return self.potency * 1.4
			elif (astralUmbral == 2):
				return self.potency * 1.6
			elif (astralUmbral == 3):
				return self.potency * 1.8
			elif (astralUmbral == -1):
				return self.potency * 0.9
			elif (astralUmbral == -2):
				return self.potency * 0.8
			else:
				return self.potency * 0.7

		def icePotency(self, state):
			astralUmbral = BLM.Helper.GetAstralUmbral(state)
			if (astralUmbral <= 0):
				return self.potency
			elif (astralUmbral == 1):
				return self.potency * 0.9
			elif (astralUmbral == 2):
				return self.potency * 0.8
			elif (astralUmbral == 3):
				return self.potency * 0.7

		def fireMana(self, state):
			astralUmbral = BLM.Helper.GetAstralUmbral(state)
			if (astralUmbral > 0):
				return self.mana * 2
			elif (astralUmbral == 0):
				return self.mana
			elif (astralUmbral == -1):
				return self.mana / 2.0
			elif (astralUmbral <= -2):
				return self.mana / 4.0

		def iceMana(self, state):
			astralUmbral = BLM.Helper.GetAstralUmbral(state)
			if (astralUmbral <= 0):
				return self.mana
			elif (astralUmbral == 1):
				return self.mana / 2.0
			elif (astralUmbral >= 2):
				return self.mana / 4.0

	class Helper:
		def GetMana(state):
			return state[-2]

		def SetMana(state, newMana):
			state[-2] = newMana

		def UpdateMana(state, change):
			mana = BLM.Helper.GetMana(state)
			BLM.Helper.SetMana(state, min(mana - change, BLM.MAXMANA))
			return state

		def GetAstralUmbral(state):
			return state[-1] # Astral/Umbral is the last state

		def AstralFireIncrease(state):
			astralUmbral = BLM.Helper.GetAstralUmbral(state)
			if (astralUmbral >= 0):
				state[-1] = min(BLM.MAXUMBRALASTRAL, astralUmbral + 1)
			else:
				state[-1] = 0
			return state

		def UmbralIceIncrease(state):
			astralUmbral = BLM.Helper.GetAstralUmbral(state)
			if (astralUmbral <= 0):
				state[-1] = max(-BLM.MAXUMBRALASTRAL, astralUmbral - 1)
			else:
				state[-1] = 0
			return state

		def SwapAstralUmbral(state):
			astralUmbral = BLM.Helper.GetAstralUmbral(state) 
			if (astralUmbral < 0):
				state[-1] = 1
			elif (astralUmbral > 0):
				state[-1] = -1
			return state

	ABILITIES = [
            Ability("Blizzard", 180, 480, Helper.UmbralIceIncrease, DamageType.Ice),
            Ability("Fire", 180, 1200, Helper.AstralFireIncrease, DamageType.Fire),
			Ability("Transpose", 0, 0, Helper.SwapAstralUmbral, DamageType.Neither)]

	def __init__(self, maxUmbralAstral):
		self.BUFFS = []
		self.MAXTIME = 30
		self.initialState = np.array([0] * (len(BLM.ABILITIES) + len(self.BUFFS)) + [BLM.MAXMANA] + [0])
		self.iteration = 0
		self.state = self.initialState.copy()
		BLM.MAXUMBRALASTRAL = maxUmbralAstral

		# What the learner can pick between
		self.action_space = spaces.Discrete(len(BLM.ABILITIES))

		# What the learner can see to make a choice (cooldowns and buffs)
		self.observation_space = spaces.MultiDiscrete([[0,1]] * (len(BLM.ABILITIES) + len(self.BUFFS)) + [[0, BLM.MAXMANA]] + [[-3,3]])

	def _reset(self):
		self.iteration = 0
		self.state = self.initialState.copy()
		print("RESET: %d, %d" % (BLM.Helper.GetMana(self.state), BLM.Helper.GetAstralUmbral(self.state)))
		return self.state

	def _step(self, action):
		assert self.action_space.contains(action), "Invalid action!"

		ability = BLM.ABILITIES[action]

		# Apply ability and get reward
		potency, self.state = ability.apply(self.state)
		print("%s -> %d, %d" % (ability.name, BLM.Helper.GetMana(self.state), BLM.Helper.GetAstralUmbral(self.state)))

		# Update observation (CDs and buffs)
		# state = self.state

		done = self._isDone()

		return self.state, potency, done, {"Name": ability.name}

	def _isDone(self):
		self.iteration += 1
		mana = BLM.Helper.GetMana(self.state)
		if mana < 0 or self.iteration >= self.MAXTIME:
			print("DONE: Mana = %d, Iteration = %d" % (mana, self.iteration))
			return True
		return False


	class Buff:
		def __init__(self, effect):
			self.effect = effect

		def apply(self, state):
			self.effect(state)