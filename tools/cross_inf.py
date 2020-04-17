

class Operator(object):
    def __init__(self, obj):
        self.obj = obj

    def op(self):
        self.obj.par['val'] = 9


class Operator1(object):
    def __init__(self, obj):
        self.par = obj.par

    def op(self):
        self.par = 8


class Param():
    par = {}


param = Param()
param.par['val'] = 7
print(param.par)
oprator = Operator(param)
oprator1 = Operator1(param)
oprator.op()

print(param.par)
oprator1.op()
print(param.par)