import random
import math
from engine import Value   # 导入昨天的 value类
#神经元：加权求和+激活函数
class Neuron:
  def __init__(self,n_inputs):
    # 随机初始化权重，初始化偏置为0
    self.w = [Value(random.uniform(-1.0, 1.0)) for _ in range(n_inputs)]
    self.b = Value(0.0)
  
  def __call__(self, x):
    #前向传播：w1* x1 + w2* x2 + ... + b
    act = sum((wi * xi for wi,xi in zip(self.w,x)), self.b)
    return act.tanh()  #经过tanh 激活函数（引入非线性）
  
  def parameters(self):
      return self.w + [self.b]  # 返回该神经元的所有参数（用于后续训练）
  
#层，报含多个神经元
class Layer:
    def __init__(self, n_inputs, n_outputs):
        # 一层包含多个神经元
        self.neurons = [Neuron(n_inputs) for _ in range(n_outputs)]
        
    def __call__(self, x):
        outs = [n(x) for n in self.neurons]
        # 如果只有一个输出神经元，直接返回这个神经元的值，否则返回列表
        return outs[0] if len(outs) == 1 else outs
        
    def parameters(self):
        # 收集这一层里所有神经元的参数
        return [p for n in self.neurons for p in n.parameters()]

class MLP:
    def __init__(self, n_inputs, layer_sizes):
        # 比如输入3个，层结构[4, 4, 1]，sizes 就是 [3, 4, 4, 1]
        sizes = [n_inputs] + layer_sizes
        # MLP 包含多个层（Layer）
        self.layers = [Layer(sizes[i], sizes[i+1]) for i in range(len(layer_sizes))]
        
    def __call__(self, x):
        # 数据一层一层往后传
        for layer in self.layers:
            x = layer(x)
        return x
        
    def parameters(self):
        # 收集所有层的参数（这里之前写错成了 self.neurons）
        return [p for layer in self.layers for p in layer.parameters()]
xs = [
    [2.0, 3.0, -1.0],
    [3.0, -1.0, 0.5],
    [0.5, 1.0, 1.0],
    [1.0, 1.0, -1.0],
]
ys = [1.0, -1.0, -1.0, 1.0]  # 期望的输出（标签）

# 2. 创建模型：输入3个特征，网络结构是 4 -> 4 -> 1
model = MLP(3, [4, 4, 1])

# 3. 训练循环（梯度下降）
learning_rate = 0.05

for step in range(50):
    # ① 前向传播：让模型预测
    y_pred = [model(x) for x in xs]
    
    # ② 算损失（Loss）：预测值和真实值差多少（均方误差）
    loss = sum((yp - yt) * 2 for yp, yt in zip(y_pred, ys))
    
    # ③ 清空梯度（极其重要！因为 backward 是 +=，不清空会梯度累加）
    for p in model.parameters():
        p.grad = 0.0
        
    # ④ 反向传播：计算所有参数的梯度
    loss.backward()
    
    # ⑤ 更新参数：顺着梯度的反方向微调权重和偏置
    for p in model.parameters():
        p.data -= learning_rate * p.grad
        
    # 打印损失（观察 Loss 是否在下降）
    if step % 10 == 0:
        print(f"Step {step}: Loss = {loss.data:.4f}")

# 训练结束后测试一下
print("\n训练后的预测：")
for x, y in zip(xs, ys):
    pred = model(x)
    print(f"输入: {x}, 目标: {y}, 预测: {pred.data:.3f}")  
  
     