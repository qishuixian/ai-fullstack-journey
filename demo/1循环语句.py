#1. for：迭代循环
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)

#2. while：条件循环
count = 5
while count > 0:
    print(count)
    count -= 1

#3. break：终止循环
for i in range(10):
    if i == 5:
        break  # 当 i 等于 5 时终止循环
    print(i)
#4. continue：跳过本次迭代
for i in range(5):
    if i == 2:
        continue  # 跳过 2
    print(i)
#5. else（循环）：循环正常结束执行
for i in range(3):
    print(i)
else:
    print("循环正常结束")

# 对比：被 break 终止
for i in range(3):
    if i == 1:
        break
else:
    print("这句不会被打印")

#6. pass：占位语句
for i in range(5):
    pass  # 暂时没想好写什么逻辑，先放 pass 防止语法报错

#7. range()：生成整数序列
for i in range(0, 5):
    print(i)  # 输出 0, 1, 2, 3, 4
#8. enumerate()：同时获取索引和值
fruits1 = ["apple", "banana", "cherry"]
for i, v in enumerate(fruits1):
    print(f"索引 {i}: {v}")