
import unittest

# Here's our "unit".
def myFunc():
    print "This is a test."

def IsOdd(n):
	return n % 2 == 1

class ScraperTest(unittest.TestCase):

    def testOne(self):
        self.failUnless(IsOdd(2))

def main():
    unittest.main()

if __name__ == '__main__':
    main()
