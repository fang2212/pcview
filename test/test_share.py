import multiprocessing
from multiprocessing import sharedctypes
import time

size = 100000
def func(a):
    t = time.time()
    for i in range(size):
        a[i]
    print("elapsed {}".format(time.time()-t))

a = multiprocessing.Array('i', [i for i in range(size)])
print('test multiprocessing.Array')
func(a)

a = sharedctypes.Array('i', [i for i in range(size)])
print('test sharedctypes.Array')
func(a)

a = multiprocessing.Manager().list([i for i in range(size)])
print('test Manager.list')
func(a)

