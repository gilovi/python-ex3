__author__ = 'PythonTeam 2015'
from decimal import *
from math import sqrt
from random import randint

"""
This file contains deceleration of methods that should assist solving to
Google BillBoard Riddle.

Written for Python Programming Workshop (67557) at HUJI, 2015
"""

def eularsNumber(n, p):
    """
    Returns eular's number using evaluation of (1 + 1 / n)^n, where n is the
    given param, and p is the precision - that is p is the number of digits of
    e to return.
    The number should be returned as a string which contains only digits.
    """
    getcontext().prec = p
    return str((1+1/Decimal(n))**n).replace('.','')


def prime_1(n):
    """
        Returns True iff n is prime.
        This should be a simple algorithm to find if a number is prime.
        from wikipedia.
    """
    if n <= 3:
        return n > 1
    if  n%2 == 0 or  n%3 == 0:
        return False
    for i in range(5, int(sqrt(n))+1, 6):
        if  n % i == 0 or n % (i + 2) == 0:
            return False
    return True



def prime_2(s, e):
    """
    Returns a list(!) of all primes between 's'(including) and 'e'(excluding)
    This method should be written using at most 2(!) lines of code
    """
    return filter(prime_1,range(s,e))


def prime_3(n, k):
    """
    Returns True iff n is a prime with probability of less than 4^(-k) for a mistake.
    This method should implement the probabilistic algorithm for primality testing
    as suggested by G. Miller and later modified by M. Rabin.
    """
    (d,s) = factor (n-1)
    for i in xrange(k):
        a = randint(2,n-2)
        x = mod_pow(a,d,n)

        if not ( x == 1 or x == n - 1):
            for j in xrange(s-1):
                x = mod_pow(x,2,n)
                if x == 1 :
                    return False
                if x == n-1:
                    break
            else:
                return False
    return True

def factor(n):
    i = 0
    while (n)%2 == 0:
        n /= 2
        i += 1
    return [n,i]


def mod_pow(a, d, n):

    result = 1
    a = a % n
    while d > 0:
        if d % 2 == 1:
           result = (result * a) % n
        d >>= 1
        a = (a * a) % n
    return result
	# getcontext().prec = 1001
	# e = eularsNumber(10**Decimal(1000),1001)
	# ans = [p for p in map(long,[e[i:i+10] for i in range (990)]) if prime_3(p,2)][0]