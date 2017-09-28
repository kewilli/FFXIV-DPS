import unittest
from BlmDamage import BlmDamage

class SanityTests(unittest.TestCase):
	def doubleFire(self):
		blm = BlmDamage(1)
		state, potency, done, d = blm._step([0])
		self.assertEqual(potency, 100)

		state, potency, done, d = blm._step([0])
		self.assertEqual(potency, 140)

if __name__ == '__main__':
	unittest.main()