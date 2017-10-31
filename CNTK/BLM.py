from enum import *
import gym
import math
import numpy as np
from gym import spaces

class BLM(gym.Env):
	"""This class creates a pseudo environment for expressing BLM potency in FFXIV."""

	MAXMANA = 316 #15480
	MANATICKTIMING = 3
	MAXUMBRALASTRAL = 0

	class AstralUmbral(IntEnum):
		Neutral = 0
		ASTRAL_FIRE_1 = 1
		ASTRAL_FIRE_2 = 2
		ASTRAL_FIRE_3 = 3
		UMBRAL_ICE_1 = -1
		UMBRAL_ICE_2 = -2
		UMBRAL_ICE_3 = -3

		def isAstral(i):
			return i == BLM.AstralUmbral.ASTRAL_FIRE_1.value or i == BLM.AstralUmbral.ASTRAL_FIRE_2 or i == BLM.AstralUmbral.ASTRAL_FIRE_3

		def isUmbral(i):
			return i == BLM.AstralUmbral.UMBRAL_ICE_1 or i == BLM.AstralUmbral.UMBRAL_ICE_2 or i == BLM.AstralUmbral.UMBRAL_ICE_3

	
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
			if (astralUmbral == BLM.AstralUmbral.Neutral):
				state = self.UpdateMana(state, BLM.MAXMANA * -0.02)
			elif (astralUmbral == BLM.AstralUmbral.UMBRAL_ICE_1):
				state = self.UpdateMana(state, BLM.MAXMANA * -0.32)
			elif (astralUmbral == BLM.AstralUmbral.UMBRAL_ICE_2):
				state = self.UpdateMana(state, BLM.MAXMANA * -0.47)
			elif (astralUmbral == BLM.AstralUmbral.UMBRAL_ICE_3):
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
			if (astralUmbral == BLM.AstralUmbral.Neutral or BLM.AstralUmbral.isAstral(astralUmbral)):
				state[-1] = min(BLM.MAXUMBRALASTRAL, astralUmbral + 1)
			else:
				state[-1] = 0
			return state

		def AstralFireMax(self, state):
			state[-1] = BLM.MAXUMBRALASTRAL
			return state

		def UmbralIceIncrease(self, state):
			astralUmbral = self.GetAstralUmbral(state)
			if (astralUmbral == BLM.AstralUmbral.Neutral or BLM.AstralUmbral.isUmbral(astralUmbral)):
				state[-1] = max(-BLM.MAXUMBRALASTRAL, astralUmbral - 1)
			else:
				state[-1] = 0
			return state

		def UmbralIceMax(self, state):
			state[-1] = -BLM.MAXUMBRALASTRAL
			return state

		def SwapAstralUmbral(self, state):
			astralUmbral = self.GetAstralUmbral(state) 
			if BLM.AstralUmbral.isUmbral(astralUmbral):
				state[-1] = 1
			elif BLM.AstralUmbral.isAstral(astralUmbral):
				state[-1] = -1
			return state

	class Ability:
		def __init__(self, name, potency, mana, castTime, refreshTime, stateChanger, elementEnum, helper):
			self.HELPER = helper
			self.name = name
			self.potency = potency
			self.mana = mana
			self.castTime = castTime
			self.refreshTime = refreshTime
			self.stateChanger = stateChanger
			self.elementEnum = elementEnum

		def apply(self, state):
			scaledPotency = self.potency
			adjustedMana = self.getManaCost(state)
			adjustedCastTime = self.castTime

			state = self.HELPER.UpdateMana(state, adjustedMana)

			# Scale potency and mana consumption according to Astral/Umbral 
			if (self.elementEnum == BLM.DamageType.Fire):
				scaledPotency = self.firePotency(state)
				adjustedCastTime = self.fireCastTime(state)
			elif (self.elementEnum == BLM.DamageType.Ice):
				scaledPotency = self.icePotency(state)
				adjustedCastTime = self.iceCastTime(state)

			return scaledPotency, self.stateChanger(state) if self.stateChanger is not None else state, adjustedCastTime

		def getManaCost(self, state):
			if self.elementEnum == BLM.DamageType.Fire:
				return self.fireMana(state)
			elif self.elementEnum == BLM.DamageType.Ice:
				return self.iceMana(state)
			else:
				return self.mana

		def firePotency(self, state):
			astralUmbral = self.HELPER.GetAstralUmbral(state)
			if (astralUmbral == BLM.AstralUmbral.Neutral):
				return self.potency
			elif (astralUmbral == BLM.AstralUmbral.ASTRAL_FIRE_1):
				return self.potency * 1.4
			elif (astralUmbral == BLM.AstralUmbral.ASTRAL_FIRE_2):
				return self.potency * 1.6
			elif (astralUmbral == BLM.AstralUmbral.ASTRAL_FIRE_3):
				return self.potency * 1.8
			elif (astralUmbral == BLM.AstralUmbral.UMBRAL_ICE_1):
				return self.potency * 0.9
			elif (astralUmbral == BLM.AstralUmbral.UMBRAL_ICE_2):
				return self.potency * 0.8
			else:
				return self.potency * 0.7

		def icePotency(self, state):
			astralUmbral = self.HELPER.GetAstralUmbral(state)
			if (astralUmbral == BLM.AstralUmbral.Neutral or BLM.AstralUmbral.isUmbral(astralUmbral)):
				return self.potency
			elif (astralUmbral == BLM.AstralUmbral.ASTRAL_FIRE_1):
				return self.potency * 0.9
			elif (astralUmbral == BLM.AstralUmbral.ASTRAL_FIRE_2):
				return self.potency * 0.8
			elif (astralUmbral == BLM.AstralUmbral.ASTRAL_FIRE_3):
				return self.potency * 0.7

		def fireMana(self, state):
			astralUmbral = self.HELPER.GetAstralUmbral(state)
			if BLM.AstralUmbral.isAstral(astralUmbral):
				return self.mana * 2
			elif (astralUmbral == BLM.AstralUmbral.Neutral):
				return self.mana
			elif (astralUmbral == BLM.AstralUmbral.UMBRAL_ICE_1):
				return self.mana / 2.0
			elif (astralUmbral == BLM.AstralUmbral.UMBRAL_ICE_2 or astralUmbral == BLM.AstralUmbral.UMBRAL_ICE_3):
				return self.mana / 4.0

		def iceMana(self, state):
			astralUmbral = self.HELPER.GetAstralUmbral(state)
			if (astralUmbral == BLM.AstralUmbral.Neutral or BLM.AstralUmbral.isUmbral(astralUmbral)):
				return self.mana
			elif (astralUmbral == BLM.AstralUmbral.ASTRAL_FIRE_1):
				return self.mana / 2.0
			elif (astralUmbral == BLM.AstralUmbral.ASTRAL_FIRE_2 or astralUmbral == BLM.AstralUmbral.ASTRAL_FIRE_3):
				return self.mana / 4.0

		def fireCastTime(self, state):
			astralUmbral = self.HELPER.GetAstralUmbral(state)
			if astralUmbral == BLM.AstralUmbral.ASTRAL_FIRE_3:
				return self.castTime / 2
			else:
				return self.castTime

		def iceCastTime(self, state):
			astralUmbral = self.HELPER.GetAstralUmbral(state)
			if astralUmbral == BLM.AstralUmbral.UMBRAL_ICE_3:
				return self.castTime / 2
			else:
				return self.castTime

	def __init__(self, maxUmbralAstral):
		# Print debug
		self.debug = False

		# Outer bound for Astral Fire and Umbral Ice
		BLM.MAXUMBRALASTRAL = maxUmbralAstral

		# Available buffs
		self.BUFFS = []

		# Maximum time available
		self.MAXTIME = 45

		self.HELPER = BLM.Helper()

		# Available abilities
		self.ABILITIES = [
			BLM.Ability("Blizzard 1", 180, 6,  2.5,  2.49, self.HELPER.UmbralIceIncrease, BLM.DamageType.Ice, self.HELPER), #480
			BLM.Ability("Fire 1",     180, 15, 2.5,  2.49, self.HELPER.AstralFireIncrease, BLM.DamageType.Fire, self.HELPER), #1200
			BLM.Ability("Transpose",  0,   0,  0.75, 12.9, self.HELPER.SwapAstralUmbral, BLM.DamageType.Neither, self.HELPER),
			BLM.Ability("Fire 3",     240, 30, 3.5,  2.5, self.HELPER.AstralFireMax, BLM.DamageType.Fire, self.HELPER), #2400
			BLM.Ability("Blizzard 3", 240, 18, 3.5,  2.5, self.HELPER.UmbralIceMax, BLM.DamageType.Ice, self.HELPER), #2400
			BLM.Ability("Fire 4",     260, 15, 2.8,  2.5, None, BLM.DamageType.Fire, self.HELPER)] #2400
		
		# State including ability cooldowns, buff time remaining, mana, and Astral/Umbral
		self.initialState = np.array([0] * (len(self.ABILITIES) + len(self.BUFFS)) + [BLM.MAXMANA] + [0])

		self.state = self._reset()

		# What the learner can pick between
		self.action_space = spaces.Discrete(len(self.ABILITIES))

		# What the learner can see to make a choice (cooldowns and buffs)
		self.observation_space = spaces.MultiDiscrete([[0,180]] * (len(self.ABILITIES) + len(self.BUFFS)) + [[0, BLM.MAXMANA]] + [[-3,3]])

	def _reset(self):
		""" Reset the environment for a fresh run """
		self.timer = 0
		self.nextManaTick = BLM.MANATICKTIMING - 0.1
		self.state = self.initialState.copy()

		if self.debug:
			print("RESET: %d, %d" % (self.HELPER.GetMana(self.state), self.HELPER.GetAstralUmbral(self.state)))
		return self.state

	def _step(self, action):
		assert self.action_space.contains(action), "Invalid action!"

		ability = self.ABILITIES[action]

		# Can I cast it?
		if self.state[action] > 0 or self.HELPER.GetMana(self.state) < ability.getManaCost(self.state):
			# Still on cooldown!
			self.timer += 0.75
			
			# Mana regen during wait?
			astralUmbral = self.HELPER.GetAstralUmbral(self.state)
			if self.timer > self.nextManaTick and (astralUmbral == BLM.AstralUmbral.Neutral or BLM.AstralUmbral.isUmbral(astralUmbral)):
				while self.timer > self.nextManaTick:
					self.state = self.HELPER.RegenTick(self.state)
					self.nextManaTick += BLM.MANATICKTIMING
			
			if self.debug:
				print("On cooldown: %s" % ability.name)
			return self.state, self.scaleResult(-100), self._isDone(), {"Name": ability.name}
		elif ability.name == "Fire 4" and self.HELPER.GetAstralUmbral(self.state) <= BLM.AstralUmbral.Neutral:
			self.timer += 0.75
			return self.state, self.scaleResult(0), self._isDone(), {"Name": ability.name}

		# Increase the time
		self.timer += ability.castTime

		# Mana regen
		astralUmbral = self.HELPER.GetAstralUmbral(self.state)
		if self.timer > self.nextManaTick and (astralUmbral == BLM.AstralUmbral.Neutral or BLM.AstralUmbral.isUmbral(astralUmbral)):
			while self.timer > self.nextManaTick:
				self.state = self.HELPER.RegenTick(self.state)
				self.nextManaTick += BLM.MANATICKTIMING

		# Apply ability and get reward
		potency, self.state, adjustedCastTime = ability.apply(self.state)
		if self.debug:
			print("%s: %d -> %d, %d" % (ability.name, potency, self.HELPER.GetMana(self.state), self.HELPER.GetAstralUmbral(self.state)))

		# Update cooldowns
		for i in range(len(self.ABILITIES)):
			if i == action:
				# Update cooldown for what was just cast
				self.state[action] = max(0, ability.refreshTime - ability.castTime)
			elif self.state[i] > 0:
				# Update spell which is on cooldown
				self.state[i] = max(0, self.state[i] - ability.castTime)

		# Update observation (CDs and buffs)
		# state = self.state

		done = self._isDone()

		return self.state, self.scaleResult(potency), done, {"Name": ability.name}

	def _isDone(self):
		mana = self.HELPER.GetMana(self.state)
		if mana < 0 or self.timer >= self.MAXTIME:
			if self.debug:
				print("DONE: Mana = %d, Timer = %d" % (mana, self.timer))
			return True
		return False

	def scaleResult(self, potency):
		return potency #math.pow(potency / 500, 3)


	class Buff:
		def __init__(self, effect):
			self.effect = effect

		def apply(self, state):
			self.effect(state)