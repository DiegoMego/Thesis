import unittest
from temp.original import main
class TestUM(unittest.TestCase):
	def setUp(self):
		pass
	def test_numbers1_1_7(self):
		self.assertEqual(main(2,1,1), 4)
if __name__ == '__main__':
	unittest.main()
