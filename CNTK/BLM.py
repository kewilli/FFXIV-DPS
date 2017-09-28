from enum import Enum
import gym
import numpy as np
from gym import spaces

class BLM(gym.Env):
	"""This class creates a pseudo environment for expressing BLM potency in FFXIV."""

	MAXMANA = 15480
	MANATICKTIMING = 3
	MAXUMBRALASTRAL = 0
	
	class DamageType(Enum):
		Neither = 0
		Ice = 1
		Fire = 2

	class Helper:

		def GetMana(self, state):
			return state[-2]

		def SetMana(self, state, newMana):
			state[-2] = newMana

		def RegenTick(self, state):
			astralUmbral = self.GetAstralUmbral(state)
			if (astralUmbral == 0):
				state = self.UpdateMana(state, BLM.MAXMANA * -0.02)
			elif (astralUmbral == -1):
				state = self.UpdateMana(state, BLM.MAXMANA * -0.32)
			elif (astralUmbral == -2):
				state = self.UpdateMana(state, BLM.MAXMANA * -0.47)
			elif (astralUmbral == -3):
				state = self.UpdateMana(state, BLM.MAXMANA * -0.62)
			return state

		def UpdateMana(self, state, change):
			mana = self.GetMana(state)
			self.SetMana(state, min(mana - change, BLM.MAXMANA))
			return state

		def GetAstralUmbral(self, state):
			return state[-1] # Astral/Umbral is the last state

		def AstralFireIncrease(self, state):
			astralUmbral = self.GetAstralUmbral(state)
			if (astralUmbral >= 0):
				state[-1] = min(BLM.MAXUMBRALASTRAL, astralUmbral + 1)
			else:
				state[-1] = 0
			return state

		def UmbralIceIncrease(self, state):
			astralUmbral = self.GetAstralUmbral(state)
			if (astralUmbral <= 0):
				state[-1] = max(-BLM.MAXUMBRALASTRAL, astralUmbral - 1)
			else:
				state[-1] = 0
			return state

		def SwapAstralUmbral(self, state):
			astralUmbral = self.GetAstralUmbral(state) 
			if (astralUmbral < 0):
				state[-1] = 1
			elif (astralUmbral > 0):
				state[-1] = -1
			return state

	class Ability:
		def __init__(self, name, potency, mana, castTime, stateChanger, elementEnum, helper):
			self.HELPER = helper
			self.name = name
			self.potency = potency
			self.mana = mana
			self.castTime = castTime
			self.stateChanger = stateChanger
			self.elementEnum = elementEnum

		def apply(self, state):
			scaledPotency = self.potency
			if (self.elementEnum == BLM.DamageType.Fire):
				scaledPotency = self.firePotency(state)
				state = self.HELPER.UpdateMana(state, self.fireMana(state))
			elif (self.elementEnum == BLM.DamageType.Ice):
				scaledPotency = self.icePotency(state)
				state = self.HELPER.UpdateMana(state, self.iceMana(state))
			else:
				state = self.HELPER.UpdateMana(state, -self.mana)

			return scaledPotency, self.stateChanger(state)

		def firePotency(self, state):
			astralUmbral = self.HELPER.GetAstralUmbral(state)
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
			astralUmbral = self.HELPER.GetAstralUmbral(state)
			if (astralUmbral <= 0):
				return self.potency
			elif (astralUmbral == 1):
				return self.potency * 0.9
			elif (astralUmbral == 2):
				return self.potency * 0.8
			elif (astralUmbral == 3):
				return self.potency * 0.7

		def fireMana(self, state):
			astralUmbral = self.HELPER.GetAstralUmbral(state)
			if (astralUmbral > 0):
				return self.mana * 2
			elif (astralUmbral == 0):
				return self.mana
			elif (astralUmbral == -1):
				return self.mana / 2.0
			elif (astralUmbral <= -2):
				return self.mana / 4.0

		def iceMana(self, state):
			astralUmbral = self.HELPER.GetAstralUmbral(state)
			if (astralUmbral <= 0):
				return self.mana
			elif (astralUmbral == 1):
				return self.mana / 2.0
			elif (astralUmbral >= 2):
				return self.mana / 4.0


	def __init__(self, maxUmbralAstral):
		# "Globals"
		BLM.MAXUMBRALASTRAL = maxUmbralAstral
		self.BUFFS = []
		self.MAXTIME = 100
		self.HELPER = BLM.Helper()		
		self.ABILITIES = [
			BLM.Ability("Blizzard", 180, BLM.MAXMANA / 12, 2.5, self.HELPER.UmbralIceIncrease, BLM.DamageType.Ice, self.HELPER),
			BLM.Ability("Fire", 180, BLM.MAXMANA / 12, 2.5, self.HELPER.AstralFireIncrease, BLM.DamageType.Fire, self.HELPER), #TODO: Was 1200
			BLM.Ability("Transpose", 0, 0, 0.75, self.HELPER.SwapAstralUmbral, BLM.DamageType.Neither, self.HELPER)]
		
		self.initialState = np.array([0] * (len(self.ABILITIES) + len(self.BUFFS)) + [BLM.MAXMANA] + [0])

		self.state = self._reset()

		# What the learner can pick between
		self.action_space = spaces.Discrete(len(self.ABILITIES))

		# What the learner can see to make a choice (cooldowns and buffs)
		self.observation_space = spaces.MultiDiscrete([[0,1]] * (len(self.ABILITIES) + len(self.BUFFS)) + [[0, BLM.MAXMANA]] + [[-3,3]])

	def _reset(self):
		self.timer = 0
		self.nextManaTick = BLM.MANATICKTIMING - 0.1
		self.state = self.initialState.copy()
		print("RESET: %d, %d" % (self.HELPER.GetMana(self.state), self.HELPER.GetAstralUmbral(self.state)))
		return self.state

	def _step(self, action):
		assert self.action_space.contains(action), "Invalid action!"

		ability = self.ABILITIES[action]

		# Increase the time
		self.timer += ability.castTime

		# Mana regen
		if self.timer > self.nextManaTick and self.HELPER.GetAstralUmbral(self.state) <= 0:
			while self.timer > self.nextManaTick:
				self.state = self.HELPER.RegenTick(self.state)
				self.nextManaTick += BLM.MANATICKTIMING

		# Apply ability and get reward
		potency, self.state = ability.apply(self.state)
		print("%s -> %d, %d" % (ability.name, self.HELPER.GetMana(self.state), self.HELPER.GetAstralUmbral(self.state)))

		# Update observation (CDs and buffs)
		# state = self.state

		done = self._isDone()

		return self.state, potency if not done else 0, done, {"Name": ability.name}

	def _isDone(self):
		mana = self.HELPER.GetMana(self.state)
		if mana < 0 or self.timer >= self.MAXTIME:
			print("DONE: Mana = %d, Timer = %d" % (mana, self.timer))
			return True
		return False


	class Buff:
		def __init__(self, effect):
			self.effect = effect

		def apply(self, state):
			self.effect(state)