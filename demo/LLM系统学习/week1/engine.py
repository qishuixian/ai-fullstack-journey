import math
class Value:
    def __init__(self, data, _children=(), _op=''):
        self.data = data      # 存实际数值（比如 2.0）
        self.grad = 0.0        # 存梯度（初始为 0）
        self._backward = lambda: None # 反向传播的函数（初始为空）
        self._prev = set(_children)   # 记录计算图的父节点（我是谁算出来的）
        self._op = _op                # 记录操作类型（比如 '+' 或 '*'）
    def tanh(self):
        x = self.data
        # 前向计算：tanh 公式
        t = (math.exp(2*x) - 1) / (math.exp(2*x) + 1)
        out = Value(t, (self,), 'tanh')
        
        # 反向传播：tanh 的导数是 1 - tanh^2
        def _backward():
            self.grad += (1 - t**2) * out.grad
            
        out._backward = _backward
        return out
    # 重载 + 运算符。如果右边是普通数字，自动包装成 Value。
    def __add__(self, other):
        # 正向加法：把普通数字自动包装成 Value 对象
        if not isinstance(other, Value):
            other = Value(other)
        out = Value(self.data + other.data, (self, other), '+')
        #  加法求导规则。上游梯度 out.grad 直接流向两端。
        def _backward():
            self.grad += 1.0 * out.grad
            other.grad += 1.0 * out.grad
        out._backward = _backward
        return out
     # 反向加法（处理 5 + Value 的情况）。   
    def __radd__(self, other):
        # 反向加法：当普通数字在左边时触发（比如 5 + Value）
        return self.__add__(other)

    def __neg__(self):
        # 取负操作
        return self * -1
        
    def __sub__(self, other):
        # 正向减法
        return self + (-other)
        
    def __rsub__(self, other):
        # 反向减法：当普通数字在左边时触发（比如 5 - Value）
        return other + (-self)
        
    def __mul__(self, other):
        # 乘法（确保你也有这个）
        if not isinstance(other, Value):
            other = Value(other)
        out = Value(self.data * other.data, (self, other), '*')
        def _backward():
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad
        out._backward = _backward
        return out
        
    def __pow__(self, other):
        # 幂运算：解决 ** 2 的问题
        out = Value(self.data ** other, (self,), f'**{other}')
        def _backward():
            # 导数公式：d/dx(x^n) = n * x^(n-1)
            self.grad += (other * (self.data ** (other - 1))) * out.grad
        out._backward = _backward
        return out
    
    def backward(self):
        # 1. 构建计算图的拓扑排序（从后往前找依赖）
        topo = []
        visited = set()
        def build_topo(v):
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build_topo(child)
                topo.append(v)
        build_topo(self)
        
        # 2. 初始化基础梯度（输出节点对自己的导数是 1）
        self.grad = 1
        
        # 3. 反向遍历计算图，执行反向传播（链式法则）
        for v in reversed(topo):
            v._backward()

# 定义变量
a = Value(2.0)
b = Value(-3.0)
c = Value(10.0)

# 构建表达式：a*b + c
e = a * b + c

# 反向传播求导
e.backward()

# 打印结果
print(f"表达式结果 (2.0 * -3.0 + 10.0): {e.data}")  # 应该是 4.0
print(f"a 的梯度 (应该等于 b 的值 -3.0): {a.grad}")
print(f"b 的梯度 (应该等于 a 的值 2.0): {b.grad}")
print(f"c 的梯度 (应该等于 1.0): {c.grad}")
